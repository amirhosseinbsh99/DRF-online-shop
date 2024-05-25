from django.contrib import admin
from .models import Category, Product
from accounts.models import Customer



class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username','PhoneNumber')
    



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('Title','Slug')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('Name', 'Category', 'Price', 'Stock', 'Available', 'Created_at', 'Updated_at')
    list_filter = ('Available', 'Category')
    search_fields = ('Name',)



admin.site.register(Customer,CustomerAdmin)


