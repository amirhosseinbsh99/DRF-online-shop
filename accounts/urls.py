from django.urls import path
from accounts.views import SignUpView,LogoutView,LoginView,DashboardView

app_name = 'account'

urlpatterns = [
    path('login/',LoginView.as_view() ,name='LoginView' ),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]   