from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
#from rest_framework.authentication import TokenAuthentication
from .OTP import generate_and_send_otp,verify_otp  
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.password_validation import validate_password
from home.models import Basket,Product,BasketItem,Color
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated,BasePermission,AllowAny
from .serializers import CustomerSerializer,CustomerLoginSerializer,DashboardViewSerializer,BasketSerializer,BasketItemSerializer,CustomerSerializer
from .models import Customer
from django.shortcuts import get_object_or_404
from django.conf import settings
import requests,secrets,os
from rest_framework_simplejwt.tokens import RefreshToken
import json
from django.utils import timezone
from datetime import timedelta
from kavenegar import *
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError 

# class SendOTPView(APIView):
#     def post(self, request, *args, **kwargs):
#         phone_number = request.data.get('phone_number')
        
#         if not phone_number:
#             return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Check if a customer exists
#             customer = Customer.objects.filter(phone_number=phone_number).first()

#             # If customer exists, check if the OTP is expired or if the last request was within the allowed time frame
#             if customer:
#                 if timezone.now() > customer.created_at + timedelta(minutes=2):
#                     # If expired, delete the customer
#                     customer.delete()
#                     print(f"Deleted expired user with phone number: {phone_number}")
#                 else:
#                     # Check the last OTP request time
#                     if customer.last_otp_request and timezone.now() < customer.last_otp_request + timedelta(minutes=2):
#                         remaining_time = (customer.last_otp_request + timedelta(minutes=1) - timezone.now()).total_seconds()
#                         return Response({"error": f"لطفا {int(remaining_time)} ثانیه صبر کنید"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

#             # Generate secure OTP
#             otp = secrets.randbelow(90000) + 10000
#             print(f"Generated OTP: {otp}")

#             # Send OTP via Kavenegar
#             api_key = settings.KAVENEGAR_API_KEY
#             if not api_key:
#                 return Response({"error": "Kavenegar API key is missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#             api = KavenegarAPI(api_key)
#             params = {
#                 'token': otp,
#                 'receptor': phone_number,
#                 'template': 'verify',
#                 'type': 'sms'
#             }

#             response = api.verify_lookup(params)
#             print(f"Kavenegar response: {response}")

#             # Save or update OTP on the Customer model
#             customer, created = Customer.objects.get_or_create(phone_number=phone_number)
#             customer.token_send = otp
#             customer.created_at = timezone.now()  # Update the created_at time to now
#             customer.last_otp_request = timezone.now()  # Update the last OTP request time
#             customer.save()

#             return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

#         except Exception as e:
#             print(f"Unexpected error: {e}")
#             return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


    # permission_classes = [AllowAny]    
    
    # def post(self, request, *args, **kwargs):
    #     serializer = CustomerSerializer(data=request.data)
    #     phone_number = request.data.get('phone_number')
    #     password = request.data.get('password')

    #     if not phone_number:
    #         return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    #     if not password:
    #         return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    #     try:
    #         # Check if a customer exists
    #         customer = Customer.objects.filter(phone_number=phone_number).first()

            
                
            
    #         # If customer exists, check if the OTP is expired or if the last request was within the allowed time frame
    #         if customer:
    #             if customer.is_active:
    #                 return Response({"error": "این شماره قبلا در سیستم ثبت شده است"}, status=status.HTTP_400_BAD_REQUEST)
                
    #             if timezone.now() > customer.created_at + timedelta(minutes=2):
    #                 # If expired, delete the customer
    #                 customer.delete()
    #                 print(f"Deleted expired user with phone number: {phone_number}")
    #             else:
    #                 # Check the last OTP request time
    #                 if customer.last_otp_request and timezone.now() < customer.last_otp_request + timedelta(minutes=2):
    #                     remaining_time = (customer.last_otp_request + timedelta(minutes=1) - timezone.now()).total_seconds()
    #                     return Response({"error": f"لطفا {int(remaining_time)} ثانیه صبر کنید"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    #         else:
    #             customer = Customer(phone_number=phone_number)    
    #         try:
    #             validate_password(password)  # Django's built-in password validation
    #             customer.set_password(password)  # Hash and save the password
    #             customer.save()  # Ensure to save the object
    #         except ValidationError as e:
    #             return Response({"error": f"Password is invalid: {', '.join(e.messages)}"}, status=status.HTTP_400_BAD_REQUEST)
            
    #         # Disable OTP sending logic for testing
    #         test_mode = getattr(settings, 'OTP_TEST_MODE', False)
    #         if test_mode:
    #             otp = 12345  # Static OTP for testing
    #             print(f"Test mode enabled. Generated static OTP: {otp}")
    #         else:
    #             # Generate secure OTP
    #             otp = secrets.randbelow(90000) + 10000
    #             print(f"Generated OTP: {otp}")

    #             # Send OTP via Kavenegar (only in non-test mode)
    #             api_key = settings.KAVENEGAR_API_KEY
    #             if not api_key:
    #                 return Response({"error": "Kavenegar API key is missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
    #             api = KavenegarAPI(api_key)
    #             params = {
    #                 'token': otp,
    #                 'receptor': phone_number,
    #                 'template': 'verify',
    #                 'type': 'sms'
    #             }

    #             response = api.verify_lookup(params)
    #             print(f"Kavenegar response: {response}")

    #         # Save or update OTP on the Customer model
    #         customer, created = Customer.objects.get_or_create(phone_number=phone_number)
    #         customer.token_send = otp
    #         customer.created_at = timezone.now()  # Update the created_at time to now
    #         customer.last_otp_request = timezone.now()  # Update the last OTP request time
    #         customer.save()

    #         return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         print(f"Unexpected error: {e}")
    #         return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class VerifyOTPAndCreateUserView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = CustomerSerializer(data=request.data)
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        
        if not phone_number or not otp:
             return Response({"error": "Phone number and otp are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            
            # Retrieve the customer and validate OTP
            customer = Customer.objects.filter(phone_number=phone_number).first()

            if not customer:
                return Response({"error": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the OTP has expired (2 minutes)
            if not customer.is_active:
                if timezone.now() > customer.created_at + timedelta(seconds=30):
                    customer.delete()
                    return Response({"error": "OTP has expired. User deleted."}, status=status.HTTP_400_BAD_REQUEST)
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
            return Response({"error": "Failed to verify OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if customer exists
            customer = Customer.objects.filter(phone_number=phone_number).first()
            if not customer:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

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

            return Response({"message": "OTP sent for password reset"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')

        if not phone_number or not otp_code or not new_password:
            return Response(
                {"error": "Phone number, OTP code, and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if customer exists
            customer = Customer.objects.filter(phone_number=phone_number).first()
            if not customer:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Verify OTP
            is_valid = verify_otp(customer, otp_code, purpose="password_reset")
            
            
            if not is_valid:
                
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

            # Reset the password if OTP is valid
            try:
                validate_password(new_password)  # Django's built-in password validation
                customer.set_password(new_password)  # Hash and save the password
                customer.save()  # Ensure to save the object
                return Response({"message": "password is chaneged"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": f"Password is invalid: {', '.join(e.messages)}"}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "Failed to verify OTP and reset password"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class LogoutView(APIView):
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
        serializer = BasketSerializer(baskets, many=True, context={'peyment': False})
        return Response(serializer.data)

    def post(self, request):
        basket, created = Basket.objects.get_or_create(customer=request.user)
        return Response(BasketSerializer(basket).data, status=status.HTTP_201_CREATED)

class BasketItemCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        basket_items = BasketItem.objects.filter(basket=basket, peyment=False)
        serializer = BasketSerializer(basket, context={'peyment': False})
        return Response(serializer.data)

    def post(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        color_id = request.data.get('color')  # Make sure this is 'color_id' in your request data
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Retrieve color if provided
        color = None
        if color_id:
            try:
                color = Color.objects.get(id=color_id)
            except Color.DoesNotExist:
                return Response({'error': 'Color not found'}, status=status.HTTP_404_NOT_FOUND)

        # Include color in the get_or_create lookup to allow different colors of the same product
        basket_item, created = BasketItem.objects.get_or_create(
            basket=basket,
            product=product,
            color=color,  # Now color is included in the uniqueness criteria
            defaults={'quantity': quantity}
        )
        
        if not created:
            basket_item.quantity += quantity
            basket_item.save()

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
    def put(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        color_id = request.data.get('color')

        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve color if color_id is provided
        color = None
        if color_id:
            try:
                color = Color.objects.get(id=color_id)
            except Color.DoesNotExist:
                return Response({'error': 'Color not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            basket_item = BasketItem.objects.get(basket=basket, product=product)
            if quantity is not None:
                basket_item.quantity = quantity
            if color:  # Update color if provided
                basket_item.color = color
            basket_item.save()
        except BasketItem.DoesNotExist:
            return Response({'error': 'Basket item not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentRequestView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, basket_id):
        customer = request.user
        basket = get_object_or_404(Basket, id=basket_id, customer=customer)
        basket_items = BasketItem.objects.filter(basket=basket, peyment=False)
        
        if not basket_items.exists():
            return Response({'error': 'Basket is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        for item in basket_items:
            if item.product.stock < item.quantity:
                return Response({'error': f'Insufficient stock for product {item.product.name}'}, status=status.HTTP_400_BAD_REQUEST)
            
        total_amount = sum(item.product.price * item.quantity for item in basket_items)

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
    permission_classes = [IsAuthenticated]

    def get(self, request, basket_id):
        authority = request.GET.get('Authority', '')
        customer = request.user
        basket = get_object_or_404(Basket, id=basket_id, customer=customer)

        # Calculate total amount for all items in the basket
        basket_items = BasketItem.objects.filter(basket=basket)
        if not basket_items.exists():
            return Response({'status': False, 'code': 'Basket is empty'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = sum(item.product.price * item.quantity for item in basket_items)

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
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        item.peyment = True
                        product.save()
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
        
        # Filter BasketItems with peyment=False
        basket_items = BasketItem.objects.filter(basket=basket, peyment=True)
        
        # Serialize basket and its items together
        serializer = BasketSerializer(basket, context={'peyment': True})
        return Response(serializer.data)