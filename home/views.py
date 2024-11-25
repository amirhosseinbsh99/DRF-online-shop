from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status,viewsets,pagination
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from .models import Product,Category,Color,Size
from accounts.models import Customer
from accounts.permissions import IsCustomAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import ProductSerializer,CategorySerializer,ColorSerializer,CustomerSerializer,SizeSerializer,UpdateProductSerializer
from rest_framework import filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.db.models import Q
from django.db.models import Min, Max


class ProductPagination(pagination.PageNumberPagination):
    permission_classes = [AllowAny]
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages

        # Create page list with ellipses if total pages > 10
        if total_pages > 10:
            page_range = self.get_paginated_range(current_page, total_pages)
        else:
            page_range = list(range(1, total_pages + 1))

        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'current_page': current_page,
            'total_pages': total_pages,
            'page_range': page_range,
            'results': data
        })

    def get_paginated_range(self, current_page, total_pages):
        page_range = []
        if current_page <= 6:  # First few pages
            page_range.extend(range(1, 8))
            page_range.append('...')
            page_range.append(total_pages)
        elif current_page > total_pages - 6:  # Last few pages
            page_range.append(1)
            page_range.append('...')
            page_range.extend(range(total_pages - 6, total_pages + 1))
        else:  # Middle pages
            page_range.append(1)
            page_range.append('...')
            page_range.extend(range(current_page - 2, current_page + 3))
            page_range.append('...')
            page_range.append(total_pages)
        return page_range


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny] 
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'  
    pagination_class = ProductPagination

class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination


class ProductsView(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    # Optional: Customize the list action
    def list(self, request, *args, **kwargs):
        queryset = Product.objects.filter(available=True)  # Only list available products
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AllCategories(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()  # Assuming you have a Category model
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ProductsByCategory(APIView):
    permission_classes = [AllowAny]

    def get(self, request, category_name):
        try:
            # Fetch the category by its title
            category = Category.objects.get(title=category_name)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

        # Filter products by the retrieved category
        products = Product.objects.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ProductsByColor(APIView):
    permission_classes = [AllowAny] 
    def get(self, request, color_id):
        colors = Product.objects.filter(colors=color_id)
        serializer = ProductSerializer(colors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HomeView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get(self, request):
        # Query products for each category separately
        shoes = Product.objects.filter(Q(available=True) & (Q(category__title__icontains='کفش') | Q(category__title__icontains='کتونی'))).order_by('-created_at')
        tshirts = Product.objects.filter(available=True, category__title__icontains='تیشرت').order_by('-created_at')
        pants = Product.objects.filter(available=True, category__title__icontains='شلوار').order_by('-created_at')

        # Serialize each queryset
        shoes_serializer = ProductSerializer(shoes, many=True)
        tshirts_serializer = ProductSerializer(tshirts, many=True)
        pants_serializer = ProductSerializer(pants, many=True)

        # Return response with three sections
        return Response({
            'shoes': shoes_serializer.data,
            'tshirts': tshirts_serializer.data,
            'pants': pants_serializer.data
        })


class ProductFilter(filters.FilterSet):
    permission_classes = [AllowAny]
    category = filters.ModelChoiceFilter(queryset=Category.objects.all())
    price = filters.RangeFilter()
    size = filters.ChoiceFilter(choices=lambda: [(size, size) for size in Product.objects.values_list('size', flat=True).distinct()])
    
    # Custom filter for colors
    color = filters.CharFilter(method='filter_by_color')

    class Meta:
        model = Product
        fields = ['category', 'price', 'size', 'color']

    def filter_by_color(self, queryset, name, value):
        return queryset.filter(colors__name__icontains=value)


class ProductSearchView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [drf_filters.SearchFilter, DjangoFilterBackend]
    # Use the correct lookup for filtering by colors (through the ManyToMany relation)
    search_fields = ['name', 'category__title', 'price', 'size', 'colors__name']
    filterset_class = ProductFilter  

    def list(self, request, *args, **kwargs):
        # Check if any search/filter parameters are present in the request
        

        queryset = self.filter_queryset(self.get_queryset())

        # Calculate min and max prices for the filtered queryset
        min_price = queryset.aggregate(Min('price'))['price__min']
        max_price = queryset.aggregate(Max('price'))['price__max']

        # Serialize the filtered products
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'min_price': min_price,
                'max_price': max_price,
                'products': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'min_price': min_price,
            'max_price': max_price,
            'products': serializer.data
        }, status=status.HTTP_200_OK)

#====================admin=====================#

class ProductListAdmin(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        products = Product.objects.prefetch_related('sizes')  # Assuming sizes is a related name in Product
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    

class ProductListCreateAdmin(APIView):
    authentication_classes = [JWTAuthentication]
    pagination_class = ProductPagination

    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'request': request})

        # Check if a product with the same slug already exists
        slug = request.data.get('slug')
        if Product.objects.filter(slug=slug).exists():
            return Response({'error': 'محصولی با این نام وجود دارد'}, status=status.HTTP_400_BAD_REQUEST)
  
        if serializer.is_valid():
            # Save the product instance
            product = serializer.save()

            # Handle the size relationship
            size_ids = request.data.get('size', [])  # Assuming sizes are passed as a list of size IDs
            if size_ids:
                # Fetch Size objects matching the provided IDs
                size_objects = Size.objects.filter(id__in=size_ids)
                # Set the relationship using the `set()` method
                product.size.set(size_objects)
            color_ids = request.data.get('colors', [])  # Assuming sizes are passed as a list of size IDs
            if color_ids:
                # Fetch Size objects matching the provided IDs
                color_objects = Color.objects.filter(id__in=color_ids)
                # Set the relationship using the `set()` method
                product.colors.set(color_objects)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def get(self, request):
        products = Product.objects.prefetch_related('size').order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    
    
class ProductAdmin(APIView):
    permission_classes = [IsCustomAdminUser]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        selected_product_ids = request.data.get('selected_products', [])

        # Step 1: Uncheck all products
        Product.objects.update(checkbox=False)

        # Step 2: Check the selected products
        if selected_product_ids:
            Product.objects.filter(id__in=selected_product_ids).update(checkbox=True)

        return Response({"success": "محصول آپدیت شد"})

    def get(self, request):
        products = Product.objects.order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductDetailAdmin(APIView):
    authentication_classes = [JWTAuthentication]

    def get_object(self, id):
        return get_object_or_404(Product.objects.prefetch_related('colors', 'size'), id=id)


    def get(self, request, id): 
        product = self.get_object(id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        product = self.get_object(id)
        
        data = request.data.copy()

        # Check if any field in request data is empty or null, and if so, keep the existing value from the product
        for field, value in data.items():
            if value in [None, '']:  # If the value is empty or null, retain the current value
                data[field] = getattr(product, field)

        # Handle updating the ManyToMany fields separately
        # Process color_ids and size_ids to update the relationships
        color_ids = data.get('color_ids', None)
        size_ids = data.get('size_ids', None)

        # If color_ids or size_ids are empty or missing, retain the current values
        if color_ids in [None, []]:
            color_ids = list(product.colors.values_list('id', flat=True))  # Retain the current color IDs

        if size_ids in [None, []]:
            size_ids = list(product.size.values_list('id', flat=True))  # Retain the current size IDs

        # Use the updated data to validate and save the product
        serializer = UpdateProductSerializer(product, data=data, partial=kwargs.get('partial', False), context={'request': request})

        # If the serializer is valid, save the object and return the response
        if serializer.is_valid():
            # Save the product first
            product = serializer.save()

            # Update the ManyToMany relationships with retained or new IDs
            product.colors.set(color_ids)  # Update the colors
            product.size.set(size_ids)  # Update the sizes

            # Save the product with the updated relationships
            product.save()

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
    def delete(self, request, id):  
        product = self.get_object(id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductSearchAdmin(APIView):
    # permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

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
    authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAdminUser]
    def post(self, request):
        data = request.data
        if Category.objects.filter(title=data.get('title')).exists():
            return Response({'error': 'دسته بندی تکراری میباشد'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        

    def get(self, request):
        category = Category.objects.all().order_by('-created_date')
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)


class CategoryDetailAdmin(APIView):
    authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAdminUser]

    def get(self, request, name):
        # Retrieve the category by name
        category = get_object_or_404(Category, name=name)
        
        # Get the child categories (if any)
        child_categories = category.children.all()  # 'children' is the related_name for the parent field

        # Serialize the parent category
        category_serializer = CategorySerializer(category)

        # Serialize the child categories
        child_serializer = CategorySerializer(child_categories, many=True)

        # Combine the data
        data = {
            'category': category_serializer.data,
            'child_categories': child_serializer.data
        }

        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, name):
        # Retrieve the category by name
        category = get_object_or_404(Category, name=name)
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, name):
        # Retrieve the category by name
        category = get_object_or_404(Category, name=name)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ColorsVeiw(APIView):
    permission_classes = [AllowAny] 
    def get(self, request):
        color = Color.objects.all()
        serializer = ColorSerializer(color, many=True)
        return Response(serializer.data)

class SizeCreateView(APIView):
    def post(self, request):
        size_name = request.data.get('name')  # Adjust this to your Size model's unique field
        
        # Check if size with the given name already exists
        if Size.objects.filter(name=size_name).exists():  
            return Response({'error': 'سایز تکراری است'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = SizeSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class SizeListView(APIView):
    def get(self, request):
        sizes = Size.objects.all()  # Get all sizes
        serializer = SizeSerializer(sizes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class SizeUpdateView(APIView):
    def put(self, request, pk):
        size = Size.objects.filter(id=pk).first()
        
        if not size:
            return Response({'error': 'Size not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SizeSerializer(size, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ColorAdmin(APIView):
    authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAdminUser]
    def post(self, request):
        data = request.data
        if Color.objects.filter(name=data.get('name')).exists():
            return Response({'error': 'رنگ تکراری میباشد'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ColorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        color = Color.objects.all()
        serializer = ColorSerializer(color, many=True)
        return Response(serializer.data)


class ColorDetailAdmin(APIView):
    
    # permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def get_object(self, id):
        try:
            return Color.objects.get(id=id)
        except Color.DoesNotExist:
            return None

    def get(self, request, id):
        color = self.get_object(id)
        if not color:
            return Response({'error': 'رنگ مورد نظر یافت نشد '}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ColorSerializer(color)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        color = self.get_object(id)
        if not color:
            return Response({'error': 'رنگ تکراری میباشد'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ColorSerializer(color, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):

        color = Color.objects.get(id=id)
        color.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoeView(APIView):

    def get(self, request):
        # Get all categories containing the word "کفش"
        shoe_categories = Category.objects.filter(title__icontains="کفش")
        
        # Get all products related to these categories
        shoes = Product.objects.filter(available=True, category__in=shoe_categories).order_by('-created_at')

        # Serialize the product data
        serializer = ProductSerializer(shoes, many=True)
        
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
    
class CustomerPagination(PageNumberPagination):
    page_size = 30  # Number of items per page
    page_size_query_param = 'page_size'  # Allows the user to set a custom page size in the query params
    max_page_size = 100

class CustomerListView(ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    pagination_class = CustomerPagination 
    permission_classes = [AllowAny] 





    #if needed edit it and use it(product rating)
# class RateProductView(APIView):
    
#     # permission_classes = [IsAuthenticated]

#     def post(self, request, product_slug):
#         product = get_object_or_404(Product, slug=product_slug)
#         rating = request.data.get('rating')

#         if rating is None:
#             return Response({"error": "Rating is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             rating = int(rating)
#             if rating < 1 or rating > 5:
#                 return Response({"error": "Rating must be between 1 and 5"}, status=status.HTTP_400_BAD_REQUEST)
#         except ValueError:
#             return Response({"error": "Invalid rating value"}, status=status.HTTP_400_BAD_REQUEST)
#         product.total_rating += rating
#         product.number_of_ratings += 1
#         product.star_rating = product.average_rating  
#         product.save()
#         return Response({"average_rating": product.star_rating}, status=status.HTTP_200_OK)
        