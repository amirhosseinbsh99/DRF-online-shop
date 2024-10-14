from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate,login
from django.contrib.auth.password_validation import validate_password
from home.models import Basket,Product,BasketItem
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated,BasePermission,AllowAny
from .serializers import CustomerSerializer,CustomerLoginSerializer,DashboardViewSerializer,BasketSerializer,BasketItemSerializer
from .models import Customer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
import requests,secrets,os
import json
from django.utils import timezone
from datetime import timedelta
from kavenegar import *
from rest_framework.authtoken.models import Token


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
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if a customer exists
            customer = Customer.objects.filter(phone_number=phone_number).first()

            # If customer exists, check if the OTP is expired or if the last request was within the allowed time frame
            if customer:
                if timezone.now() > customer.created_at + timedelta(minutes=2):
                    # If expired, delete the customer
                    customer.delete()
                    print(f"Deleted expired user with phone number: {phone_number}")
                else:
                    # Check the last OTP request time
                    if customer.last_otp_request and timezone.now() < customer.last_otp_request + timedelta(minutes=2):
                        remaining_time = (customer.last_otp_request + timedelta(minutes=1) - timezone.now()).total_seconds()
                        return Response({"error": f"لطفا {int(remaining_time)} ثانیه صبر کنید"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Disable OTP sending logic for testing
            test_mode = getattr(settings, 'OTP_TEST_MODE', False)
            if test_mode:
                otp = 12345  # Static OTP for testing
                print(f"Test mode enabled. Generated static OTP: {otp}")
            else:
                # Generate secure OTP
                otp = secrets.randbelow(90000) + 10000
                print(f"Generated OTP: {otp}")

                # Send OTP via Kavenegar (only in non-test mode)
                api_key = settings.KAVENEGAR_API_KEY
                if not api_key:
                    return Response({"error": "Kavenegar API key is missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                api = KavenegarAPI(api_key)
                params = {
                    'token': otp,
                    'receptor': phone_number,
                    'template': 'verify',
                    'type': 'sms'
                }

                response = api.verify_lookup(params)
                print(f"Kavenegar response: {response}")

            # Save or update OTP on the Customer model
            customer, created = Customer.objects.get_or_create(phone_number=phone_number)
            customer.token_send = otp
            customer.created_at = timezone.now()  # Update the created_at time to now
            customer.last_otp_request = timezone.now()  # Update the last OTP request time
            customer.save()

            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "Failed to send OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOTPAndCreateUserView(APIView):
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        password = request.data.get('password')

        if not phone_number or not otp or not password:
            return Response({"error": "Phone number, OTP, and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            # Retrieve the customer and validate OTP
            customer = Customer.objects.filter(phone_number=phone_number).first()

            if not customer:
                return Response({"error": "کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the OTP has expired (2 minutes)
            if timezone.now() > customer.created_at + timedelta(minutes=2):
                customer.delete()
                return Response({"error": "OTP has expired. User deleted."}, status=status.HTTP_400_BAD_REQUEST)

            if customer.token_send != int(otp):
                return Response({"error": "کد تایید اشتباه است"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate password (check length, strength, etc.)
            try:
                validate_password(password)  # Django's built-in password validation
            except ValidationError as e:
                return Response({"error": f"Password is invalid: {', '.join(e.messages)}"}, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"Customer is_active: {customer.is_active}")  # Check if condition is met
            # OTP is valid, now set the password using set_password()
            if not customer.is_active:
                customer.is_active = True  # Activate the user
                print(f"Received password: {password}")
                customer.set_password(password)  # Hash and save the password
                customer.save()  # Ensure to save the object


                # Generate the auth token if needed
                token, _ = Token.objects.get_or_create(user=customer)
            else:
                # If the user is already active, retrieve the existing token
                token = Token.objects.get(user=customer)

            return Response({
                "message": "User created successfully",
                "token": token.key
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({"error": "Failed to verify OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
            
            # Manually retrieve the user based on phone number
            try:
                user = Customer.objects.get(phone_number=phone_number)
            except Customer.DoesNotExist:
                return Response({'error': 'کاربری با این شماره موبایل یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

            # Check if the password is correct
            if user.check_password(password):
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({'token': token.key}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'حساب کاربری شما غیرفعال است'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'شماره موبایل یا پسورد اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and is an admin
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)
    
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

    def get(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        
        # Filter BasketItems with peyment=False
        basket_items = BasketItem.objects.filter(basket=basket, peyment=False)
        
        # Serialize basket and its items together
        serializer = BasketSerializer(basket, context={'peyment': False})
        return Response(serializer.data)
    
    def post(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        basket_item, created = BasketItem.objects.get_or_create(basket=basket, product=product)
        if not created:
            basket_item.quantity += quantity
            basket_item.save()

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        if not product_id or not quantity:
            return Response({'error': 'Product ID and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            basket_item = BasketItem.objects.get(basket=basket, product=product)
            basket_item.quantity = quantity
            basket_item.save()
        except BasketItem.DoesNotExist:
            return Response({'error': 'Basket item not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, basket_id):
        customer = request.user
        basket = get_object_or_404(Basket, id=basket_id, customer=customer)

        basket_items = BasketItem.objects.filter(basket=basket, peyment = False)
        
        if not basket_items.exists():
            return Response({'error': 'Basket is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        for item in basket_items:
            if item.product.stock < item.quantity:
                return Response({'error': f'Insufficient stock for product {item.product.name}'}, status=status.HTTP_400_BAD_REQUEST)
            
        total_amount = sum(item.product.price * item.quantity for item in basket_items)

        data = {
            "MerchantID": settings.ZARINPAL_MERCHANT_ID,
            "Amount": total_amount,  
            "CallbackURL": settings.ZARINPAL_CALLBACK_URL.format(basket_id=basket.id),
            "Description": "Payment for items in basket",
        }
        data = json.dumps(data)
        headers = {'content-type': 'application/json', 'content-length': str(len(data))}

        try:
            response = requests.post(settings.ZP_API_PAYMENT_REQUEST, data=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            if response_data['Status'] == 100:
                payment_url = settings.ZP_PAYMENT_GATEWAY_URL + response_data['Authority']
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

        # Calculate the total amount for all items in the basket
        basket_items = BasketItem.objects.filter(basket=basket)
        if not basket_items.exists():
            return Response({'status': False, 'code': 'Basket is empty'}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = sum(item.product.price * item.quantity for item in basket_items)

        data = {
            "MerchantID": settings.ZARINPAL_MERCHANT_ID,
            "Amount": total_amount,  # Rial / Required
            "Authority": authority,
        }
        data = json.dumps(data)
        headers = {'content-type': 'application/json', 'content-length': str(len(data))}

        try:
            response = requests.post(settings.ZP_API_VERIFY, data=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            if response_data['Status'] == 100:
                # Payment was successful
                ref_id = response_data['RefID']
                
                # Update stock quantity and clear the basket
                for item in basket_items:
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        item.peyment = True
                        product.save()
                        item.save()
                    else:
                        return Response({'status': False, 'code': 'Insufficient stock for one or more products'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Optionally clear the basket after successful purchase
                

                return Response({'status': True, 'RefID': ref_id}, status=status.HTTP_200_OK)
            else:
                return Response({'status': False, 'code': str(response_data['Status'])}, status=status.HTTP_400_BAD_REQUEST)
        except requests.exceptions.Timeout:
            return Response({'status': False, 'code': 'timeout'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({'status': False, 'code': 'connection error'}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.HTTPError as http_err:
            return Response({'status': False, 'code': f'HTTP error occurred: {http_err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            return Response({'status': False, 'code': f'An error occurred: {err}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, basket_id):
        basket = get_object_or_404(Basket, id=basket_id, customer=request.user)
        
        # Filter BasketItems with peyment=False
        basket_items = BasketItem.objects.filter(basket=basket, peyment=True)
        
        # Serialize basket and its items together
        serializer = BasketSerializer(basket, context={'peyment': True})
        return Response(serializer.data)