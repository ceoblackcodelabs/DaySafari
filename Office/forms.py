from django import forms
from .models import Employee
from django.core.exceptions import ValidationError
import re

class EmployeeForm(forms.ModelForm):
    confirm_email = forms.EmailField(
        label='Confirm Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Confirm email address'})
    )
    
    class Meta:
        model = Employee
        fields = ['name', 'email', 'contact', 'role', 'department', 'salary', 'hire_date', 'address', 'emergency_name', 'emergency_contact']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254 700 000 000'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Physical address'}),
            'emergency_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact name'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254 700 000 000'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set empty label for select fields
        self.fields['role'].empty_label = 'Select Role'
        self.fields['department'].empty_label = 'Select Department'
    
    # def clean_email(self):
    #     email = self.cleaned_data.get('email')
    #     if Employee.objects.filter(email=email).exists():
    #         raise ValidationError('An employee with this email already exists.')
    #     return email
    
    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        # Remove any non-digit characters
        clean_contact = re.sub(r'\D', '', contact)
        if len(clean_contact) < 10:
            raise ValidationError('Enter a valid phone number with at least 10 digits.')
        return contact
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        
        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', 'Email addresses do not match.')
        
        return cleaned_data