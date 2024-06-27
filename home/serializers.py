from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
from home.models import Product,Category,Basket, BasketItem,ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()

    def validate_slug(self, value):
        if not re.match(r'^[\w-]+$', value, re.UNICODE):
            raise serializers.ValidationError('Enter a valid “slug” consisting of letters, numbers, underscores, or hyphens.')
        return value

    def validate_star_rating(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError("Star rating must be between 0 and 5.")
        return value

    def validate_color(self, value):
        if not isinstance(value, str):
            raise serializers.ValidationError("Color must be a string.")
        return value

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'brand', 'description', 'model_number',
            'available', 'price', 'stock', 'color', 'star_rating',
            'size', 'material', 'created_at', 'updated_at', 'slug', 'images',
            'average_rating'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        images_data = request.FILES.getlist('images')
        product = Product.objects.create(**validated_data)
        for image_data in images_data:
            ProductImage.objects.create(product=product, image=image_data)
        return product 
    
class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = "__all__"



