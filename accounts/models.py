from django.db import models

from django.contrib.auth.models import AbstractUser


class Customer(AbstractUser):

	
	PhoneNumber = models.CharField(max_length = 250 , null = True , blank = True)
	PostCode = models.IntegerField(null = True , blank = True)
	
	first_name = None
	last_name = None
	




	


	








