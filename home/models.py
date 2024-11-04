from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import Customer


class Category(models.Model):
    title = models.CharField(max_length=200)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}, {self.title}'   

class Color(models.Model):  
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey("Category", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    model_number = models.CharField(max_length=100, null=True, blank=True)
    available = models.BooleanField(default=True)
    price = models.IntegerField()
    stock = models.PositiveIntegerField()
    colors = models.ManyToManyField(Color, blank=True)  
    size = models.CharField(max_length=10, null=True, blank=True)
    material = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, max_length=200, blank=True, allow_unicode=True)
    # total_rating = models.IntegerField(default=0)
    # number_of_ratings = models.IntegerField(default=0)
    # star_rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])

    # @property
    # def average_rating(self):
    #     if self.number_of_ratings == 0:
    #         return 0.0
    #     return self.total_rating / self.number_of_ratings

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name.replace(" ", "-"), allow_unicode=True)
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='blog/')
    
    def __str__(self):
        return f"Image for {self.product.name}"

class Basket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='baskets')
    

    def __str__(self):
        return f"Basket {self.id} for {self.customer.username}"

class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    peyment = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in basket {self.basket.id}"
