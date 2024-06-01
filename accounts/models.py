from django.db import models

from django.contrib.auth.models import AbstractUser


class Customer(AbstractUser):
    phone_number = models.CharField(max_length=11, unique=True)
    post_Code = models.IntegerField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Set the username to be the same as the phone_number
        self.username = self.phone_number
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone_number if self.phone_number else ""
