from django.shortcuts import render
import os
import json
import traceback
from decouple import config
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import openai
from django.conf import settings
import logging
from django.http import JsonResponse
from pathlib import Path

logger = logging.getLogger(__name__)

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

def load_prompt_template():
    """Load the prompt template from file with error handling"""
    try:
        prompt_path = BASE_DIR / 'ChatBot' / 'prompts' / 'god.txt'
        logger.info(f"Looking for prompt at: {prompt_path}")
        
        if prompt_path.exists():
            encodings = ['utf-8-sig', 'utf-8', 'latin-1']
            for encoding in encodings:
                try:
                    with open(prompt_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        logger.info(f"Prompt loaded successfully using {encoding} encoding, length: {len(content)}")
                        return content
                except UnicodeDecodeError:
                    continue
            
            with open(prompt_path, 'rb') as f:
                content = f.read()
                content = content.decode('utf-8', errors='ignore')
                logger.warning("Prompt loaded with error handling")
                return content
        else:
            logger.warning(f"Prompt file not found at {prompt_path}")
            return get_default_prompt()
            
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return get_default_prompt()


def get_default_prompt():
    """Return default prompt when file can't be loaded"""
    return """You are a customer support assistant for Day Safaris Adventures, a premier East African safari tour operator.

STRICT RULES:
1. ONLY answer questions about Day Safaris Adventures safaris, destinations, packages, bookings, and East African travel
2. For off-topic questions, politely redirect to safari topics
3. Be friendly, professional, and helpful

COMPANY INFO:
- Name: Day Safaris Adventures
- Contact: +254 734 962 965, info@daysafarisadventures.co.ke
- Destinations: Masai Mara, Serengeti, Amboseli, Zanzibar, Mount Kilimanjaro

Now assist the customer with their question."""


def get_ai_response(user_message, system_prompt):
    """Get AI analysis using GitHub's Azure AI endpoint"""
    
    # Get GitHub token from environment
    api_key = config('github', default=None)
    base_url = 'https://models.inference.ai.azure.com'
    
    if not api_key:
        logger.error("GitHub API key not configured")
        return generate_mock_response(user_message)
    
    # Initialize client with GitHub's Azure endpoint
    try:
        client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=30.0
        )
        
        # Use the correct model for GitHub's Azure AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4o", "gpt-35-turbo" depending on what's available
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.95
        )
        
        ai_response = response.choices[0].message.content
        logger.info(f"AI Response received successfully")
        return ai_response
        
    except openai.AuthenticationError as auth_error:
        logger.error(f"Authentication Failed: {auth_error}")
        logger.error("Please check your GitHub token is valid and has access to Azure AI models")
        return generate_mock_response(user_message)
        
    except openai.APIError as api_error:
        logger.error(f"API Error: {api_error}")
        # Check if it's a model access issue
        if "model" in str(api_error).lower():
            logger.error("Model not accessible. Trying alternative model...")
            try:
                # Try with a different model
                response = client.chat.completions.create(
                    model="gpt-35-turbo",  # Alternative model name
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.95
                )
                ai_response = response.choices[0].message.content
                logger.info(f"AI Response received using alternative model")
                return ai_response
            except Exception as e:
                logger.error(f"Alternative model also failed: {e}")
                return generate_mock_response(user_message)
        return generate_mock_response(user_message)
        
    except openi.APIConnectionError as conn_error:
        logger.error(f"Connection Error: {conn_error}")
        return generate_mock_response(user_message)
        
    except openai.RateLimitError as rate_error:
        logger.error(f"Rate Limit Error: {rate_error}")
        return generate_mock_response(user_message)
        
    except Exception as e:
        logger.error(f"Unexpected AI Error: {e}")
        logger.error(traceback.format_exc())
        return generate_mock_response(user_message)


def generate_mock_response(user_message):
    """Generate a mock response when AI is unavailable"""
    user_message_lower = user_message.lower()
    
    # Simple keyword matching for common questions
    if any(word in user_message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! Welcome to Day Safaris Adventures! 🦁 How can I help you plan your East African safari today? I can assist with destinations, packages, bookings, or any questions about our services!"
    
    elif any(word in user_message_lower for word in ['book', 'booking', 'safari']):
        return "Great! I can help you book a safari. 🦁 Please visit our booking form or provide me with your preferred destination, travel dates, and number of people. You can also email us at bookings@daysafarisadventures.co.ke for immediate assistance."
    
    elif any(word in user_message_lower for word in ['destination', 'place', 'where', 'location']):
        return "We offer amazing destinations including: Masai Mara (Kenya), Serengeti (Tanzania), Zanzibar Beach, Mount Kilimanjaro, Amboseli National Park, Lake Nakuru, Tsavo National Park, and many more! Which destination interests you? 🗺️"
    
    elif any(word in user_message_lower for word in ['package', 'price', 'cost', 'rate']):
        return "Our safari packages start from $649 for 3-day adventures to $1,899 for luxury experiences. Popular packages include:\n• Masai Mara Safari (4 days, $849)\n• Zanzibar Beach Holiday (6 days, $1,299)\n• Serengeti Migration (5 days, $1,499)\n• Amboseli Elephant Experience (3 days, $649)\n\nWould you like details on any specific package? 💰"
    
    elif any(word in user_message_lower for word in ['payment', 'pay', 'credit card', 'mpesa']):
        return "We accept various payment methods including credit cards (Visa, Mastercard, American Express), bank transfers, and mobile money (M-Pesa in Kenya). We also offer flexible payment plans with 30% deposit required to confirm booking. 💳"
    
    elif any(word in user_message_lower for word in ['discount', 'offer', 'deal', 'promotion']):
        return "We currently have several special offers! 🎁\n• First-Time Customers: 50% off first adventure trip\n• Early Bird: 10% off bookings 3+ months in advance\n• Group Discount: 15% off for 6+ persons\n• Family Package: Children under 12 get 30% off\n\nWould you like to know more about any of these offers?"
    
    elif any(word in user_message_lower for word in ['group', 'family']):
        return "We offer special group and family packages! Groups of 6+ get 15% discount, and children under 12 get 30% off. We can customize itineraries for families with activities suitable for all ages. Would you like a custom quote for your group? 👨‍👩‍👧‍👦"
    
    elif any(word in user_message_lower for word in ['contact', 'phone', 'email', 'reach']):
        return "You can reach us at:\n📞 Phone: +254 734 962 965 (Main)\n📞 Emergency: +254 782 390 295\n📧 Email: info@daysafarisadventures.co.ke\n📍 Location: Nairobi, Kenya\n🌐 Website: daysafarisadventures.co.ke\n\nWe're available 24/7 for your inquiries!"
    
    elif any(word in user_message_lower for word in ['thank', 'thanks']):
        return "You're very welcome! 🎉 Is there anything else I can help you with? Feel free to ask about our safari packages, destinations, or special offers! We look forward to hosting you in East Africa! 🌍"
    
    else:
        return "Thank you for your message! 📧 I'd be happy to help you with:\n\n• Safari bookings and packages\n• Destination information\n• Pricing and availability\n• Payment options\n• Group and family discounts\n• Travel tips and requirements\n\nCould you please provide more details about what you're looking for? Or feel free to contact us directly at info@daysafarisadventures.co.ke or call +254 734 962 965 for immediate assistance. 🦁"


@csrf_exempt
@require_http_methods(["POST"])
def response_api(request):
    """API endpoint for chatbot"""
    try:
        # Parse JSON request
        try:
            body = json.loads(request.body)
            user_message = body.get('message', '').strip()
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'No message provided'
            }, status=400)
        
        logger.info(f"Processing message: {user_message[:50]}...")
        
        # Load prompt and get response
        system_prompt = load_prompt_template()
        ai_response = get_ai_response(user_message, system_prompt)
        
        return JsonResponse({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        logger.error(f"Error in response_api: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


def test_chatbot(request):
    """Test view to check if chatbot is working"""
    # Test the GitHub API connection
    api_key = config('github', default=None)
    api_status = "configured" if api_key else "not configured"
    
    # Mask the API key for security
    masked_key = api_key[:10] + "..." + api_key[-4:] if api_key and len(api_key) > 14 else "None"
    
    return JsonResponse({
        'status': 'ok',
        'message': 'Chatbot API is reachable',
        'api_status': api_status,
        'api_key_preview': masked_key if api_key else "None",
        'paths': {
            'base_dir': str(BASE_DIR),
            'prompt_file_exists': (BASE_DIR / 'ChatBot' / 'prompts' / 'god.txt').exists(),
            'env_file_exists': (BASE_DIR / '.env').exists()
        }
    })


def test_github_api(request):
    """Test view to check GitHub API connectivity"""
    api_key = config('github', default=None)
    
    if not api_key:
        return JsonResponse({
            'success': False,
            'error': 'GitHub API key not configured'
        }, status=400)
    
    try:
        client = openai.OpenAI(
            base_url='https://models.inference.ai.azure.com',
            api_key=api_key,
            timeout=10.0
        )
        
        # Simple test request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API is working'"}
            ],
            max_tokens=20
        )
        
        return JsonResponse({
            'success': True,
            'message': 'GitHub API is working',
            'response': response.choices[0].message.content
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)