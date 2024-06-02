from django.urls import path
from .views import HomeView,ProductAdmin,ProductSearchView,CategoryAdmin,Shoeview,ShirtView,PantsView



app_name = 'home'

urlpatterns = [
        path('', HomeView.as_view(), name='ProductView'),
        path('Search/', ProductSearchView.as_view(), name='ProductSearchView'),
        path('Padmin/', ProductAdmin.as_view(), name='ProductAdmin'),
        path('Padmin/Create', ProductAdmin.as_view(), name='CreateProductAdmin'),
        path('Padmin/<int:id>/', ProductAdmin.as_view(), name='EditProductAdmin'),
        path('Padmin/Category/Create/', CategoryAdmin.as_view(), name='CreateCategoryAdmin'),
        path('Shoes', Shoeview.as_view(), name='Shoeview'),
        path('Shirts', ShirtView.as_view(), name='ShirtView'),
        path('Pants', PantsView.as_view(), name='PantsView'),


]