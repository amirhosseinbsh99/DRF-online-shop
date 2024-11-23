import os
import django
from random import choice
# Set up Django settings (make sure the path is correct)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medesco.settings")

# Initialize Django
django.setup()

from home.models import Product, Category, Color  # Import after django.setup()

def create_products():
    # Create a category (optional)
    category, _ = Category.objects.get_or_create(title="Clothing")  # Avoid duplicate categories

    # Create some colors (optional)
    color1, _ = Color.objects.get_or_create(name="Red", hex_code="#FF0000")
    color2, _ = Color.objects.get_or_create(name="Blue", hex_code="#0000FF")
    color3, _ = Color.objects.get_or_create(name="Green", hex_code="#00FF00")
    colors = [color1, color2, color3]

    # Create 24 products
    for i in range(1, 300):
        product, created = Product.objects.get_or_create(
            name=f"Product {i}",
            category=category,
            description=f"Description for product {i}",
            price=1000 + i,
            stock=10,
        )
        product.colors.add(choice(colors))  # Add a random color to the product
        print(f"{'Created' if created else 'Already exists'} product {i}: {product.name}")

if __name__ == "__main__":
    create_products()
