from django import forms
from .models import StripeCustomer

class UserForm(forms.ModelForm):
    class Meta:
        model = StripeCustomer
        exclude = ('user','regist_date','stripeSubscriptionId','stripeCustomerId')
