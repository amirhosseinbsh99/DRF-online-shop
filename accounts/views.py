from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.permissions import BasePermission
from .serializers import CustomerSerializer
from .models import Customer

# Create your views here.
class SignUpView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "ثبت نام با موفقیت انجام شد"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# class LoginView(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = CustomerLoginSerializer(data=request.data)
#         if serializer.is_valid():
#             phone_number = serializer.data['phone_number']
#             password = serializer.data['password']
#             user = authenticate(request, phone_number=phone_number, password=password)
#             if user is not None:
#                 login(request, user)
#                 return Response({"message": "با موفقیت وارد شدید"}, status=status.HTTP_200_OK)
#             return Response({"error": "شماره موبایل یا پسورد اشتباه است"}, status=status.HTTP_401_UNAUTHORIZED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and is an admin
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)