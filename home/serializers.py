from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
from home.models import Product,Category,Basket, BasketItem,ProductImage,Color,Size,ProductVariant
from accounts.models import Customer


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id','name', 'hex_code']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name', 'description']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']



class UpdateProductSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField() 

    def get_color_names(self, obj):
        return [color.name for color in obj.colors.all()]

    def get_size_names(self, obj):
        # Ensure 'size' is properly accessed as a related field
        try:
            return [size.name for size in obj.size.all()]  # For ManyToManyField
        except AttributeError:
            return []

    def get_discounted_price(self, obj):
        # Compute discounted price based on discount_percentage
        if obj.discount_percentage > 0:
            return obj.price * (1 - obj.discount_percentage / 100)
        return obj.price

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'brand', 'description', 'model_number',
            'available', 'price', 'stock','material', 'created_at', 'updated_at', 'slug', 
            'thumbnail','discount_percentage', 'discounted_price'
        ]


# class ProductVariantAdminSerializer(serializers.ModelSerializer):
#     color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all()) 
#     size = serializers.PrimaryKeyRelatedField(queryset=Size.objects.all())  
    
#     discounted_price = serializers.SerializerMethodField()

#     class Meta:
#         model = ProductVariant
#         fields = ['id', 'product', 'color', 'size', 'stock', 'price','discount_percentage', 'discounted_price']

#     def get_discounted_price(self, obj):
#         return obj.get_discounted_price()

#     def get_color(self, obj):
#         """Retrieve color details (name and hex code)."""
#         color = obj.color
#         return {
#             "name": color.name,
#             "hex_code": color.hex_code
#         }

#     def get_size(self, obj):
#         """Retrieve size details (name)."""
#         return {
#             "name": obj.size.name
#         }

class ProductVariantSerializer(serializers.ModelSerializer):
    
    color = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'color', 'size', 'stock', 'price','discount_percentage', 'discounted_price']

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()

    def get_color(self, obj):
        """Retrieve color details (name and hex code)."""
        color = obj.color
        return {
            "name": color.name,
            "hex_code": color.hex_code
        }

    def get_size(self, obj):
        """Retrieve size details (name)."""
        return {
            "name": obj.size.name
        }

class ProductSerializer(serializers.ModelSerializer):
    colors = ColorSerializer(many=True, read_only=True)
    sizes = SizeSerializer(many=True, read_only=True)  # This should reference sizes via the related name
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    thumbnail = serializers.ImageField(required=False)
    discounted_price = serializers.SerializerMethodField()

    def create(self, validated_data):
        colors_data = validated_data.pop('color_ids', [])
        sizes_data = validated_data.pop('size_ids', [])
        thumbnail = validated_data.pop('thumbnail', None)

        # Create the product instance
        product = Product.objects.create(**validated_data)

        # Set many-to-many relationships for colors and sizes via the ProductVariant
        for size in sizes_data:
            # Create ProductVariant for each size and color combination (if necessary)
            ProductVariant.objects.create(product=product, size_id=size, color_id=colors_data[0])  # Example for creating variants

        # Handle the thumbnail if provided
        if thumbnail:
            product.thumbnail = thumbnail
            product.save()

        # Handle the gallery images (make sure request.FILES is passed correctly)
        request = self.context.get('request')
        if request and request.FILES:
            images_data = request.FILES.getlist('images')
            for image_data in images_data:
                # Create ProductImage instances for each uploaded image
                ProductImage.objects.create(product=product, image=image_data)

        return product

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'brand', 'description', 'model_number',
            'available', 'price', 'discount_percentage', 'discounted_price', 'stock',
            'material', 'created_at', 'updated_at', 'slug', 'thumbnail', 'images', 'variants', 'sizes', 'colors',
        ]

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()

    # STAR RATING IF NEEDED :D
    # def validate_star_rating(self, value):
    #     if value < 0 or value > 5:
    #         raise serializers.ValidationError("Star rating must be between 0 and 5.")
    #     return value

    

class ProductCheckboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['checkbox']  # Only include 'checkbox' field to update
    
    
class CategorySerializer(serializers.ModelSerializer):
    parent_title = serializers.CharField(source='parent.title', read_only=True)  # Show parent title
    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Category
        fields = ['id','parent','title', 'parent_id', 'parent_title']  # Include both parent id and title

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'address', 'is_active', 'created_at']



