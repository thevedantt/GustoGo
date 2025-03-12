from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from decimal import Decimal, ROUND_HALF_UP

db = SQLAlchemy()
logger = logging.getLogger(__name__)

# Create separate database engines for menu and cake databases
menu_engine = create_engine('sqlite:///instance/menu_db.db')
cake_engine = create_engine('sqlite:///instance/cakes_db.db')

# Create separate sessions for menu and cake databases
MenuSession = sessionmaker(bind=menu_engine)
CakeSession = sessionmaker(bind=cake_engine)

# Context manager for database sessions
class DatabaseSession:
    """Context manager for database sessions to ensure proper cleanup"""
    def __init__(self, session_class):
        self.session_class = session_class
        self.session = None
        
    def __enter__(self):
        self.session = self.session_class()
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is not None:
                    # An exception occurred, rollback
                    self.session.rollback()
                self.session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {str(e)}")
                
# Convenience functions for database sessions
def with_menu_session():
    """Get a menu database session with context manager"""
    return DatabaseSession(MenuSession)
    
def with_cake_session():
    """Get a cake database session with context manager"""
    return DatabaseSession(CakeSession)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    items = db.relationship('MenuItem', backref='category', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<MenuItem {self.name}>'

class CakeFlavor(db.Model):
    __tablename__ = 'cake_flavors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_per_kg = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))  # Single or Combination
    image_url = db.Column(db.String(200))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<CakeFlavor {self.name}>'

class CakeOrder(db.Model):
    __tablename__ = 'cake_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    flavor_id = db.Column(db.Integer, db.ForeignKey('cake_flavors.id'), nullable=False)
    size_kg = db.Column(db.Float, nullable=False)
    message = db.Column(db.String(100))
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_date = db.Column(db.DateTime, nullable=False)
    special_instructions = db.Column(db.Text)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # Relationship with CakeFlavor
    flavor = db.relationship('CakeFlavor', backref='orders')

    def to_dict(self):
        return {
            'id': self.id,
            'flavor': self.flavor.name,
            'size_kg': self.size_kg,
            'message': self.message,
            'customer_name': self.customer_name,
            'delivery_date': self.delivery_date,
            'total_price': self.total_price,
            'status': self.status
        }

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __init__(self, session_id):
        self.session_id = session_id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def get_subtotal(self):
        """Calculate the subtotal of all items in the cart (before delivery fee)"""
        try:
            return sum(item.get_subtotal() for item in self.items)
        except Exception as e:
            logger.error(f"Error calculating cart subtotal: {str(e)}")
            return 0

    def get_delivery_fee(self):
        """Calculate the delivery fee based on cart subtotal"""
        subtotal = self.get_subtotal()
        if subtotal >= 1000:  # Free delivery for orders over ₹1000
            return 0
        return 50  # Standard delivery fee of ₹50

    def get_total(self):
        """Calculate the total price including delivery fee"""
        return self.get_subtotal() + self.get_delivery_fee()

    def get_total_price(self):
        """Alias for get_total for backward compatibility"""
        return self.get_total()

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'items': [item.to_dict() for item in self.items],
            'subtotal': self.get_subtotal(),
            'delivery_fee': self.get_delivery_fee(),
            'total': self.get_total(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def add_item(self, item_type, item_id, quantity=1, **kwargs):
        try:
            existing_item = CartItem.query.filter_by(
                cart_id=self.id,
                item_type=item_type,
                item_id=item_id
            ).first()

            if existing_item:
                existing_item.quantity = min(existing_item.quantity + quantity, 10)
            else:
                cart_item = CartItem(
                    cart_id=self.id,
                    item_type=item_type,
                    item_id=item_id,
                    quantity=min(quantity, 10)
                )
                
                # Add additional attributes (e.g., size_kg, message for cakes)
                for key, value in kwargs.items():
                    setattr(cart_item, key, value)
                
                db.session.add(cart_item)
            
            return True
        except Exception as e:
            print(f"Error adding item to cart: {str(e)}")
            return False

    def update_item_quantity(self, item_id, quantity):
        try:
            item = CartItem.query.get(item_id)
            if item and item.cart_id == self.id:
                if quantity < 1:
                    db.session.delete(item)
                else:
                    item.quantity = min(quantity, 10)
                return True
            return False
        except Exception as e:
            print(f"Error updating cart item quantity: {str(e)}")
            return False

    def remove_item(self, item_id):
        try:
            item = CartItem.query.get(item_id)
            if item and item.cart_id == self.id:
                db.session.delete(item)
                return True
            return False
        except Exception as e:
            print(f"Error removing item from cart: {str(e)}")
            return False

    def clear(self):
        try:
            for item in self.items:
                db.session.delete(item)
            return True
        except Exception as e:
            print(f"Error clearing cart: {str(e)}")
            return False

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'menu_item' or 'cake'
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    # For cakes
    size_kg = db.Column(db.Float)
    message = db.Column(db.String(100))
    special_instructions = db.Column(db.Text)
    customization_details = db.Column(db.Text)  # JSON string for cake customizations
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def get_item(self):
        try:
            if self.item_type == 'menu_item' or self.item_type == 'menu':
                with with_menu_session() as session:
                    return session.query(MenuItem).get(self.item_id)
            elif self.item_type == 'cake':
                with with_cake_session() as session:
                    return session.query(CakeFlavor).get(self.item_id)
            return None
        except Exception as e:
            logger.error(f"Error in get_item: {str(e)}")
            return None

    def calculate_cake_price(self, base_price, size_kg, customization_details):
        """Calculate the final price of a customized cake"""
        try:
            # Convert to Decimal for precise calculations
            total = Decimal(str(base_price))
            size = Decimal(str(size_kg))
            
            # Base price calculation (price per kg × size)
            total = total * size
            
            if customization_details:
                try:
                    details = json.loads(customization_details) if isinstance(customization_details, str) else customization_details
                    
                    # Icing type costs
                    icing_prices = {
                        'fondant': Decimal('200'),
                        'ganache': Decimal('150'),
                        'buttercream': Decimal('100'),
                        'whipped_cream': Decimal('80')
                    }
                    
                    # Add icing cost
                    icing_type = details.get('icing_type', '').lower()
                    if icing_type in icing_prices:
                        total += icing_prices[icing_type]
                    
                    # Add toppings cost (₹100 per topping)
                    toppings = details.get('toppings', [])
                    if isinstance(toppings, list) and toppings:
                        total += len(toppings) * Decimal('100')
                    
                    # Add special instructions cost
                    if details.get('special_instructions', '').strip():
                        total += Decimal('150')
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.error(f"Error parsing customization details: {str(e)}")
                    # Don't add any customization costs if there's an error
            
            # Round to 2 decimal places
            return float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        except Exception as e:
            logger.error(f"Error calculating cake price: {str(e)}")
            # Fallback to basic calculation with proper decimal handling
            try:
                return float((Decimal(str(base_price)) * Decimal(str(size_kg))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            except:
                return float(base_price * size_kg)  # Last resort fallback

    def get_subtotal(self):
        """Calculate the total price for this cart item"""
        try:
            item = self.get_item()
            if not item:
                return 0
            
            if self.item_type == 'menu_item' or self.item_type == 'menu':
                return item.price * self.quantity
            elif self.item_type == 'cake':
                # Get base price and size
                base_price = item.price_per_kg
                size = self.size_kg or 1
                
                # Calculate unit price with customizations
                unit_price = self.calculate_cake_price(
                    base_price=base_price,
                    size_kg=size,
                    customization_details=self.customization_details
                )
                
                # Return total price (unit price × quantity)
                return unit_price * self.quantity
            return 0
        except Exception as e:
            logger.error(f"Error in get_subtotal: {str(e)}")
            return 0

    def to_dict(self):
        """Convert cart item to dictionary with all necessary information"""
        try:
            item = self.get_item()
            if not item:
                return {
                    'id': self.id,
                    'item_type': self.item_type,
                    'quantity': self.quantity,
                    'subtotal': 0
                }
            
            base_dict = {
                'id': self.id,
                'item_type': self.item_type,
                'quantity': self.quantity,
            }
            
            if self.item_type == 'menu_item' or self.item_type == 'menu':
                base_dict.update({
                    'name': item.name,
                    'price': item.price,
                    'subtotal': self.get_subtotal(),
                    'image_url': item.image_url
                })
            elif self.item_type == 'cake':
                # Calculate prices
                base_price = item.price_per_kg
                size = self.size_kg or 1
                unit_price = self.calculate_cake_price(
                    base_price=base_price,
                    size_kg=size,
                    customization_details=self.customization_details
                )
                subtotal = unit_price * self.quantity
                
                # Parse customization details
                try:
                    customization = json.loads(self.customization_details) if self.customization_details else {}
                except json.JSONDecodeError:
                    customization = {}
                
                base_dict.update({
                    'name': item.name,
                    'base_price_per_kg': base_price,
                    'size_kg': size,
                    'unit_price': unit_price,
                    'subtotal': subtotal,
                    'message': self.message,
                    'customization_details': customization,
                    'image_url': item.image_url
                })
            
            return base_dict
        except Exception as e:
            logger.error(f"Error in to_dict: {str(e)}")
            return {
                'id': self.id,
                'item_type': self.item_type,
                'quantity': self.quantity,
                'subtotal': 0
            }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    delivery_instructions = db.Column(db.Text)
    payment_method = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'pincode': self.pincode,
            'delivery_instructions': self.delivery_instructions,
            'payment_method': self.payment_method,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'menu' or 'cake'
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    size_kg = db.Column(db.Float)  # Only for cakes
    message = db.Column(db.Text)  # Only for cakes

    def get_item(self):
        if self.item_type == 'menu':
            return MenuItem.query.get(self.item_id)
        elif self.item_type == 'cake':
            return CakeFlavor.query.get(self.item_id)
        return None

    def to_dict(self):
        item_dict = {
            'id': self.id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'price': self.price,
            'subtotal': self.subtotal
        }
        if self.item_type == 'cake':
            item_dict.update({
                'size_kg': self.size_kg,
                'message': self.message
            })
        return item_dict 

        # Update to Cart model methods for better integration with routes

def increase_item_quantity(self, item_id):
    """Increase the quantity of an item in the cart"""
    try:
        item = CartItem.query.get(item_id)
        if item and item.cart_id == self.id:
            item.quantity = min(item.quantity + 1, 10)  # Cap at 10 items
            item.updated_at = datetime.now(timezone.utc)
            return True
        return False
    except Exception as e:
        logger.error(f"Error increasing item quantity: {str(e)}")
        return False

def decrease_item_quantity(self, item_id):
    """Decrease the quantity of an item in the cart"""
    try:
        item = CartItem.query.get(item_id)
        if item and item.cart_id == self.id:
            if item.quantity > 1:
                item.quantity -= 1
                item.updated_at = datetime.now(timezone.utc)
            else:
                # If quantity would go below 1, remove the item
                db.session.delete(item)
            return True
        return False
    except Exception as e:
        logger.error(f"Error decreasing item quantity: {str(e)}")
        return False