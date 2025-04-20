from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    address = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def get_cart_total(self):
        return sum(item.calculate_price() for item in self.cart_items)
    
    def get_active_orders(self):
        return self.orders.filter(Order.status != 'cancelled').all()
    
    def get_order_history(self):
        return self.orders.order_by(Order.created_at.desc()).all()

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(256))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url,
            'is_available': self.is_available
        }

    def is_in_cart(self, user):
        if user.is_authenticated:
            return CartItem.query.filter_by(user_id=user.id, menu_item_id=self.id).first() is not None
        return False

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    item_type = db.Column(db.String(20), default='menu')  # 'menu' or 'cake'
    cake_details = db.Column(db.Text, nullable=True)  # JSON string for cake customization
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    menu_item = db.relationship('MenuItem', backref='cart_items')
    
    def get_cake_details(self):
        if self.cake_details:
            return json.loads(self.cake_details)
        return None
    
    def set_cake_details(self, details_dict):
        self.cake_details = json.dumps(details_dict)
    
    def calculate_price(self):
        if self.item_type == 'menu' and self.menu_item:
            return self.menu_item.price * self.quantity
        elif self.item_type == 'cake':
            details = self.get_cake_details()
            if details:
                # Get prices from the cake details
                flavor_price = details['flavor']['price']
                size_price = details['size']['price']
                frosting_price = details['frosting']['price']
                topping_price = details['topping']['price']
                
                # Calculate total price
                total = (flavor_price + size_price + frosting_price + topping_price) * self.quantity
                return total
        return 0
    
    def __repr__(self):
        return f'<CartItem {self.id}>'

    def to_dict(self):
        data = {
            'id': self.id,
            'quantity': self.quantity,
            'item_type': self.item_type
        }
        if self.item_type == 'menu' and self.menu_item:
            data['menu_item'] = self.menu_item.to_dict()
        elif self.item_type == 'cake':
            data['cake_details'] = self.get_cake_details()
        return data

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, completed, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    payment_method = db.Column(db.String(20))  # card, upi, cod
    payment_details = db.Column(db.String(100))  # payment ID or UPI ID
    shipping_address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.id}>'

    def get_order_items(self):
        return self.items
    
    def calculate_total(self):
        return sum(item.price * item.quantity for item in self.items)
    
    def update_status(self, new_status):
        self.status = new_status
        db.session.commit()

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=True)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    item_type = db.Column(db.String(20), default='menu')  # 'menu' or 'cake'
    item_details = db.Column(db.Text, nullable=True)  # JSON string for item details
    
    # Relationships
    menu_item = db.relationship('MenuItem', backref='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_type = db.Column(db.String(10), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    min_order_value = db.Column(db.Float, nullable=True)
    max_discount = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    times_used = db.Column(db.Integer, default=0)
    applicable_days = db.Column(db.String(50), nullable=True)  # Comma-separated days (e.g., "Monday,Tuesday")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def validate(self, cart_total):
        """Validate the coupon and return (is_valid, error_message)"""
        if not self.is_active:
            return False, "This coupon is no longer active"
            
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit"
            
        if self.min_order_value and cart_total < self.min_order_value:
            remaining = self.min_order_value - cart_total
            return False, f"Add ₹{remaining:.2f} more to your cart to use this coupon"
            
        if self.applicable_days:
            current_day = datetime.utcnow().strftime("%A")
            if current_day not in self.applicable_days.split(","):
                return False, f"This coupon is only valid on {self.applicable_days.replace(',', ', ')}"
                
        return True, None

    def calculate_discount(self, cart_total):
        if not self.is_active:
            return 0
        
        if self.min_order_value and cart_total < self.min_order_value:
            return 0

        if self.discount_type == 'percentage':
            discount = (cart_total * self.discount_value) / 100
            if self.max_discount and discount > self.max_discount:
                return self.max_discount
            return discount
        else:  # fixed
            return min(self.discount_value, cart_total)

    def get_discount_description(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        else:
            return f"₹{self.discount_value} off"

    def get_conditions(self):
        conditions = []
        if self.min_order_value:
            conditions.append(f"Min. order: ₹{self.min_order_value}")
        if self.max_discount and self.discount_type == 'percentage':
            conditions.append(f"Max. discount: ₹{self.max_discount}")
        if self.applicable_days:
            conditions.append(f"Valid on: {self.applicable_days.replace(',', ', ')}")
        if self.usage_limit:
            conditions.append(f"Usage limit: {self.usage_limit} times")
        return conditions

def init_db():
    with db.engine.connect() as conn:
        # Check if we already have menu items
        if MenuItem.query.count() == 0:
            # Create some menu items
            menu_items = [
                # Starters
                MenuItem(name="Garlic Bread", description="Freshly baked bread with garlic butter", price=199, category="starters", image_url="garlicbread.jpg"),
                MenuItem(name="Bruschetta", description="Toasted bread topped with tomatoes, garlic, and fresh basil", price=299, category="starters", image_url="bruschetta.jpg"),
                MenuItem(name="Mozzarella Sticks", description="Breaded mozzarella sticks with marinara sauce", price=249, category="starters", image_url="mozzarellasticks.jpg"),
                
                # Snacks
                MenuItem(name="French Fries", description="Crispy golden fries with ketchup", price=159, category="snacks", image_url="frenchfries.jpg"),
                MenuItem(name="Chicken Nuggets", description="Crispy chicken nuggets with dipping sauce", price=349, category="snacks", image_url="chickennuggets.jpg"),
                MenuItem(name="Onion Rings", description="Battered and fried onion rings", price=199, category="snacks", image_url="onionrings.jpg"),
                
                # Main Course
                MenuItem(name="Margherita Pizza", description="Classic pizza with tomato sauce, mozzarella, and basil", price=499, category="main-course", image_url="margheritapizza.jpg"),
                MenuItem(name="Cheeseburger", description="Beef patty with cheese, lettuce, tomato, and special sauce", price=399, category="main-course", image_url="cheeseburger.jpg"),
                MenuItem(name="Spaghetti Carbonara", description="Pasta with creamy sauce, bacon, and parmesan", price=549, category="main-course", image_url="spaghetticarbonara.jpg"),
                MenuItem(name="Grilled Chicken Salad", description="Mixed greens with grilled chicken, cherry tomatoes, and balsamic dressing", price=449, category="main-course", image_url="grilledchickensalad.jpg"),
                
                # Desserts
                MenuItem(name="Chocolate Brownie", description="Warm chocolate brownie with vanilla ice cream", price=299, category="desserts", image_url="chocolatebrownie.webp"),
                MenuItem(name="Cheesecake", description="New York style cheesecake with berry compote", price=349, category="desserts", image_url="cheesecake.jpg"),
                MenuItem(name="Ice Cream Sundae", description="Vanilla ice cream with chocolate sauce and whipped cream", price=249, category="desserts", image_url="icecreamsundae.jpg"),
                
                # Drinks
                MenuItem(name="Soda", description="Coca-Cola, Sprite, or Fanta", price=99, category="drinks", image_url="soda.jpg"),
                MenuItem(name="Iced Tea", description="Freshly brewed iced tea", price=119, category="drinks", image_url="icetea.jpg"),
                MenuItem(name="Milkshake", description="Chocolate, vanilla, or strawberry milkshake", price=199, category="drinks", image_url="milkshake.jpg"),
                MenuItem(name="Coffee", description="Freshly brewed coffee", price=129, category="drinks", image_url="coffee.jpg"),
            ]
            
            db.session.add_all(menu_items)
            db.session.commit()
