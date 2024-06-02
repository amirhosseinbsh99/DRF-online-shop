from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import ListAPIView
from .models import Product,Category
from .serializers import ProductSerializer,CategorySerializer
from rest_framework import filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from accounts.views import IsAdminUser



class HomeView(ListAPIView):
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Update availability of products with zero stock
        zero_stock_products = Product.objects.filter(stock=0)
        for product in zero_stock_products:
            product.Available = False
            product.save()
        
        # Return queryset excluding products with zero stock
        return Product.objects.filter(available=True).order_by('-created_at')
    
class ProductFilter(filters.FilterSet):
    category = filters.ModelChoiceFilter(queryset=Category.objects.all())
    price = filters.NumberFilter()
    size = filters.ChoiceFilter(choices=[(size, size) for size in Product.objects.values_list('size', flat=True).distinct()])
    color = filters.ChoiceFilter(choices=[(color, color) for color in Product.objects.values_list('color', flat=True).distinct()])

    class Meta:
        model = Product
        fields = ['category', 'price', 'size', 'color']

class ProductSearchView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [drf_filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'category__title', 'price', 'size', 'color']
    filterset_class = ProductFilter  # Use the filter set here

class ProductAdmin(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        request.data 
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
class CategoryAdmin(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        request.data 
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        category = Category.objects.all().order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)
    
class Shoeview(APIView):

    def get(self, request):
        category = Category.objects.filter(title__icontains="shoe").order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)
    
class ShirtView(APIView):

    def get(self, request):
        category = Category.objects.filter(title__icontains="Shirt").order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)
    
class PantsView(APIView):

    def get(self, request):
        category = Category.objects.filter(title__icontains="pants").order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)
        
    
        