from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated, 
    BasePermission, 
    AllowAny
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
import secrets
import os
import json

from kavenegar import *

from .OTP import generate_and_send_otp, verify_otp
from .models import Customer
from .serializers import (
    CustomerSerializer, 
    CustomerLoginSerializer, 
    OrderHistorySerializer, 
    DashboardViewSerializer, 
    BasketSerializer, 
    BasketItemSerializer
)
from home.models import (
    Basket, 
    Product, 
    BasketItem, 
    Color, 
    ProductVariant
)


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        if not phone_number:
            return Response({"error": "شماره تلفن الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({"error": "رمز عبور الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if a customer exists
            customer = Customer.objects.filter(phone_number=phone_number).first()

            if customer:
                # Handle existing customer who is inactive or waiting for OTP verification
                if customer.is_active:
                    return Response({"error": "این شماره قبلا در سیستم ثبت شده است"}, status=status.HTTP_400_BAD_REQUEST)
                
                # If the customer’s OTP request has expired
                if timezone.now() > customer.created_at + timedelta(seconds=30):
                    customer.delete()
                    print(f"Deleted expired user with phone number: {phone_number}")
                    customer = None  # Reset customer to None for recreation below
                else:
                    # Check for recent OTP request to enforce rate limiting
                    if customer.last_otp_request and timezone.now() < customer.last_otp_request + timedelta(minutes=2):
                        remaining_time = (customer.last_otp_request + timedelta(minutes=2) - timezone.now()).total_seconds()
                        return Response({"error": f"لطفا {int(remaining_time)} ثانیه صبر کنید"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Create a new customer instance if none exists or was deleted
            if not customer:
                customer = Customer(phone_number=phone_number)
            
            try:
                validate_password(password)
                customer.set_password(password)
                # Send OTP only if the request is not rate-limited
                generate_and_send_otp(customer, purpose="signup")
                customer.last_otp_request = timezone.now()  # Update OTP request time
                customer.save()
                return Response({"message": "کد تایید برای ثبت‌نام ارسال شد"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": f"رمز عبور نامعتبر است: {', '.join(e.messages)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "ارسال کد تایید با شکست مواجه شد"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class VerifyOTPAndCreateUserView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = CustomerSerializer(data=request.data)
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        
        if not phone_number or not otp:
             return Response({"error": " شماره و کد تایید مورد نیاز است"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            
            # Retrieve the customer and validate OTP
            customer = Customer.objects.filter(phone_number=phone_number).first()

            if not customer:
                return Response({"error": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the OTP has expired (2 minutes)
            if not customer.is_active:
                if timezone.now() > customer.created_at + timedelta(seconds=30):
                    customer.delete()
                    return Response({"error": "زمان کد تایید به پایان رسید"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "اکانت شما قبلا فعال شده است"}, status=status.HTTP_400_BAD_REQUEST)

            if customer.token_send != int(otp):
                return Response({"error": "کد تایید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate password (check length, strength, etc.)
            
            
            print(f"Customer is_active: {customer.is_active}")  # Check if condition is met
            # OTP is valid, now set the password using set_password()
            if not customer.is_active:
                customer.is_active = True  # Activate the user
                
                customer.save()  # Ensure to save the object
                # Generate the auth token if needed
                token, _ = Token.objects.get_or_create(user=customer)
                Basket.objects.create(customer=customer)
                baskets = Basket.objects.get(customer=customer)

            else:
                # If the user is already active, retrieve the existing token
                token = Token.objects.get(user=customer)
                
            return Response({
                "message": "User created successfully",
                "token": token.key,
                "phone_number":phone_number,
                "BasketID":baskets.id,

            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "کد تایید نشد"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({"error": "شماره مورد نیاز است"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if customer exists
            customer = Customer.objects.filter(phone_number=phone_number).first()
            if not customer:
                return Response({"error": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

            # Rate limiting: ensure OTP isn't sent too frequently
            if customer.last_otp_request and timezone.now() < customer.last_otp_request + timedelta(seconds=30):
                remaining_time = (customer.last_otp_request + timedelta(seconds=30) - timezone.now()).total_seconds()
                return Response(
                    {"error": f"Please wait {int(remaining_time)} seconds before requesting another OTP"},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Generate and send OTP
            generate_and_send_otp(customer, purpose="password_reset")
            
            # Update the OTP request timestamp
            customer.last_otp_request = timezone.now()
            customer.save()

            return Response({"message": "کد تایید ارسال شد"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "کد تایید نشد"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')

        if not phone_number or not otp_code or not new_password:
            return Response(
                {"error": "شماره و کد تایید و پسورد جدید مورد نیاز است"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if customer exists
            customer = Customer.objects.filter(phone_number=phone_number).first()
            if not customer:
                return Response({"error": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

            # Verify OTP
            is_valid = verify_otp(customer, otp_code, purpose="password_reset")
            
            
            if not is_valid:
                
                return Response({"error": "زمان کد تایید به پایان رسید یا کد اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)

            # Reset the password if OTP is valid
            try:
                validate_password(new_password)  # Django's built-in password validation
                customer.set_password(new_password)  # Hash and save the password
                customer.save()  # Ensure to save the object
                return Response({"message": "پسورد تغییر یافت"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": f"پسورد اشتباه است {', '.join(e.messages)}"}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "کد تایید و پسورد تایید نشد"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = CustomerLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            password = serializer.validated_data['password']
            
            try:
                user = Customer.objects.get(phone_number=phone_number)
                
                if user.check_password(password):
                    if user.is_active:
                        # Generate JWT tokens
                        refresh = RefreshToken.for_user(user)
                        
                        # Return JWT tokens and user data
                        return Response({
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                            'phone_number': user.phone_number,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'post_Code': user.post_Code,
                            'address': user.address,
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({'error': 'حساب کاربری شما غیرفعال است'}, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({'error': 'شماره موبایل یا پسورد اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)
                    
            except Customer.DoesNotExist:
                return Response({'error': 'کاربری با این شماره موبایل یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, id=None):
        # If no id is provided, return the logged-in user's details
        if id is None:
            customer = request.user
        else:
            # If an id is provided, fetch the customer with that id
            customer = get_object_or_404(Customer, id=id)


        customer.password=''
        # Serialize the customer data
        serializer = DashboardViewSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id=None):
        if id is None:
            customer = request.user
        else:
            customer = get_object_or_404(Customer, id=id)

        data = request.data.copy()
        password = data.pop('password', None)

        for field, value in data.items():
            if value in [None, '']:  # If the value is empty or null, keep the current value
                data[field] = getattr(customer, field)
        # Update other fields
        serializer = DashboardViewSerializer(customer, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Update password if provided
            if password:
                customer.set_password(password)
                customer.save()

            # Return the updated customer data without password
            customer.password = ''
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BasketListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        baskets = Basket.objects.filter(customer=request.user)
        basket_data = []

        for basket in baskets:
            # Get basket items for the current basket
            basket_items = BasketItem.objects.filter(basket=basket, payment=False)
            basket_item_serializer = BasketItemSerializer(basket_items, many=True)

            # Calculate the total discounted price for all basket items
            total_discounted_price = sum(
                item['quantity'] * item['total_discounted_price']  # Sum all the items' discounted prices
                for item in basket_item_serializer.data
            )

            # Append the basket data with the total discounted price
            basket_data.append({
                'basket': BasketSerializer(basket).data,
                'total_discounted_price': int(total_discounted_price)  # Ensure it's an integer
            })

        return Response(basket_data)

    def post(self, request):
        basket, created = Basket.objects.get_or_create(customer=request.user)
        return Response(BasketSerializer(basket).data, status=status.HTTP_201_CREATED)


class BasketItemCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    def get(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        basket_items = BasketItem.objects.filter(basket=basket, payment=False)
        serializer = BasketItemSerializer(basket_items, many=True)
        return Response(serializer.data)


    def post(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        product_variant_id = request.data.get('product_variant_id')  # Use product_variant_id in request
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product_variant = ProductVariant.objects.get(id=product_variant_id)
        except ProductVariant.DoesNotExist:
            return Response({'error': ' محصول یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
         # Check if the product variant has already been paid for in this basket
        if BasketItem.objects.filter(basket=basket, product_variant=product_variant, payment=True).exists():
            return Response({'error': 'این ویژگی محصول قبلاً پرداخت شده است و نمی توان آن را دوباره اضافه کرد'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Create or update the basket item
        basket_item, created = BasketItem.objects.get_or_create(
            basket=basket,
            product_variant=product_variant,  # Use the product_variant
            defaults={'quantity': quantity}
        )
        
        if not created:
            basket_item.quantity += quantity
            basket_item.save()

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        product_variant_id = request.data.get('product_variant_id')  # Use product_variant_id
        quantity = request.data.get('quantity')

        if not product_variant_id:
            return Response({'error': 'آی دی ویژگی محصول مورد نیاز است'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_variant = ProductVariant.objects.get(id=product_variant_id)
        except ProductVariant.DoesNotExist:
            return Response({'error': 'ویژگی محصول یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        try:
            basket_item = BasketItem.objects.get(basket=basket, product_variant=product_variant)
            if quantity is not None:
                basket_item.quantity = quantity
            basket_item.save()
        except BasketItem.DoesNotExist:
            return Response({'error': 'سبد یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PaymentRequestView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, basket_id):
        customer = request.user
        basket = get_object_or_404(Basket, id=basket_id, customer=customer)
        basket_items = BasketItem.objects.filter(basket=basket, payment=False)
        basket_item_serializer = BasketItemSerializer(basket_items, many=True)

        
        if not basket_items.exists():
            return Response({'error': 'سبد شما خالی است'}, status=status.HTTP_400_BAD_REQUEST)
        
        for item in basket_items:
            if item.product_variant.stock < item.quantity:
                return Response({'error': f'محصول نا موجود است {item.product_variant.name}'}, status=status.HTTP_400_BAD_REQUEST)
            


        total_amount = sum(
            item['quantity'] * item['total_discounted_price']  # Sum all the items' discounted prices
            for item in basket_item_serializer.data
        )

        data = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": total_amount,
            "callback_url": settings.ZARINPAL_CALLBACK_URL.format(basket_id=basket.id),
            "description": "Payment for items in basket",
        }
        data = json.dumps(data)
        headers = {'content-type': 'application/json'}

        try:
            response = requests.post(settings.ZP_API_PAYMENT_REQUEST, data=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get('data', {}).get('code') == 100:
                authority = response_data['data']['authority']
                payment_url = settings.ZP_PAYMENT_GATEWAY_URL + authority
                return Response({'payment_url': payment_url})
            else:
                return Response({'error': 'Failed to generate payment link'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.exceptions.Timeout:
            return Response({'error': 'Request timeout'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({'error': 'Connection error'}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.HTTPError as http_err:
            return Response({'error': f'HTTP error occurred: {http_err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            return Response({'error': f'An error occurred: {err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentVerifyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, basket_id):
        authority = request.GET.get('Authority', '')
        # Get the basket by ID only
        basket = get_object_or_404(Basket, id=basket_id)

        # Calculate total amount for all items in the basket
        basket_items = BasketItem.objects.filter(basket=basket)
        if not basket_items.exists():
            return Response({'status': False, 'code': 'سبد خرید خالی است'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = sum(item.product_variant.price * item.quantity for item in basket_items)

        data = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": total_amount,  
            "authority": authority,
        }
        data = json.dumps(data)
        headers = {'content-type': 'application/json'}

        try:
            response = requests.post(settings.ZP_API_VERIFY, data=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get('data', {}).get('code') == 100:
                # Payment successful
                ref_id = response_data['data']['ref_id']
                
                # Update stock quantity and mark items as paid
                for item in basket_items:
                    product_variant = item.product_variant
                    if product_variant.stock >= item.quantity:
                        product_variant.stock -= item.quantity
                        item.payment = True
                        product_variant.save()
                        item.save()
                    else:
                        return Response({'status': False, 'code': 'Insufficient stock'}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({'status': True, 'RefID': ref_id}, status=status.HTTP_200_OK)
            else:
                error_code = response_data.get('errors', {}).get('code', 'Unknown error')
                return Response({'status': False, 'code': str(error_code)}, status=status.HTTP_400_BAD_REQUEST)
        except requests.exceptions.Timeout:
            return Response({'status': False, 'code': 'timeout'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({'status': False, 'code': 'connection error'}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.HTTPError as http_err:
            return Response({'status': False, 'code': f'HTTP error: {http_err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            return Response({'status': False, 'code': f'Error: {err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        
        # Filter BasketItems with payment=False
        basket_items = BasketItem.objects.filter(basket=basket, payment=True)
        
        # Serialize basket and its items together
        serializer = BasketSerializer(basket, context={'payment': True})
        return Response(serializer.data)
    
class OrderHistoryAdminView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        # Get all Baskets where at least one item has payment=True
        baskets = Basket.objects.filter(items__payment=True).distinct()

        serializer = OrderHistorySerializer(baskets, many=True)
        return Response(serializer.data)