from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
from home.models import Product,Category,Basket, BasketItem,ProductImage,Color

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

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    colors = ColorSerializer(many=True, read_only=True)  # For displaying colors with name
    color_ids = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all(), many=True, write_only=True)  # For inputting color IDs
    # average_rating = serializers.ReadOnlyField()

    def validate_slug(self, value):
        if not re.match(r'^[\w-]+$', value, re.UNICODE):
            raise serializers.ValidationError('Enter a valid “slug” consisting of letters, numbers, underscores, or hyphens.')
        return value

    # def validate_star_rating(self, value):
    #     if value < 0 or value > 5:
    #         raise serializers.ValidationError("Star rating must be between 0 and 5.")
    #     return value

    def create(self, validated_data):
        colors_data = validated_data.pop('color_ids', [])
        product = Product.objects.create(**validated_data)
        product.colors.set(colors_data)  # Associate colors with the product

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
            'available', 'price', 'stock', 'colors','color_ids',
            'size', 'material', 'created_at', 'updated_at', 'slug', 'images',
            
        ]

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



