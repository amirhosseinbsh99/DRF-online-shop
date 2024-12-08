import os
import django
from random import choice

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medesco.settings")
django.setup()

from home.models import Product, Category, Color, Size, ProductVariant

def create_products():
    # Create or get a parent category
    parent_category, _ = Category.objects.get_or_create(title="Clothing")
    subcategory, _ = Category.objects.get_or_create(title="Men's Clothing", parent=parent_category)

    # Create colors
    color1, _ = Color.objects.get_or_create(name="Red", hex_code="#FF0000")
    color2, _ = Color.objects.get_or_create(name="Blue", hex_code="#0000FF")
    color3, _ = Color.objects.get_or_create(name="Green", hex_code="#00FF00")
    colors = [color1, color2, color3]

    # Create sizes
    size_small, _ = Size.objects.get_or_create(name="S", description="Small")
    size_medium, _ = Size.objects.get_or_create(name="M", description="Medium")
    size_large, _ = Size.objects.get_or_create(name="L", description="Large")
    sizes = [size_small, size_medium, size_large]

    # Create products with variants
    for i in range(1, 25):  # Adjust the range as needed
        product, created = Product.objects.get_or_create(
            name=f"لباس {i}",
            category=subcategory,
            description=f"Description for product {i}",
            price=1000 + i,
            stock=10,  # Set default stock at the product level
        )

        # Create variants for each product
        for color in colors:
            for size in sizes:
                variant, variant_created = ProductVariant.objects.get_or_create(
                    product=product,
                    color=color,
                    size=size,
                    stock=5,  # Default stock for each variant
                    price=product.price + 100,  # Example price adjustment for variants
                )
                print(f"{'Created' if variant_created else 'Already exists'} variant: {variant}")

        print(f"{'Created' if created else 'Already exists'} product: {product}")

if __name__ == "__main__":
    create_products()
