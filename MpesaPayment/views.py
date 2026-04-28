# transactions/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django_daraja.mpesa.core import MpesaClient
from .models import MpesaTransaction
import json
from datetime import datetime
import time
from django.conf import settings
from decimal import Decimal

# transactions/views.py
class InitiateSTKPush(View):
    def post(self, request):
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        
        # Convert amount to integer (M-Pesa requires whole number)
        try:
            amount = float(amount) if amount else 0
            amount = int(amount)  # Convert to integer (remove decimal)
        except (ValueError, TypeError):
            amount = 0
            
        reference = request.POST.get('reference')
        description = request.POST.get('description', 'Payment')

        # Validate inputs
        if not all([phone_number, amount, reference]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Format phone number (2547...)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]

        # Initialize M-Pesa client
        cl = MpesaClient()

        try:
            # Use ngrok URL for callback in development
            if settings.DEBUG:
                callback_url = 'https://a50c-154-159-252-109.ngrok-free.app/mpesa/callback/'
            else:
                callback_url = request.build_absolute_uri('/mpesa/callback/')
            print(f"Using callback URL: {callback_url}")

            # Initiate STK push
            response = cl.stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=reference,
                transaction_desc=description,
                callback_url=callback_url
            )

            # Debug: Print the actual response
            print("Raw M-Pesa Response:", response)
            print("Response Type:", type(response))

            # Convert response to serializable format
            response_dict = self._parse_mpesa_response(response)
            print("Parsed Response:", response_dict)

            # Check if request was successful
            if response_dict.get('success'):
                # Create transaction record with only essential data
                transaction = MpesaTransaction.objects.create(
                    phone_number=phone_number,
                    amount=Decimal(str(amount)),
                    reference=reference,
                    description=description,
                    checkout_request_id=response_dict.get('checkout_request_id', ''),
                    merchant_request_id=response_dict.get('merchant_request_id', ''),
                    # Store only the essential response data, not the entire complex object
                    raw_response={
                        'response_code': response_dict.get('response_code'),
                        'response_description': response_dict.get('response_description'),
                        'customer_message': response_dict.get('customer_message'),
                        'merchant_request_id': response_dict.get('merchant_request_id'),
                        'checkout_request_id': response_dict.get('checkout_request_id'),
                    }
                )

                return JsonResponse({
                    'success': True,
                    'message': 'STK push sent successfully! Check your phone to complete payment.',
                    'transaction_id': transaction.id,
                    'checkout_request_id': response_dict.get('checkout_request_id'),
                    'response_description': response_dict.get('response_description', 'Request sent successfully')
                })
            else:
                # STK push failed
                return JsonResponse({
                    'success': False,
                    'error': response_dict.get('error_message', 'Failed to send STK push'),
                    'response_code': response_dict.get('response_code'),
                }, status=400)

        except Exception as e:
            print("Exception:", str(e))
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'success': False,
                'error': f'Failed to initiate payment: {str(e)}'
            }, status=500)

    def _parse_mpesa_response(self, response):
        """
        Convert M-Pesa response object to serializable dictionary
        """
        try:
            # If it's already a dict, return it
            if isinstance(response, dict):
                return response

            # If it has __dict__ attribute, use that but filter non-serializable objects
            if hasattr(response, '__dict__'):
                response_dict = {}

                # Only extract the fields we actually need
                essential_fields = [
                    'response_code', 'response_description', 'customer_message',
                    'merchant_request_id', 'checkout_request_id', 'error_message',
                    'error_code', 'conversation_id', 'originator_conversation_id'
                ]

                for field in essential_fields:
                    if hasattr(response, field):
                        value = getattr(response, field)
                        # Convert to string if it's not a basic type
                        if value is not None and not isinstance(value, (str, int, float, bool, type(None))):
                            response_dict[field] = str(value)
                        else:
                            response_dict[field] = value

                # Determine success
                response_dict['success'] = getattr(response, 'response_code', None) == "0"

                return response_dict

            # If it's a string or bytes, convert to string
            elif isinstance(response, (str, bytes)):
                return {
                    'success': False,
                    'raw_response': response.decode('utf-8') if isinstance(response, bytes) else response,
                    'error_message': 'Unexpected response format'
                }

            else:
                # Last resort - convert to string
                return {
                    'success': False,
                    'raw_response': str(response),
                    'error_message': 'Could not parse response'
                }

        except Exception as e:
            print(f"Error parsing response: {e}")
            return {
                'success': False,
                'error_message': f'Error parsing response: {str(e)}',
                'raw_response': str(response)
            }


@csrf_exempt
def stk_push_callback(request):
    """
    Handle M-Pesa STK Push callback
    """
    if request.method == 'POST':
        try:
            # Log the raw callback data for debugging
            raw_body = request.body
            print("Raw callback body type:", type(raw_body))

            # Decode bytes to string if necessary
            if isinstance(raw_body, bytes):
                raw_body_str = raw_body.decode('utf-8')
            else:
                raw_body_str = raw_body

            print("Raw callback data:", raw_body_str)

            data = json.loads(raw_body_str)

            # Extract the STK callback
            stk_callback = data.get('Body', {}).get('stkCallback', {})

            if not stk_callback:
                print("No stkCallback found in data")
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid callback format'})

            # Extract basic info
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            merchant_request_id = stk_callback.get('MerchantRequestID')

            print(f"Callback received - ResultCode: {result_code}, CheckoutRequestID: {checkout_request_id}")

            # Find transaction
            try:
                transaction = MpesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )

                if result_code == 0:
                    # Transaction successful
                    transaction.status = 'successful'

                    # Extract details from callback metadata
                    callback_metadata = stk_callback.get('CallbackMetadata', {})
                    items = callback_metadata.get('Item', [])

                    for item in items:
                        item_name = item.get('Name')
                        item_value = item.get('Value')

                        if item_name == 'MpesaReceiptNumber':
                            transaction.mpesa_receipt_number = item_value
                            print(f"Receipt Number: {item_value}")
                        elif item_name == 'Amount':
                            print(f"Amount: {item_value}")
                        elif item_name == 'TransactionDate':
                            try:
                                transaction_date_str = str(item_value)
                                transaction.transaction_date = datetime.strptime(
                                    transaction_date_str, '%Y%m%d%H%M%S'
                                )
                            except ValueError as e:
                                print(f"Failed to parse date: {item_value}, Error: {e}")
                        elif item_name == 'PhoneNumber':
                            print(f"Phone: {item_value}")

                else:
                    # Transaction failed
                    transaction.status = 'failed'
                    print(f"Transaction failed: {result_desc}")

                # Store the complete callback data
                transaction.raw_response = data
                transaction.save()

                print(f"Transaction {transaction.id} updated to status: {transaction.status}")

                # Return success response to M-Pesa
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})

            except MpesaTransaction.DoesNotExist:
                print(f"Transaction not found for CheckoutRequestID: {checkout_request_id}")
                # Still return success to M-Pesa to avoid repeated callbacks
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Transaction not found but acknowledged'})

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Callback processing error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)}, status=500)

    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request method'}, status=405)


def payment_page(request):
    return render(request, 'Transactions/payment.html')


class TransactionStatusView(View):
    def get(self, request, transaction_id):
        try:
            transaction = MpesaTransaction.objects.get(id=transaction_id)

            response_data = {
                'id': transaction.id,
                'phone_number': transaction.phone_number,
                'amount': str(transaction.amount),
                'reference': transaction.reference,
                'status': transaction.status,
                'mpesa_receipt_number': transaction.mpesa_receipt_number,
                'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                'created_at': transaction.created_at.isoformat(),
                'checkout_request_id': transaction.checkout_request_id
            }

            return JsonResponse(response_data)

        except MpesaTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)


# Manual simulation for development
@csrf_exempt
def simulate_success(request, transaction_id):
    """
    Manually simulate successful payment for testing
    """
    if request.method == 'POST':
        try:
            transaction = MpesaTransaction.objects.get(id=transaction_id)

            # Update transaction as successful
            transaction.status = 'successful'
            transaction.mpesa_receipt_number = f"SIM{int(time.time())}"
            transaction.transaction_date = datetime.now()

            # Create mock callback data
            mock_callback = {
                'Body': {
                    'stkCallback': {
                        'ResultCode': 0,
                        'ResultDesc': 'The service request is processed successfully.',
                        'CallbackMetadata': {
                            'Item': [
                                {'Name': 'Amount', 'Value': float(transaction.amount)},
                                {'Name': 'MpesaReceiptNumber', 'Value': transaction.mpesa_receipt_number},
                                {'Name': 'TransactionDate', 'Value': transaction.transaction_date.strftime('%Y%m%d%H%M%S')},
                                {'Name': 'PhoneNumber', 'Value': transaction.phone_number}
                            ]
                        }
                    }
                }
            }

            transaction.raw_response = mock_callback
            transaction.save()

            return JsonResponse({
                'success': True,
                'message': 'Payment simulated successfully!',
                'transaction': {
                    'id': transaction.id,
                    'status': transaction.status,
                    'receipt': transaction.mpesa_receipt_number
                }
            })

        except MpesaTransaction.DoesNotExist:
            return JsonResponse({'error': 'Transaction not found'}, status=404)

    return JsonResponse({'error': 'Invalid method'}, status=405)