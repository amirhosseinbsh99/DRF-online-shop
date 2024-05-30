from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from .models import Product
from .serializers import ProductSerializer
from rest_framework import filters 


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
    
class ProductSearchView(ListAPIView):
    queryset =Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['$name']
    


        
    
        