from django.contrib import admin
from subscriptions.models import StripeCustomer
from .forms import UserForm


admin.site.register(StripeCustomer)

