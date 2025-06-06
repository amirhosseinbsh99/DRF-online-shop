from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from home.serializers import ProductVariantSerializer
from .models import Customer
from home.models import Product,BasketItem,Basket,Color,ProductVariant,ProductImage


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_phone_number(self, value):
        if len(value) != 11:
            raise serializers.ValidationError("شماره موبایل باید 11 رقمی باشد")
        if Customer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("کاربری با این شماره موبایل قبلاً ثبت نام کرده است")
        return value
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("رمز عبور باید حداقل 8 کاراکتر باشد")
        return value
    def create(self, validated_data):
        customer = Customer(
            phone_number=validated_data['phone_number'],
        )
        customer.set_password(validated_data['password'])
        customer.save()
        return customer


class CustomerLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        # Optionally, add phone number validation logic here (e.g., check if it's a valid number format)
        if not value.isdigit():
            raise serializers.ValidationError("شماره موبایل فقط باید عدد باشد")
        return value

    def validate_password(self, value):
        # Add any additional password validation here if needed (e.g., complexity rules)
        if len(value) < 8:
            raise serializers.ValidationError("پسورد باید 8 رقمی باشد")
        return value
    
    class Meta:
        model = Customer
        exclude = ['is_superuser','id','groups','user_permissions','is_staff','is_active']

class DashboardViewSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        exclude = ['is_superuser','id','groups','user_permissions','is_staff','is_active']


class BasketItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    product_variant = ProductVariantSerializer() 
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all(), required=False)
    price = serializers.FloatField(source='product_variant.price', read_only=True)  # Access price via product_variant
    total_price = serializers.SerializerMethodField()  # Calculated field
    total_discounted_price = serializers.SerializerMethodField()  # Total discounted price
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = BasketItem
        fields = ['id','product','thumbnail','quantity', 'payment','color','product_variant','price','total_price','total_discounted_price']
        
    def get_total_price(self, obj):
        return obj.quantity * obj.product_variant.price
    
    def get_thumbnail(self, obj):
    # Try to fetch the thumbnail directly from the Product model
        if obj.product_variant.product.thumbnail:
            return obj.product_variant.product.thumbnail.url  # Return thumbnail URL if present
        
        # Fallback: Fetch the first related image for the product if thumbnail is not set
        product_image = ProductImage.objects.filter(product=obj.product_variant.product).first()
        if product_image and product_image.image:
            return product_image.image.url  # Return the URL of the image
        
        # Return None if no thumbnail or image is found
        return None
    
    def get_product_name(self, obj):
        return obj.product_variant.product.name  # Assuming the product is related to the variant
    
    def get_product_slug(self, obj):
        return obj.product_variant.product.slug  # Assuming the product is related to the variant
    
    def get_total_discounted_price(self, obj):
        """
        Calculate the total discounted price for this item.
        """
        return obj.product_variant.get_discounted_price()

    def get_product(self, obj):
        """Retrieve product details from the related product variant."""
        product = obj.product_variant.product
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
        }


class BasketSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = ['id', 'customer', 'items']


    def get_items(self, obj):
        payment_status = self.context.get('payment', None)
        items = obj.items.all()
        if payment_status is not None:
            items = items.filter(payment=payment_status)
        return BasketItemSerializer(items, many=True).data
    
    def get_total_discounted_price(self, obj):
        """
        Sum up the total discounted prices for all items in the basket.
        Each item's total discounted price is already calculated.
        """
        return sum(item.get_total_discounted_price() for item in obj.items.all())
    
class OrderHistorySerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.get_full_name')
    phone_number = serializers.ReadOnlyField(source='customer.phone_number')
    items = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = ['id', 'customer_name', 'phone_number', 'items']

    def get_items(self, obj):
        # Filter BasketItems where payment=True for this Basket
        items = obj.items.filter(payment=True)
        return BasketItemSerializer(items, many=True).data