from django.urls import path
from .views import HomeView,ProductSearchView,ProductAdmin



app_name = 'home'

urlpatterns = [
        path('', HomeView.as_view(), name='ProductView'),
        path('Search/', ProductSearchView.as_view(), name='ProductSearchView'),
        path('Padmin/', ProductAdmin.as_view(), name='ProductAdmin'),
        path('Padmin/Create', ProductAdmin.as_view(), name='CreateProductAdmin'),
        path('Padmin/<int:id>/', ProductAdmin.as_view(), name='EditProductAdmin'),


]