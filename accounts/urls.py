from django.urls import path
from accounts.views import SendOTPView,VerifyOTPAndCreateUserView,LogoutView,BasketListCreateView,BasketItemCreateView,LoginView,DashboardView,PaymentVerifyView,PaymentRequestView,OrderHistoryView
from accounts import views
app_name = 'account'

urlpatterns = [
    path('login/',LoginView.as_view() ,name='LoginView' ),
    path('signup/', SendOTPView.as_view(), name='signup'),
    path('signup/verify/', VerifyOTPAndCreateUserView.as_view(), name='VerifyOTPAndCreateUserView'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('basket/', BasketListCreateView.as_view(), name='basket-list-create'),
    path('basket/<int:basket_id>/items/', BasketItemCreateView.as_view(), name='basket-item-create'),
    path('basket/<int:basket_id>/request/', PaymentRequestView.as_view(), name='request'),
    path('basket/<int:basket_id>/verify/', PaymentVerifyView.as_view(), name='verify'),
    path('basket/<int:basket_id>/OrderHistory/', OrderHistoryView.as_view(), name='OrderHistory'),

]