from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
from home.models import Product,Category,Basket, BasketItem,ProductImage

class ProductSerializer(serializers.ModelSerializer):

    def validate_slug(self, value):
        if not re.match(r'^[\w-]+$', value, re.UNICODE):
            raise serializers.ValidationError('Enter a valid “slug” consisting of letters, numbers, underscores, or hyphens.')
        return value
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'brand', 'description', 'model_number',
            'image', 'available', 'price', 'stock', 'color', 'star_rating',
            'size', 'material', 'created_at', 'updated_at','slug'
        ]

    def validate_star_rating(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError("Star rating must be between 0 and 5.")
        return value
    
    def validate_colors(self, value):
        # Ensure colors is a list of strings
        if not isinstance(value, list):
            raise serializers.ValidationError("Colors must be a list.")
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Each color must be a string.")
        return value

class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = "__all__"

class BasketItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = BasketItem
        fields = ('product', 'quantity')

class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True)

    class Meta:
        model = Basket
        fields = ('items',)

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']