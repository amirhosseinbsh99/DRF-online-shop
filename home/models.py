from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}, {self.title}'
    

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
    color = models.CharField(max_length=30)
    star_rating = models.IntegerField()
    size = models.CharField(max_length=10)
    material = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.available} - {self.price}"
    

