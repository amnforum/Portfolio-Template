from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your Name',
            'class': 'contact-input',
            'id': 'contact-name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
            'class': 'contact-input',
            'id': 'contact-email',
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Subject',
            'class': 'contact-input',
            'id': 'contact-subject',
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Tell me about your project...',
            'rows': 6,
            'class': 'contact-input',
            'id': 'contact-message',
        })
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
