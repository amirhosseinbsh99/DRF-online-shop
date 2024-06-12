from django.contrib import admin
from .models import Category, Product
from accounts.models import Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone_number')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','title')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'available', 'created_at', 'updated_at')
    list_filter = ('available', 'category')
    search_fields = ('name',)


admin.site.register(Customer,CustomerAdmin)


