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