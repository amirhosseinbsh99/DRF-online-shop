from django.contrib import admin
from .models import Category, Product,Basket, BasketItem,Color,Size,ProductVariant,ProductImage
from accounts.models import Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id','username','phone_number', 'is_active', 'is_admin', 'created_at')

class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'product_count')

    def product_count(self, obj):
        # Count distinct products related to this color through ProductVariant
        return ProductVariant.objects.filter(color=obj).values('product').distinct().count()

    product_count.short_description = 'Number of Products'
    
admin.site.register(Color, ColorAdmin)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')
    search_fields = ('title',)


# 
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('id','name', 'category', 'price', 'stock', 'available', 'created_at', 'updated_at')
#     list_filter = ('available', 'category')
#     search_fields = ('name',)

    
class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0  # Do not display extra empty forms

class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer',)
    search_fields = ('customer__username', 'customer__email','product_variant__product__name')
    inlines = [BasketItemInline]

class BasketItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'basket', 'get_product_name', 'get_color', 'get_size', 'quantity', 'payment')  # Ensure 'payment' exists on the model
    search_fields = ('basket__customer__username', 'product_variant__product__name')

    def get_product_name(self, obj):
        return obj.product_variant.product.name
    get_product_name.short_description = 'Product'

    def get_color(self, obj):
        return obj.product_variant.color.name
    get_color.short_description = 'Color'

    def get_size(self, obj):
        return obj.product_variant.size.name
    get_size.short_description = 'Size'

# @admin.register(Product)
class ProductVariantInline(admin.TabularInline):  # Use TabularInline for a table-like display
    model = ProductVariant
    extra = 0  # Do not show empty extra rows
    fields = ('color', 'size', 'stock', 'price','discount_percentage', 'get_discounted_price')  # Fields to display in the inline
    readonly_fields = ('get_discounted_price',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available', 'stock','discount_percentage', 'get_discounted_price')
    readonly_fields = ('get_discounted_price',)
    inlines = [ProductVariantInline]  # Add the inline for ProductVariant


class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_product_name', 'get_color', 'get_size', 'stock', 'price')
    search_fields = ('product__name', 'color__name', 'size__name')  # Search by product name, color name, and size name

    # Display product name for the product variant
    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = 'Product Name'  # Column header name

    # Display color name for the product variant
    def get_color(self, obj):
        return obj.color.name
    get_color.short_description = 'Color'

    # Display size name for the product variant
    def get_size(self, obj):
        return obj.size.name
    get_size.short_description = 'Size'

@admin.register(ProductImage)
class ProductImage(admin.ModelAdmin):
    list_display = ('product', 'image')
    search_fields = ('product',)

# Register the ProductVariantAdmin
admin.site.register(ProductVariant, ProductVariantAdmin)

# Register models
admin.site.register(Product, ProductAdmin)

admin.site.register(Basket, BasketAdmin)
admin.site.register(BasketItem, BasketItemAdmin)
# admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(Customer,CustomerAdmin)

class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')  # Display fields in the admin list view
    search_fields = ('name',)  # Allow searching by name

admin.site.register(Size, SizeAdmin)


