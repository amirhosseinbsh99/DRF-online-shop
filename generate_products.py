import os
import django
from random import choice
from home.models import Product, Category, Color

# Set up Django settings (make sure the path is correct)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medesco.settings")

# Initialize Django
django.setup()

def create_products():
    # Create a category (optional)
    category = Category.objects.create(title="Clothing")

    # Create some colors (optional)
    color1 = Color.objects.create(name="Red", hex_code="#FF0000")
    color2 = Color.objects.create(name="Blue", hex_code="#0000FF")
    color3 = Color.objects.create(name="Green", hex_code="#00FF00")
    colors = [color1, color2, color3]

    # Create 24 products
    for i in range(1, 25):
        product = Product.objects.create(
            name=f"Product {i}",
            category=category,
            description=f"Description for product {i}",
            price=1000 + i,
            stock=10,
            colors=[choice(colors)],  # Randomly assign one of the colors
        )
        product.save()
        print(f"Created product {i}: {product.name}")

if __name__ == "__main__":
    create_products()
