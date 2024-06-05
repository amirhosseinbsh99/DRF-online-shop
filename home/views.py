from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import ListAPIView
from .models import Product,Category,Basket, BasketItem
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
    size = filters.ChoiceFilter(choices=lambda: [(size, size) for size in Product.objects.values_list('size', flat=True).distinct()])
    
    # Custom filter for colors
    color = filters.CharFilter(method='filter_by_color')

    class Meta:
        model = Product
        fields = ['category', 'price', 'size', 'color']

    def filter_by_color(self, queryset, name, value):
        return queryset.filter(color__icontains=value)

class ProductSearchView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [drf_filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'category__title', 'price', 'size', 'color']
    filterset_class = ProductFilter  # Use the filter set here

class ProductListCreateAdmin(APIView):

    # permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    
    

        
class ProductDetailAdmin(APIView):

    # permission_classes = [IsAdminUser]

    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({"error": "محصول یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({"error": "محصول یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"error": "محصول یافت نشد"}, status=status.HTTP_404_NOT_FOUND)


class ProductSearchAdmin(APIView):

    # permission_classes = [IsAdminUser]

    def get(self, request):
        query = request.query_params.get('q', None)
        if query:
            products = Product.objects.filter(name__icontains=query)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No search query provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        #http://127.0.0.1:8000/padmin/search/?q=nike
    
class CategoryAdmin(APIView):
    # permission_classes = [IsAdminUser]

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
    
class CategoryDetailAdmin(APIView):
    # permission_classes = [IsAdminUser]

    def get_object(self, id):
        try:
            return Category.objects.get(id=id)
        except Category.DoesNotExist:
            return None

    def get(self, request, id):
        category = self.get_object(id)
        if not category:
            return Response({"error": "دسته بندی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        category = self.get_object(id)
        if not category:
            return Response({"error": "دسته بندی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        category = self.get_object(id)
        if not category:
            return Response({"error": "دسته بندی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

class Shoeview(APIView):

    def get(self, request):
        category = Category.objects.filter(title__icontains="کفش").order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)
    
class ShirtView(APIView):

    def get(self, request):
        category = Category.objects.filter(title__icontains="لباس").order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)
    
class PantsView(APIView):

    def get(self, request):
        category = Category.objects.filter(title__icontains="شلوار").order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)

class BasketView(APIView):
    def get(self, request):
        basket, created = Basket.objects.get_or_create(user=request.user)
        serializer = BasketSerializer(basket)
        return Response(serializer.data)

    def post(self, request):
        basket, created = Basket.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        product = get_object_or_404(Product, id=product_id)
        basket_item, created = BasketItem.objects.get_or_create(basket=basket, product=product)
        basket_item.quantity += int(quantity)
        basket_item.save()
        serializer = BasketSerializer(basket)
        return Response(serializer.data)

    def delete(self, request, product_id):
        basket, created = Basket.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, id=product_id)
        basket_item = get_object_or_404(BasketItem, basket=basket, product=product)
        basket_item.delete()
        serializer = BasketSerializer(basket)
        return Response(serializer.data)
    
        