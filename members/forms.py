
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
from django import forms

from captcha.fields import CaptchaField

def validate_over_18(dob):
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 18:
        raise ValidationError("You must be at least 18 years old to register.")

class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    date_of_birth = forms.DateField(
    widget=forms.DateInput(
        attrs={
            'type': 'date',
            'class': 'form-control',
            'max': '2008-01-01',
        }
    ),
    validators=[validate_over_18]

    )

    class Meta:
        model = User
        fields = ['username', 'email', 'date_of_birth', 'password', 'password_confirm']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password_confirm")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")

        return cleaned_data


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
    captcha = CaptchaField()


