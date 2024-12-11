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
    images = ProductImageSerializer(many=True, read_only=True)
    colors = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all(), many=True, required=False)
    size = serializers.PrimaryKeyRelatedField(queryset=Size.objects.all(), many=True, required=False)
    color_names = serializers.SerializerMethodField()
    size_names = serializers.SerializerMethodField()

    def get_color_names(self, obj):
        return [color.name for color in obj.colors.all()]

    def get_size_names(self, obj):
        return [size.name for size in obj.size.all()]

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'brand', 'description', 'model_number',
            'available', 'price', 'stock', 'colors', 'color_names', 'size',
            'size_names', 'material', 'created_at', 'updated_at', 'slug', 'thumbnail', 'images',
        ]


class ProductVariantSerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()  # Get color details
    size = serializers.SerializerMethodField()  # Get size details

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'color', 'size', 'stock', 'price']

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
    sizes = SizeSerializer(many=True, source='size', read_only=True)  # Use the related name `size`  # Use the related name `size`
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    thumbnail = serializers.ImageField(required=False)  # Separate thumbnail field

    def create(self, validated_data):
        # Extract related data

        colors_data = validated_data.pop('color_ids', [])
        sizes_data = validated_data.pop('size_ids', [])  
        thumbnail = validated_data.pop('thumbnail', None)

        # Create the product
        product = Product.objects.create(**validated_data)

        # Set many-to-many relationships
        product.colors.set(colors_data)  # Set colors
        product.size.set(sizes_data)  # Set sizes

        # Handle the thumbnail
        if thumbnail:
            product.thumbnail = thumbnail
            product.save()

        # Handle the gallery images
        request = self.context.get('request')
        if request and request.FILES:
            images_data = request.FILES.getlist('images')
            for image_data in images_data:
                ProductImage.objects.create(product=product, image=image_data)

        return product
    
    class Meta:
            model = Product
            fields = [
                'id', 'category', 'name', 'brand', 'description', 'model_number',
                'available', 'price', 'stock', 'material', 'created_at', 
                'updated_at', 'slug', 'thumbnail', 'images', 'variants','sizes','colors',
            ]

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
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)  # Show parent id
    parent_title = serializers.CharField(source='parent.title', read_only=True)  # Show parent title

    class Meta:
        model = Category
        fields = ['id','title', 'parent_id', 'parent_title']  # Include both parent id and title

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'address', 'is_active', 'created_at']



