from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Customer
from home.models import Product,BasketItem,Basket,Color,ProductVariant


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
    
class DashboardViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        exclude = ['is_admin','is_superuser','id','groups','user_permissions','is_staff','is_active']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'color', 'size', 'price', 'stock']

class BasketItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer()  # Include product_variant data in the response

    class Meta:
        model = BasketItem
        fields = ['id', 'basket', 'product_variant', 'quantity', 'payment']

# class BasketItemSerializer(serializers.ModelSerializer):
#     product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

#     class Meta:
#         model = BasketItem
#         fields = ['id', 'product', 'quantity', 'payment']

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