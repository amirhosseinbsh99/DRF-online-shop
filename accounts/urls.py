from django.urls import path
from accounts.views import SignUpView

app_name = 'account'

urlpatterns = [
    # path('login/',LoginView.as_view() ,name='LoginView' ),
    path('signup/', SignUpView.as_view(), name='signup'),

]