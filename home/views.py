from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from .models import Product
from .serializers import ProductSerializer

class ListProductView(ListAPIView):
    queryset = Product.objects.filter(Available=True)
    serializer_class = ProductSerializer

    def get_queryset(self):
        # Update availability of products with zero stock
        zero_stock_products = Product.objects.filter(Stock=0)
        for product in zero_stock_products:
            product.Available = False
            product.save()
        
        # Return queryset excluding products with zero stock
        return Product.objects.filter(Available=True).order_by('-Created_at')
        
    
        