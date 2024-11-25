from django.contrib import admin
from .models import Category, Product,Basket, BasketItem,Color,Size
from accounts.models import Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username','phone_number', 'is_active', 'is_admin', 'created_at')

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['id','name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')
    search_fields = ('title',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'category', 'price', 'stock', 'available', 'created_at', 'updated_at')
    list_filter = ('available', 'category')
    search_fields = ('name',)

    
class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0  # Do not display extra empty forms

class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer',)
    search_fields = ('customer__username', 'customer__email')
    inlines = [BasketItemInline]

class BasketItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'basket', 'product', 'quantity')
    search_fields = ('basket__customer__username', 'product__name')

admin.site.register(Basket, BasketAdmin)
admin.site.register(BasketItem, BasketItemAdmin)

admin.site.register(Customer,CustomerAdmin)

class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')  # Display fields in the admin list view
    search_fields = ('name',)  # Allow searching by name

admin.site.register(Size, SizeAdmin)


