from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Customer


User = get_user_model()

class PhoneNumberBackend(ModelBackend):
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        try:
            user = Customer.objects.get(phone_number=phone_number)
            if user.check_password(password):
                return user
        except Customer.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Customer.objects.get(pk=user_id)
        except Customer.DoesNotExist:
            return None