from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    HomeView,
    ProductListCreateAdmin,
    ProductSearchView,
    ProductAdmin,
    ProductDetailAdmin,
    ProductsView,
    ColorAdmin,
    ColorDetailAdmin,
    CategoryAdmin,
    CategoryDetailAdmin,
    ShoeView,
    ShirtView,
    PantsView,
    AllCategories,
    ProductsByCategory,
    ProductsByColor,
    ColorsVeiw,
    ProductViewSet
)

app_name = 'home'

# Configure the router
router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    # Home view
    path('', HomeView.as_view(), name='HomeView'),
    
    # Product search
    path('search/', ProductSearchView.as_view(), name='ProductSearchView'),
    
    # Admin product views
    path('padmin/', ProductListCreateAdmin.as_view(), name='ProductAdmin'),
    path('padmin/product/', ProductAdmin.as_view(), name='ProductAdmin'),
    path('padmin/product/create/', ProductListCreateAdmin.as_view(), name='CreateProductAdmin'),
    path('padmin/product/<int:id>/', ProductDetailAdmin.as_view(), name='EditProductAdmin'),
    
    # Admin color views
    path('padmin/product/color/', ColorAdmin.as_view(), name='ColorAdmin'),
    path('padmin/product/color/<int:id>/', ColorDetailAdmin.as_view(), name='ColorDetailAdmin'),
    
    # Admin category views
    path('padmin/category/', CategoryAdmin.as_view(), name='CategoryAdmin'),
    path('padmin/category/create/', CategoryAdmin.as_view(), name='CreateCategoryAdmin'),
    path('padmin/category/<str:name>/', CategoryDetailAdmin.as_view(), name='EditCategoryAdmin'),
    
    # Products by category & color
    path('products/', ProductViewSet.as_view({'get': 'list'}), name='products-list'),
    path('products/category/', AllCategories.as_view(), name='AllCategories'),
    path('products/category/<str:category_name>/', ProductsByCategory.as_view(), name='products-by-category'),
    path('products/color/', ColorsVeiw.as_view(), name='products-by-color'),
    path('products/color/<int:color_id>/', ProductsByColor.as_view(), name='products-by-color'),
    
    # Product views for specific categories
    path('shoes/', ShoeView.as_view(), name='ShoeView'),
    path('shirts/', ShirtView.as_view(), name='ShirtView'),
    path('pants/', PantsView.as_view(), name='PantsView'),
    
    # Include the API router for product-related actions
    path('api/', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
