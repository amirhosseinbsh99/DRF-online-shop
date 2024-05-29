from django.urls import path
from .views import ListProductView



app_name = 'home'

urlpatterns = [
        path('', ListProductView.as_view(), name='ConcertAdminView'),


]