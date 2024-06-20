from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate,login
from home.models import Basket,Product,BasketItem
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated,BasePermission,AllowAny
from .serializers import CustomerSerializer,CustomerLoginSerializer,DashboardViewSerializer,BasketSerializer,BasketItemSerializer
from .models import Customer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
import requests
import json
from django.urls import reverse
class SignUpView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create basket for the newly created user
            Basket.objects.create(customer=user)
            return Response({"message": "ثبت نام با موفقیت انجام شد"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

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
            user = authenticate(request, phone_number=phone_number, password=password)
            if user is not None:
                login(request, user)
                return Response({"message": "با موفقیت وارد شدید"}, status=status.HTTP_200_OK)
            return Response({"error": "شماره موبایل یا پسورد اشتباه است"}, status=status.HTTP_401_UNAUTHORIZED)
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
        serializer = BasketSerializer(baskets, many=True)
        return Response(serializer.data)

    def post(self, request):
        basket, created = Basket.objects.get_or_create(customer=request.user)
        return Response(BasketSerializer(basket).data, status=status.HTTP_201_CREATED)
    

class BasketItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,basket_id):
        baskets = Basket.objects.filter(customer=request.user)
        serializer = BasketSerializer(baskets, many=True)
        return Response(serializer.data)
    
    def post(self, request, basket_id):
        basket = Basket.objects.get(id=basket_id, customer=request.user)
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
    def put(self, request):
        basket, created = Basket.objects.get_or_create(customer=request.user)
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
    





@permission_classes([IsAuthenticated])
def send_request(request, basket_id):
    customer = request.user

    # Fetch the specific basket for the given basket ID
    try:
        basket = Basket.objects.get(id=basket_id, customer=customer)
    except Basket.DoesNotExist:
        return JsonResponse({'status': False, 'code': 'Basket not found'})

    # Calculate the total amount for all items in the basket
    basket_items = BasketItem.objects.filter(basket=basket)
    if not basket_items.exists():
        return JsonResponse({'status': False, 'code': 'Basket is empty'})

    total_amount = sum(item.product.price * item.quantity for item in basket_items)

    description = f"Purchase of {basket_items.count()} items"
    mobile = customer.phone_number

    callback_url = request.build_absolute_uri(reverse('account:verify', kwargs={'basket_id': basket_id}))

    data = {
        "MerchantID": settings.ZARINPAL_MERCHANT_ID,
        "Amount": total_amount,  # Rial / Required
        "Description": description,
        "Phone": mobile,
        "CallbackURL": callback_url,
    }
    data = json.dumps(data)
    headers = {'content-type': 'application/json', 'content-length': str(len(data))}

    try:
        response = requests.post(settings.ZP_API_REQUEST, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        response_data = response.json()

        if response_data['Status'] == 100:
            return HttpResponseRedirect(settings.ZP_API_STARTPAY + str(response_data['Authority']))
        else:
            return JsonResponse({'status': False, 'code': str(response_data['Status'])})
    except requests.exceptions.Timeout:
        return JsonResponse({'status': False, 'code': 'timeout'})
    except requests.exceptions.ConnectionError:
        return JsonResponse({'status': False, 'code': 'connection error'})
    except requests.exceptions.HTTPError as http_err:
        return JsonResponse({'status': False, 'code': f'HTTP error occurred: {http_err}'})
    except Exception as err:
        return JsonResponse({'status': False, 'code': f'An error occurred: {err}'})

def verify(request, basket_id):
    authority = request.GET.get('Authority', '')
    
    # Fetch the specific basket for the given basket ID
    customer = request.user
    try:
        basket = Basket.objects.get(id=basket_id, customer=customer)
    except Basket.DoesNotExist:
        return JsonResponse({'status': False, 'code': 'Basket not found'})

    # Calculate the total amount for all items in the basket
    basket_items = BasketItem.objects.filter(basket=basket)
    if not basket_items.exists():
        return JsonResponse({'status': False, 'code': 'Basket is empty'})

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
                    product.save()
                else:
                    return JsonResponse({'status': False, 'code': 'Insufficient stock for one or more products'})
            
            # Optionally clear the basket after successful purchase
            basket_items.delete()

            return JsonResponse({'status': True, 'RefID': ref_id})
        else:
            return JsonResponse({'status': False, 'code': str(response_data['Status'])})
    except requests.exceptions.Timeout:
        return JsonResponse({'status': False, 'code': 'timeout'})
    except requests.exceptions.ConnectionError:
        return JsonResponse({'status': False, 'code': 'connection error'})
    except requests.exceptions.HTTPError as http_err:
        return JsonResponse({'status': False, 'code': f'HTTP error occurred: {http_err}'})
    except Exception as err:
        return JsonResponse({'status': False, 'code': f'An error occurred: {err}'})



