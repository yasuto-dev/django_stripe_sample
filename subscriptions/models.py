from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

class BaseManager(models.Manager):
   def get_or_none(self, **kwargs):
       """
       検索にヒットすればそのモデルを、しなければNoneを返します。
       """
       try:
           return self.get_queryset().get(**kwargs)
       except self.model.DoesNotExist:
           return None

class StripeCustomer(models.Model):
    objects = BaseManager()
    user = models.OneToOneField( to=User, on_delete=models.CASCADE)
    stripeCustomerId = models.CharField(max_length=255)
    stripeSubscriptionId = models.CharField(max_length=255)
    ac_name = models.CharField('アカウント名', max_length=100, null=True, blank=True)
    regist_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username
