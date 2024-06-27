from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from .models import Customer
from home.models import Product,BasketItem,Basket


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_phone_number(self, value):
        if len(value) != 11:
            raise serializers.ValidationError("شماره موبایل باید 11 رقمی باشد")
        return value

    def create(self, validated_data):
        customer = Customer(
            phone_number=validated_data['phone_number'],
        )
        customer.set_password(validated_data['password'])
        customer.save()
        return customer
    
class CustomerLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()

class DashboardViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        exclude = ['is_admin','is_superuser','id','groups','user_permissions','is_staff','is_active']

class BasketItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = BasketItem
        fields = ['id', 'product', 'quantity', 'peyment']

class BasketItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = BasketItem
        fields = ['id', 'product', 'quantity', 'peyment']

class BasketSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = ['id', 'customer', 'items']

    def get_items(self, obj):
        peyment_status = self.context.get('peyment', None)
        items = obj.items.all()
        if peyment_status is not None:
            items = items.filter(peyment=peyment_status)
        return BasketItemSerializer(items, many=True).data