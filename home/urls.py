from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from .views import HomeView,ProductListCreateAdmin,ProductViewSet,ProductsByCategory,ProductSearchAdmin,CategoryDetailAdmin,ProductSearchView,CategoryAdmin,ShoeView,ShirtView,PantsView,ProductDetailAdmin,ColorAdmin,ColorDetailAdmin


app_name = 'home'

# Configure the router
router = DefaultRouter()
router.register(r'products', ProductViewSet)
urlpatterns = [

        path('', HomeView.as_view(), name='ProductView'),
        path('Search/', ProductSearchView.as_view(), name='ProductSearchView'),
        path('padmin/', ProductListCreateAdmin.as_view(), name='ProductAdmin'),
        path('padmin/product/color/', ColorAdmin.as_view(), name='ColorAdmin'),
        path('padmin/product/color/<int:id>/', ColorDetailAdmin.as_view(), name='ColorDetailAdmin'),
        path('padmin/product/create/', ProductListCreateAdmin.as_view(), name='CreateProductAdmin'),
        path('padmin/product/<int:id>/', ProductDetailAdmin.as_view(), name='EditProductAdmin'),
        path('padmin/search/', ProductSearchAdmin.as_view(), name='product-search-admin'),
        path('padmin/category/', CategoryAdmin.as_view(), name='CreateCategoryAdmin'),
        path('padmin/category/create/', CategoryAdmin.as_view(), name='CreateCategoryAdmin'),
        path('padmin/category/<int:id>/', CategoryDetailAdmin.as_view(), name='EditCategoryAdmin'),
        path('shoes/', ShoeView.as_view(), name='ShoeView'),
        path('shirts/', ShirtView.as_view(), name='ShirtView'),
        path('pants/', PantsView.as_view(), name='PantsView'),
        path('products/category/<int:category_id>/', ProductsByCategory.as_view(), name='products-by-category'),


        path('', include(router.urls)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)