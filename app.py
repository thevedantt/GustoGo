import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Category, MenuItem, CakeFlavor, CakeOrder, Order, OrderItem, Cart, CartItem, MenuSession, CakeSession
from models import with_menu_session, with_cake_session
from functools import wraps
import logging
from datetime import datetime, timedelta, timezone
import json
import stripe

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///gustogo.db'  # Main database for cart and orders
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_USE_SIGNER = True
    # Test keys for development - these are Stripe test keys that will work
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51OvQXWSJnCnKlvxPJnCGQXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51OvQXWSJnCnKlvxPJnCGQXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

app.config.from_object(Config)

# Initialize Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# For development - use a simple checkout page instead of Stripe if keys aren't set
USE_SIMPLE_CHECKOUT = False  # Set to False to always use Stripe checkout

if not app.config['STRIPE_SECRET_KEY'] or not app.config['STRIPE_PUBLISHABLE_KEY']:
    logger.warning('Stripe keys not set. Payment functionality will not work.')
    USE_SIMPLE_CHECKOUT = True

# Initialize database
db.init_app(app)

def init_db():
    """Initialize the main database with required tables"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Main database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize main database: {str(e)}")
        raise

# Error handling decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            # Only redirect if we're not already on the error page
            if request.endpoint != 'error_page':
                flash('An error occurred. Please try again.', 'error')
                return redirect(url_for('error_page'))
            return render_template('error.html', error=str(e))
    return decorated_function

# Make sessions permanent by default
@app.before_request
def make_session_permanent():
    """Make the session permanent and initialize session ID if needed"""
    session.permanent = True
    
    # Ensure we have a session ID
    if '_id' not in session:
        session['_id'] = os.urandom(16).hex()
        logger.debug(f"Generated new session ID: {session['_id']}")
        session.modified = True
    
    # Initialize cart variable
    cart = None

    # Check if we need to create a cart
    if 'cart_id' not in session and request.endpoint != 'static':
        logger.debug("No cart in session, checking if we should create one")
        # Only create cart for non-static requests
        if request.endpoint and not request.endpoint.startswith('static'):
            cart = create_cart()
    if cart:
        # Ensure the cart is cleared after order confirmation
        session.pop('cart_id', None)
        logger.debug(f"Created new cart with ID: {cart.id}")
        session['cart_id'] = cart.id
    else:
        logger.warning("No cart was created or found.")
    session.modified = True

# Cart management functions
def get_cart():
    """Get the current user's cart from the session"""
    try:
        logger.debug("Starting get_cart function")
        if 'cart_id' not in session:
            logger.debug("No cart_id in session")
            return None
            
        logger.debug(f"Found cart_id in session: {session['cart_id']}")
        cart = Cart.query.get(session['cart_id'])
        if not cart:
            # Clear invalid cart ID from session
            logger.warning(f"Cart with ID {session['cart_id']} not found in database")
            session.pop('cart_id', None)
            return None
            
        # Check if cart is expired (older than 24 hours)
        cart_age = (datetime.now() - cart.created_at).total_seconds()
        if cart_age > app.config['PERMANENT_SESSION_LIFETIME']:
            logger.info(f"Cart {cart.id} expired after {cart_age} seconds")
            # Delete expired cart
            db.session.delete(cart)
            db.session.commit()
            session.pop('cart_id', None)
            return None
            
        logger.debug(f"Returning valid cart with ID: {cart.id}, containing {len(cart.items)} items")
        return cart
    except Exception as e:
        logger.error(f"Error in get_cart: {str(e)}")
        # Clear cart ID from session on error
        session.pop('cart_id', None)
        return None

def create_cart():
    """Create a new cart for the current session"""
    try:
        logger.debug("Starting create_cart function")
        # Generate a unique session ID if not exists
        if '_id' not in session:
            session['_id'] = os.urandom(16).hex()
            logger.debug(f"Generated new session ID: {session['_id']}")
        else:
            logger.debug(f"Using existing session ID: {session['_id']}")
        
        # Check if a cart already exists for this session
        existing_cart = Cart.query.filter_by(session_id=session['_id']).first()
        if existing_cart:
            logger.debug(f"Found existing cart with ID: {existing_cart.id} for session")
            session['cart_id'] = existing_cart.id
            session.modified = True
            return existing_cart
        
        # Create new cart
        cart = Cart(session_id=session['_id'])
        db.session.add(cart)
        try:
            db.session.commit()
            logger.debug(f"Successfully committed new cart with ID: {cart.id}")
        except Exception as e:
            logger.error(f"Error committing cart to database: {str(e)}")
            db.session.rollback()
            return None
        
        # Ensure cart was saved with an ID
        if not cart.id:
            logger.error("Cart was created but no ID was assigned")
            return None
            
        session['cart_id'] = cart.id
        # Make sure session is saved
        session.modified = True
        
        logger.info(f"Created new cart with ID: {cart.id}")
        
        # Add a test item to verify it works
        try:
            with with_menu_session() as menu_session:
                menu_items = menu_session.query(MenuItem).all()
                if menu_items:
                    test_item = menu_items[0]
                    cart_item = CartItem(
                        cart_id=cart.id,
                        item_type='menu_item',
                        item_id=test_item.id,
                        quantity=1
                    )
                    db.session.add(cart_item)
                    db.session.commit()
                    logger.debug(f"Added test item to cart: {test_item.name}")
        except Exception as e:
            logger.error(f"Error adding test item to cart: {str(e)}")
            # Continue even if test item fails
        
        return cart
    except Exception as e:
        logger.error(f"Error in create_cart: {str(e)}")
        db.session.rollback()
        return None

# Cleanup expired carts (run periodically)
def cleanup_expired_carts():
    """Remove expired carts from the database"""
    try:
        expiration_time = datetime.now(timezone.utc) - timedelta(seconds=app.config['PERMANENT_SESSION_LIFETIME'])
        expired_carts = Cart.query.filter(Cart.updated_at < expiration_time).all()
        
        for cart in expired_carts:
            db.session.delete(cart)
        
        if expired_carts:
            db.session.commit()
            logger.info(f"Cleaned up {len(expired_carts)} expired carts")
    except Exception as e:
        logger.error(f"Error cleaning up expired carts: {str(e)}")
        db.session.rollback()

# Context processors
@app.context_processor
def inject_cart():
    """Make cart information available to all templates"""
    def get_cart_count():
        cart = get_cart()
        if cart and cart.items:
            return sum(item.quantity for item in cart.items)
        return 0
    
    def get_current_cart():
        return get_cart()
    
    return dict(
        get_cart_count=get_cart_count,
        get_current_cart=get_current_cart
    )

# Main routes
@app.route('/')
@app.route('/index')
@handle_errors
def index():
    try:
        with with_menu_session() as menu_session:
            # Get all menu items for the index page
            popular_items = menu_session.query(MenuItem).all()
            return render_template('index.html', popular_items=popular_items)
    except Exception as e:
        logger.error(f"Error fetching popular items: {str(e)}")
        return render_template('index.html', popular_items=[])

@app.route('/menu')
def menu():
    try:
        with with_menu_session() as session:
            # Get all categories and menu items
            categories = session.query(Category).all()
            menu_items = session.query(MenuItem).all()
            
            # Group items by category
            menu_items_by_category = {}
            for category in categories:
                menu_items_by_category[category.name] = [
                    item for item in menu_items if item.category_id == category.id
                ]
            
            return render_template('menu.html', menu_items=menu_items_by_category)
    except Exception as e:
        app.logger.error(f"Error fetching menu items: {str(e)}")
        flash('Error loading menu items. Please try again later.', 'error')
        return redirect(url_for('index'))

@app.route('/dish/<int:dish_id>')
@handle_errors
def dish_detail(dish_id):
    try:
        with with_menu_session() as menu_session:
            dish = menu_session.query(MenuItem).get_or_404(dish_id)
            return render_template('dish_detail.html', dish=dish)
    except Exception as e:
        logger.error(f"Error fetching dish details: {str(e)}")
        flash('Error loading dish details. Please try again later.', 'error')
        return redirect(url_for('menu'))

# Cake routes
@app.route('/cakes')
@handle_errors
def cakes():
    """Display all cake flavors"""
    try:
        logger.info("Opening cake database session...")
        with with_cake_session() as cake_session:
            # Fetch all cake flavors
            logger.info("Fetching all cake flavors...")
            all_flavors = cake_session.query(CakeFlavor).all()
            logger.info(f"Found {len(all_flavors)} cake flavors")
        
        # Group flavors by category for display
        single_flavors = [f for f in all_flavors if f.category == 'Single']
        combination_flavors = [f for f in all_flavors if f.category == 'Combination']
        logger.info(f"Found {len(single_flavors)} single flavors and {len(combination_flavors)} combination flavors")
        
        return render_template('cakes.html', 
                             single_flavors=single_flavors,
                             combination_flavors=combination_flavors)
    except Exception as e:
        logger.error(f"Error fetching cake flavors: {str(e)}")
        flash('Error loading cake flavors. Please try again later.', 'error')
        return redirect(url_for('index'))

@app.route('/add-cake-to-cart', methods=['POST'])
@handle_errors
def add_cake_to_cart():
    """Handle cake order form submission and add to cart"""
    try:
        # Get form data
        flavor_id = request.form.get('flavor_id')
        size = request.form.get('size')
        message = request.form.get('message')
        quantity = int(request.form.get('quantity', 1))

        if not all([flavor_id, size]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('cake_order_form', flavor_id=flavor_id))

        # Get or create cart
        cart = get_cart()
        if not cart:
            cart = create_cart()
            if not cart:
                raise Exception("Failed to create cart")

        # Get cake flavor
        with with_cake_session() as cake_session:
            flavor = cake_session.query(CakeFlavor).get(flavor_id)
        
        if not flavor:
            flash('Selected cake flavor not found.', 'error')
            return redirect(url_for('cakes'))

        # Create cart item
        cart_item = CartItem(
            cart_id=cart.id,
            item_type='cake',
            item_id=flavor_id,
            quantity=quantity,
            size_kg=float(size),
            message=message
        )
        db.session.add(cart_item)
        db.session.commit()

        flash('Cake added to cart successfully!', 'success')
        return redirect(url_for('view_cart'))

    except Exception as e:
        logger.error(f"Error adding cake to cart: {str(e)}")
        flash('Error adding cake to cart. Please try again.', 'error')
        return redirect(url_for('cake_order_form', flavor_id=flavor_id))

@app.route('/submit-cake-order', methods=['POST'])
@handle_errors
def submit_cake_order():
    # Add cake to cart first
    flavor_id = int(request.form['flavor'])
    size_kg = float(request.form['size'])
    message = request.form['message']
    
    # Create cart and add cake
    cart = get_cart() or create_cart()
    if not cart:
        raise Exception("Failed to create cart")
        
    cart_item = CartItem(
        cart_id=cart.id,
        item_type='cake',
        item_id=flavor_id,
        quantity=1,
        size_kg=size_kg,
        message=message
    )
    db.session.add(cart_item)
    db.session.commit()
    
    # Redirect to checkout
    return redirect(url_for('checkout'))

@app.route('/cake-order-confirmation/<int:order_id>')
@handle_errors
def cake_order_confirmation(order_id):
    order = CakeOrder.query.get_or_404(order_id)
    return render_template('cake_order_confirmation.html', order=order)

# Cart routes
@app.route('/cart')
@handle_errors
def view_cart():
    try:
        logger.debug("Starting view_cart function")
        logger.debug(f"Current session ID: {session.get('_id', 'None')}")
        logger.debug(f"Current cart ID: {session.get('cart_id', 'None')}")
        
        cart = get_cart()
        
        if not cart:
            logger.debug("No cart found, creating a new one")
            cart = create_cart()
            
        if cart:
            logger.debug(f"Cart found with ID: {cart.id}, containing {len(cart.items)} items")
            
            # Force reload cart items from database to ensure we have the latest data
            db.session.refresh(cart)
            
            if not cart.items:
                logger.debug("Cart is empty")
                flash("Your cart is empty. Add some delicious items!", "info")
        else:
            logger.error("Failed to get or create cart")
            flash("There was an issue with your shopping cart. Please try again.", "error")
            
        return render_template('cart.html', cart=cart)
    except Exception as e:
        logger.error(f"Error in view_cart: {str(e)}")
        flash("There was an error loading your cart. Please try again.", "error")
        return render_template('cart.html', cart=None)

@app.route('/cart/add', methods=['POST'])
@handle_errors
def add_to_cart():
    try:
        logger.debug("Starting add_to_cart")
        logger.debug(f"Form data received: {request.form}")
        logger.debug(f"Current session ID: {session.get('_id', 'None')}")
        logger.debug(f"Current cart ID: {session.get('cart_id', 'None')}")
        
        # Get and validate form data
        item_type = request.form.get('item_type')
        item_id = request.form.get('item_id')
        quantity = int(request.form.get('quantity', 1))
        
        if not all([item_type, item_id]):
            logger.error("Missing required item information")
            flash('Missing required item information', 'error')
            return redirect(request.referrer or url_for('menu'))
        
        # Convert item_id to integer
        item_id = int(item_id)
        
        # Validate item exists in appropriate database
        if item_type == 'menu_item':
            with with_menu_session() as menu_session:
                item = menu_session.query(MenuItem).get(item_id)
                if not item:
                    logger.error(f"Menu item with ID {item_id} not found")
                    flash('Item not found', 'error')
                    return redirect(request.referrer or url_for('menu'))
        elif item_type == 'cake':
            with with_cake_session() as cake_session:
                item = cake_session.query(CakeFlavor).get(item_id)
                if not item:
                    logger.error(f"Cake flavor with ID {item_id} not found")
                    flash('Item not found', 'error')
                    return redirect(request.referrer or url_for('cakes'))
        else:
            logger.error(f"Invalid item type: {item_type}")
            flash('Invalid item type', 'error')
            return redirect(request.referrer or url_for('menu'))
        
        # Get or create cart
        cart = get_cart()
        if not cart:
            logger.debug("No existing cart found, creating new cart")
            cart = create_cart()
            
        if not cart:
            logger.error("Failed to create cart")
            flash('Failed to create cart. Please try again.', 'error')
            return redirect(request.referrer or url_for('menu'))
            
        logger.debug(f"Using cart with ID: {cart.id}")

        # For customized cakes, always create a new cart item
        is_customized = request.form.get('is_customized') == 'true'
        logger.debug(f"Is customized: {is_customized}")
        
        # Check if same item configuration exists in cart (only for non-customized items)
        existing_item = None if is_customized else CartItem.query.filter_by(
            cart_id=cart.id,
            item_type=item_type,
            item_id=item_id
        ).first()

        if existing_item and not is_customized:
            logger.debug(f"Found existing cart item with ID: {existing_item.id}")
            new_quantity = existing_item.quantity + quantity
            if new_quantity > 10:
                logger.warning(f"Quantity would exceed limit: {new_quantity}")
                flash('Maximum quantity per item is 10', 'error')
                return redirect(request.referrer or url_for('menu'))
            existing_item.quantity = new_quantity
            logger.debug(f"Updated existing item quantity to: {new_quantity}")
        else:
            logger.debug("Creating new cart item")
            cart_item = CartItem(
                cart_id=cart.id,
                item_type=item_type,
                item_id=item_id,
                quantity=min(quantity, 10)
            )
            
            # Add cake-specific attributes if applicable
            if item_type == 'cake':
                cart_item.size_kg = float(request.form.get('size_kg', 1))
                cart_item.message = request.form.get('message', '')
                if is_customized:
                    customization_details = request.form.get('customization_details')
                    logger.debug(f"Customization details: {customization_details}")
                    cart_item.customization_details = customization_details
            
            db.session.add(cart_item)
            logger.debug(f"Added new cart item with ID: {cart_item.id if cart_item.id else 'Not yet assigned'}")

        try:
            db.session.commit()
            logger.info(f"Successfully committed cart changes")
        except Exception as e:
            logger.error(f"Error committing cart changes: {str(e)}")
            db.session.rollback()
            flash('Error adding item to cart. Please try again.', 'error')
            return redirect(request.referrer or url_for('menu'))
            
        logger.info(f"Successfully added {item.name} to cart. Cart ID: {cart.id}")
        flash(f'{item.name} added to cart successfully!', 'success')
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'{item.name} added to cart successfully!'})
            
        return redirect(url_for('view_cart'))

    except ValueError as e:
        logger.error(f"ValueError in add_to_cart: {str(e)}")
        flash('Invalid input values. Please check your selections.', 'error')
        return redirect(request.referrer or url_for('menu'))
    except Exception as e:
        logger.error(f"Error in add_to_cart: {str(e)}")
        db.session.rollback()
        flash('Error adding item to cart. Please try again.', 'error')
        return redirect(request.referrer or url_for('menu'))

# The following route definition is a duplicate and will be removed
@app.route('/update-cart-item/<int:item_id>', methods=['POST'])
@handle_errors
def update_cart_item(item_id):
    try:
        # Get cart item
        cart_item = CartItem.query.get_or_404(item_id)
        
        # Verify cart belongs to current session
        cart = get_cart()
        if not cart or cart.id != cart_item.cart_id:
            flash('Invalid cart item', 'error')
            return redirect(url_for('view_cart'))
        
        # Get action from form
        action = request.form.get('action')
        
        if action == 'increase':
            if cart_item.quantity < 10:  # Maximum quantity limit
                cart_item.quantity += 1
                flash('Quantity increased', 'success')
            else:
                flash('Maximum quantity limit reached', 'error')
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                flash('Quantity decreased', 'success')
            else:
                # If quantity would go to 0, remove the item
                db.session.delete(cart_item)
                flash('Item removed from cart', 'success')
        
        db.session.commit()
        return redirect(url_for('view_cart'))
        
    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        flash('Error updating cart', 'error')
        return redirect(url_for('view_cart'))

@app.route('/remove-cart-item/<int:item_id>', methods=['POST', 'GET'])
@handle_errors
def remove_cart_item(item_id):
    try:
        # Get cart item
        cart_item = CartItem.query.get_or_404(item_id)
        
        # Get current cart
        cart = get_cart()
        if not cart or cart.id != cart_item.cart_id:
            flash('Invalid cart item', 'error')
            return redirect(url_for('view_cart'))
        
        # Delete the item
        db.session.delete(cart_item)
        db.session.commit()
        
        flash('Item removed from cart successfully', 'success')
        return redirect(url_for('view_cart'))
        
    except Exception as e:
        logger.error(f"Error removing cart item: {str(e)}")
        flash('Error removing item from cart', 'error')
        return redirect(url_for('view_cart'))

@app.route('/update-cart-item/<int:item_id>/customize', methods=['POST'])
@handle_errors
def update_cart_item_customization(item_id):
    try:
        cart = get_cart()
        if not cart:
            return {'success': False, 'message': 'Cart not found'}, 404
        
        item = CartItem.query.get(item_id)
        if not item or item.cart_id != cart.id:
            return {'success': False, 'message': 'Item not found'}, 404
        
        if item.item_type != 'cake':
            return {'success': False, 'message': 'Only cakes can be customized'}, 400

        # Update cake customization
        item.size_kg = float(request.form.get('size_kg', 1))
        item.customization_details = request.form.get('customization_details')
        
        db.session.commit()
        return {'success': True}
    except Exception as e:
        logger.error(f"Error updating cake customization: {str(e)}")
        return {'success': False, 'message': 'Error updating customization'}, 500

# Checkout routes
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    try:
        # For POST requests (form submission)
        if request.method == 'POST':
            # Create order record
            order = Order(
                customer_name=request.form.get('name', 'Guest'),
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                address=request.form.get('address', ''),
                city=request.form.get('city', ''),
                pincode=request.form.get('pincode', ''),
                delivery_instructions=request.form.get('instructions', ''),
                payment_method=request.form.get('payment_method', 'cash_on_delivery'),
                total_amount=float(request.form.get('total_amount', 0)),
                status='pending'
            )
            db.session.add(order)
            db.session.commit()
            
            # Clear the cart after order is placed
            session.pop('cart_id', None)
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_success'))

        # For GET requests
        # Create a simple cart with sample items if needed
        cart = get_cart()
        if not cart or not cart.items:
            # Create a sample cart with items for demonstration
            with with_menu_session() as menu_session:
                menu_items = menu_session.query(MenuItem).limit(2).all()
                if menu_items:
                    cart = create_cart()
                    for item in menu_items:
                        cart_item = CartItem(
                            cart_id=cart.id,
                            item_type='menu_item',
                            item_id=item.id,
                            quantity=1
                        )
                        db.session.add(cart_item)
                    db.session.commit()
        
        return render_template('checkout.html', cart=cart, stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'])
            
    except Exception as e:
        logger.error(f"Error in checkout: {str(e)}")
        flash('Unable to process checkout. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/order-success')
def order_success():
    cart = get_cart()
    if cart:
        # Ensure the cart is cleared after order confirmation
        session.pop('cart_id', None)

    return render_template('order_confirmation.html')

@app.route('/cake-order-form')
@handle_errors
def cake_order_form():
    """Display the cake order form"""
    try:
        # Get the selected flavor ID from URL parameters
        flavor_id = request.args.get('flavor_id')
        if not flavor_id:
            logger.warning("No flavor_id provided in URL parameters")
            flash('Please select a cake flavor first.', 'error')
            return redirect(url_for('cakes'))

        try:
            flavor_id = int(flavor_id)
        except ValueError:
            logger.error(f"Invalid flavor_id format: {flavor_id}")
            flash('Invalid cake flavor selection.', 'error')
            return redirect(url_for('cakes'))

        # Fetch the cake flavor from the database
        with with_cake_session() as cake_session:
            flavor = cake_session.query(CakeFlavor).get(flavor_id)
        
        if not flavor:
            logger.error(f"Cake flavor with ID {flavor_id} not found")
            flash('Selected cake flavor not found.', 'error')
            return redirect(url_for('cakes'))
        
        logger.info(f"Displaying order form for cake flavor: {flavor.name}")
        return render_template('cake_order_form.html', flavor=flavor)
        
    except Exception as e:
        logger.error(f"Error displaying cake order form: {str(e)}")
        flash('Error loading cake order form. Please try again later.', 'error')
        return redirect(url_for('cakes'))

# Add error page route
@app.route('/error')
def error_page():
    return render_template('error.html', error="An error occurred. Please try again.")

@app.template_filter('from_json')
def from_json_filter(value):
    """Convert a JSON string to Python object"""
    try:
        # Handle empty values
        if value is None:
            return {}
            
        # Handle already parsed values
        if isinstance(value, dict):
            return value
            
        # Handle string values
        if isinstance(value, str):
            if not value.strip():
                return {}
                
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON string: {value[:50]}... Error: {str(e)}")
                return {}
        
        # Handle other types
        logger.warning(f"Unexpected type for JSON conversion: {type(value)}")
        return {}
    except Exception as e:
        logger.error(f"Error in from_json filter: {str(e)}")
        return {}

# Initialize only the main database on startup
with app.app_context():
    try:
        if not os.path.exists('instance'):
            os.makedirs('instance')
        logger.info("Starting main database initialization...")
        init_db()
        logger.info("Main database initialization completed successfully")
        
        # Clean up expired carts on startup
        cleanup_expired_carts()
    except Exception as e:
        logger.error(f"Failed to initialize main database: {str(e)}")
        raise

# Add a before_request handler to periodically clean up expired carts
last_cleanup_time = datetime.now(timezone.utc)

@app.before_request
def periodic_cleanup():
    """Periodically clean up expired carts"""
    global last_cleanup_time
    current_time = datetime.now(timezone.utc)
    
    # Run cleanup every hour
    if (current_time - last_cleanup_time).total_seconds() > 3600:  # 1 hour
        try:
            with app.app_context():
                cleanup_expired_carts()
            last_cleanup_time = current_time
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {str(e)}")

# Debug routes
@app.route('/debug/cart')
def debug_cart():
    """Debug route to check cart status"""
    if not app.debug:
        return "Debug routes only available in debug mode", 403
        
    try:
        output = []
        output.append(f"Session ID: {session.get('_id', 'None')}")
        output.append(f"Cart ID in session: {session.get('cart_id', 'None')}")
        
        # Check if cart exists in database
        if 'cart_id' in session:
            cart = Cart.query.get(session['cart_id'])
            if cart:
                output.append(f"Cart found in database: ID={cart.id}, Session ID={cart.session_id}")
                output.append(f"Cart items count: {len(cart.items)}")
                
                # List cart items
                if cart.items:
                    output.append("Cart items:")
                    for i, item in enumerate(cart.items, 1):
                        item_obj = item.get_item()
                        item_name = item_obj.name if item_obj else "Unknown"
                        output.append(f"  {i}. {item_name} (Type: {item.item_type}, ID: {item.item_id}, Qty: {item.quantity})")
                else:
                    output.append("Cart is empty")
            else:
                output.append("Cart ID in session not found in database")
        else:
            output.append("No cart ID in session")
            
        # Check all carts in database
        all_carts = Cart.query.all()
        output.append(f"Total carts in database: {len(all_carts)}")
        
        return "<br>".join(output)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/debug/fix-cart')
def debug_fix_cart():
    """Debug route to fix cart issues"""
    try:
        # Clear existing cart session
        session.pop('cart_id', None)
        session.pop('_id', None)
        
        # Create new session ID
        session['_id'] = os.urandom(16).hex()
        session.modified = True
        
        # Create new cart
        cart = Cart(session_id=session['_id'])
        db.session.add(cart)
        db.session.commit()
        
        # Store cart ID in session
        session['cart_id'] = cart.id
        session.modified = True
        
        return redirect(url_for('view_cart'))
    except Exception as e:
        return f"Error fixing cart: {str(e)}"

@app.route('/debug/set-session')
def set_session():
    """Debug route to set session values"""
    try:
        # Set session values from fix_cart.py
        session['_id'] = '48c2efae62aa7b7ad6fbe0f6c0a2ed3e'
        session['cart_id'] = 5
        session.modified = True
        
        return f"""
        <h1>Session Set!</h1>
        <p>Session ID: {session.get('_id')}</p>
        <p>Cart ID: {session.get('cart_id')}</p>
        <p><a href="{url_for('view_cart')}">View Cart</a></p>
        <p><a href="{url_for('menu')}">Go to Menu</a></p>
        """
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/add-sample-item')
def add_sample_item():
    """Add a sample item to the cart for demonstration purposes"""
    try:
        # Get or create cart
        cart = get_cart()
        if not cart:
            cart = create_cart()
            if not cart:
                flash('Failed to create cart', 'error')
                return redirect(url_for('menu'))
        
        # Add a sample menu item
        with with_menu_session() as menu_session:
            menu_items = menu_session.query(MenuItem).limit(1).all()
            if menu_items:
                item = menu_items[0]
                cart_item = CartItem(
                    cart_id=cart.id,
                    item_type='menu_item',
                    item_id=item.id,
                    quantity=1
                )
                db.session.add(cart_item)
                db.session.commit()
                flash(f'Added {item.name} to your cart!', 'success')
            else:
                # Add a sample cake item
                with with_cake_session() as cake_session:
                    cakes = cake_session.query(CakeFlavor).limit(1).all()
                    if cakes:
                        cake = cakes[0]
                        cart_item = CartItem(
                            cart_id=cart.id,
                            item_type='cake',
                            item_id=cake.id,
                            quantity=1,
                            size_kg=1.0
                        )
                        db.session.add(cart_item)
                        db.session.commit()
                        flash(f'Added {cake.name} Cake to your cart!', 'success')
                    else:
                        flash('No sample items available', 'error')
        
        return redirect(url_for('view_cart'))
    except Exception as e:
        logger.error(f"Error adding sample item: {str(e)}")
        flash('Error adding sample item', 'error')
        return redirect(url_for('menu'))

@app.route('/debug/check-cart')
def debug_check_cart():
    """Debug route to check cart status"""
    try:
        output = []
        output.append(f"Session ID: {session.get('_id', 'None')}")
        output.append(f"Cart ID in session: {session.get('cart_id', 'None')}")
        
        # Check if cart exists in database
        cart = None
        if 'cart_id' in session:
            cart = Cart.query.get(session['cart_id'])
            
        if cart:
            output.append(f"Cart found in database:")
            output.append(f"- Cart ID: {cart.id}")
            output.append(f"- Session ID: {cart.session_id}")
            output.append(f"- Created at: {cart.created_at}")
            output.append(f"- Items count: {len(cart.items)}")
            
            # List cart items
            if cart.items:
                output.append("Cart items:")
                for item in cart.items:
                    output.append(f"- Item ID: {item.id}")
                    output.append(f"  Type: {item.item_type}")
                    output.append(f"  Quantity: {item.quantity}")
        else:
            output.append("No valid cart found")
            
        return "<br>".join(output)
    except Exception as e:
        return f"Error checking cart: {str(e)}"

# Print the URL when the application starts
if __name__ == '__main__':
    print("Visit the application at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
