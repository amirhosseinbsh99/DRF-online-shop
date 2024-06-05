from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import Customer
import unidecode

class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200, blank=True, allow_unicode=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}, {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            # Use unidecode to convert Persian characters to ASCII for the slug
            self.slug = slugify(unidecode.unidecode(self.title), allow_unicode=True)
        super().save(*args, **kwargs)
            

class Product(models.Model):
    category = models.ForeignKey("Category", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, null=True, blank=True)
    description  = models.TextField()
    model_number = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='blog/', null=True, blank=True)
    available = models.BooleanField(default=True)
    price = models.IntegerField()
    stock = models.PositiveIntegerField()
    color = models.JSONField(null=True, blank=True)  # e.g., ["Red", "Green", "Blue"]
    star_rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    size = models.CharField(max_length=10)
    material = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.available} - {self.price}"
    
class Basket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through='BasketItem')

class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
