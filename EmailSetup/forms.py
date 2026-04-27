from django import forms

class ContactReplyForm(forms.Form):
    reply_subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re: ',
            'id': 'reply_subject'
        })
    )
    reply_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Type your response here...',
            'id': 'reply_message'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reply_subject'].label = 'Subject'
        self.fields['reply_message'].label = 'Message'