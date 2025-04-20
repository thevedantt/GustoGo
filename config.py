import os

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///gustogo.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Application configuration
DEBUG = True
SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Stripe configuration
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_your_key')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_key')

# Domain configuration for Stripe callbacks
DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
if os.environ.get('REPLIT_DEPLOYMENT') == '' and os.environ.get('REPLIT_DOMAINS'):
    DOMAIN = os.environ.get('REPLIT_DOMAINS').split(',')[0]

# Static files configuration
STATIC_FOLDER = 'static'
TEMPLATES_FOLDER = 'templates'

# Menu categories
MENU_CATEGORIES = [
    {"id": "starters", "name": "Starters"},
    {"id": "snacks", "name": "Snacks"},
    {"id": "main-course", "name": "Main Course"},
    {"id": "desserts", "name": "Desserts"},
    {"id": "drinks", "name": "Drinks"}
]

# Cake customization options
CAKE_FLAVORS = [
    {"id": "vanilla", "name": "Vanilla", "price": 300.00},
    {"id": "chocolate", "name": "Chocolate", "price": 350.00},
    {"id": "strawberry", "name": "Strawberry", "price": 400.00},
    {"id": "red-velvet", "name": "Red Velvet", "price": 450.00}
]

CAKE_SIZES = [
    {"id": "small", "name": "Small (6\")", "price": 0.00},
    {"id": "medium", "name": "Medium (8\")", "price": 200.00},
    {"id": "large", "name": "Large (10\")", "price": 400.00}
]

CAKE_FROSTINGS = [
    {"id": "buttercream", "name": "Buttercream", "price": 0.00},
    {"id": "cream-cheese", "name": "Cream Cheese", "price": 100.00},
    {"id": "fondant", "name": "Fondant", "price": 200.00}
]

CAKE_TOPPINGS = [
    {"id": "none", "name": "No Topping", "price": 0.00},
    {"id": "fresh-fruits", "name": "Fresh Fruits", "price": 150.00},
    {"id": "chocolate-chips", "name": "Chocolate Chips", "price": 100.00},
    {"id": "sprinkles", "name": "Sprinkles", "price": 50.00}
]
