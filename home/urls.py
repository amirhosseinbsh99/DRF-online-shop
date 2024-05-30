from django.urls import path
from .views import HomeView,ProductSearchView



app_name = 'home'

urlpatterns = [
        path('', HomeView.as_view(), name='ProductView'),
        path('Search/', ProductSearchView.as_view(), name='ProductSearchView'),


]