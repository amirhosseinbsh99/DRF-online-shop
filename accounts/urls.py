from django.urls import path
from accounts.views import (
    SendOTPView,
    VerifyOTPAndCreateUserView,
    LogoutView,
    BasketListCreateView,
    BasketItemCreateView,
    LoginView,
    DashboardView,
    PaymentVerifyView,
    PaymentRequestView,
    OrderHistoryView,
    SendPasswordResetOTPView,
    VerifyPasswordResetOTPView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'account'


urlpatterns = [
    # Authentication & Authorization
    path('login/', LoginView.as_view(), name='login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),


    # Signup & Password Reset
    path('signup/', SendOTPView.as_view(), name='signup'),
    path('signup/verify/', VerifyOTPAndCreateUserView.as_view(), name='verify_signup'),
    path('resetpassword/', SendPasswordResetOTPView.as_view(), name='reset_password'),
    path('resetpassword/verify/', VerifyPasswordResetOTPView.as_view(), name='verify_reset_password'),
    
    # Dashboard & User-specific actions
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Basket & Payment
    path('basket/', BasketListCreateView.as_view(), name='basket_list_create'),
    path('basket/<int:basket_id>/items/', BasketItemCreateView.as_view(), name='basket_item_create'),
    path('basket/<int:basket_id>/request/', PaymentRequestView.as_view(), name='payment_request'),
    path('basket/<int:basket_id>/verify/', PaymentVerifyView.as_view(), name='payment_verify'),
    path('basket/<int:basket_id>/order_history/', OrderHistoryView.as_view(), name='order_history'),
]