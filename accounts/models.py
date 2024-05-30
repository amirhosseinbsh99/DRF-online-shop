from django.db import models

from django.contrib.auth.models import AbstractUser


class Customer(AbstractUser):

	
	phone_number = models.CharField(max_length = 250 , null = True , blank = True)
	post_Code = models.IntegerField(null = True , blank = True)
	
	first_name = None
	last_name = None
	




	


	








