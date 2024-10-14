from django.db import models
from django.contrib.auth.models import AbstractUser

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from rest_framework.authtoken.models import Token

class Customer(AbstractUser):
    phone_number = models.CharField(max_length=11, unique=True)
    first_name = models.CharField(max_length=50)
    last_name =models.CharField(max_length=50 )
    post_Code = models.IntegerField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    token_send = models.IntegerField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)  
    last_otp_request = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)   
    address = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Set the username to be the same as the phone_number
        self.username = self.phone_number
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone_number if self.phone_number else ""

# Create token when a new user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)