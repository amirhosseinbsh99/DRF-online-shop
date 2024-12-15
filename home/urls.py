from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    HomeView,
    ProductListCreateAdmin,
    ProductSearchView,
    ProductAdmin,
    ProductDetailAdmin,
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
    ProductViewSet,
    CustomerListView,
    SizeCreateView,
    SizeListView,
    SizeUpdateView,
    ProductDetailBySlugView,
    ProductListAdmin,
    UploadProductImagesView,
    ProductVariantAdminView,
    DeleteProductImageView,
    GetProductImagesView
)
from accounts.views import OrderHistoryAdminView

app_name = 'home'

# Configure the router
router = DefaultRouter()
# router.register(r'products', ProductViewSet)


urlpatterns = [
    # Home view
    path('', HomeView.as_view(), name='HomeView'),
    
    # Product search
    path('search/', ProductSearchView.as_view(), name='ProductSearchView'),

    # Admin product views
    path('padmin/', ProductListAdmin.as_view(), name='ProductListAdmin'),
    path('padmin/product/', ProductAdmin.as_view(), name='ProductAdmin'),
    path('padmin/product/create/', ProductListCreateAdmin.as_view(), name='CreateProductAdmin'),
    path('padmin/<slug:product_slug>/upload-images/', UploadProductImagesView.as_view(), name='upload-product-images'),
    path('padmin/<slug:product_slug>/images/<int:image_id>/delete/', DeleteProductImageView.as_view(), name='delete-product-image'),
    path('padmin/<slug:product_slug>/images/', GetProductImagesView.as_view(), name='get-product-image'),
    path('padmin/product/<int:id>/', ProductDetailAdmin.as_view(), name='EditProductAdmin'),
    path('padmin/customers/', CustomerListView.as_view(), name='CustomerListView'),
    # Admin color views
    path('padmin/product/color/', ColorAdmin.as_view(), name='ColorAdmin'),
    path('padmin/product/color/<int:id>/', ColorDetailAdmin.as_view(), name='ColorDetailAdmin'),
    #Admin Size
    path('padmin/sizes/', SizeListView.as_view(), name='size-list'),
    path('padmin/sizes/create/', SizeCreateView.as_view(), name='size-create'),
    path('padmin/sizes/<int:pk>/', SizeUpdateView.as_view(), name='size-update'),
    #admin variant
    path('padmin/product-variant/create/', ProductVariantAdminView.as_view(), name='product_variant_create'),
    path('padmin/product-variant/<int:id>/', ProductVariantAdminView.as_view(), name='product_variant_update_delete'),  
    
    # Admin category views
    path('padmin/category/', CategoryAdmin.as_view(), name='CategoryAdmin'),
    path('padmin/category/create/', CategoryAdmin.as_view(), name='CreateCategoryAdmin'),
    path('padmin/category/<str:name>/', CategoryDetailAdmin.as_view(), name='EditCategoryAdmin'),

    path('padmin/OrderHistoryAdminView/', OrderHistoryAdminView.as_view(), name='OrderHistoryAdminView'),
    
    # Products by category & color
    path('products/', ProductViewSet.as_view({'get': 'list'}), name='products-list'),
    path('products/category/', AllCategories.as_view(), name='AllCategories'),
    path('products/category/<str:category_name>/', ProductsByCategory.as_view(), name='products-by-category'),
    path('products/color/', ColorsVeiw.as_view(), name='products-by-color'),
    path('products/color/<int:color_id>/', ProductsByColor.as_view(), name='products-by-color'),
    #path('products/<slug:slug>/', ProductDetailBySlugView.as_view(), name='product-detail-slug'),
    re_path(r'^products/(?P<slug>[-\w\u0600-\u06FF]+)/$', ProductDetailBySlugView.as_view(), name='product-detail-slug'),

    # Product views for specific categories
    path('shoes/', ShoeView.as_view(), name='ShoeView'),
    path('shirts/', ShirtView.as_view(), name='ShirtView'),
    path('pants/', PantsView.as_view(), name='PantsView'),
    
    # Include the API router for product-related actions
    # path('api/', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
