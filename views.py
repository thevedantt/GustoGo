from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
import stripe
import json
from datetime import datetime

from extensions import db
from models import User, MenuItem, CartItem, Order, OrderItem, Coupon
from forms import LoginForm, RegistrationForm, ProfileForm, CakeCustomizationForm, CartUpdateForm, CheckoutForm
from config import MENU_CATEGORIES, CAKE_FLAVORS, CAKE_SIZES, CAKE_FROSTINGS, CAKE_TOPPINGS

# Create a Blueprint for our views
bp = Blueprint('main', __name__)

# Helper functions
def get_cart_items():
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).all()
    elif 'cart' in session:
        cart_items = []
        for item in session['cart']:
            cart_item = CartItem()
            cart_item.id = item.get('id')
            cart_item.quantity = item.get('quantity', 1)
            cart_item.item_type = item.get('item_type', 'menu')
            
            if item.get('menu_item_id'):
                cart_item.menu_item_id = item.get('menu_item_id')
                cart_item.menu_item = MenuItem.query.get(item.get('menu_item_id'))
            
            if item.get('cake_details'):
                cart_item.cake_details = json.dumps(item.get('cake_details'))
                # Add calculate_price method to cart_item
                cake_details = item.get('cake_details')
                cart_item.calculate_price = lambda: cake_details.get('total_price', 0) * cart_item.quantity
            else:
                # Define calculate_price for items without cake_details
                cart_item.calculate_price = lambda: cart_item.menu_item.price * cart_item.quantity if cart_item.menu_item else 0
            
            cart_items.append(cart_item)
        return cart_items
    return []

def calculate_cart_total(cart_items):
    return sum(item.calculate_price() for item in cart_items)

def merge_session_cart_with_db():
    if 'cart' in session and current_user.is_authenticated:
        session_cart = session.pop('cart')
        for item in session_cart:
            if item.get('item_type') == 'menu' and item.get('menu_item_id'):
                # Check if the same menu item already exists in the user's cart
                existing_item = CartItem.query.filter_by(
                    user_id=current_user.id,
                    menu_item_id=item.get('menu_item_id'),
                    item_type='menu'
                ).first()
                
                if existing_item:
                    existing_item.quantity += item.get('quantity', 1)
                else:
                    cart_item = CartItem(
                        user_id=current_user.id,
                        menu_item_id=item.get('menu_item_id'),
                        quantity=item.get('quantity', 1),
                        item_type='menu'
                    )
                    db.session.add(cart_item)
            
            elif item.get('item_type') == 'cake' and item.get('cake_details'):
                cart_item = CartItem(
                    user_id=current_user.id,
                    quantity=item.get('quantity', 1),
                    item_type='cake',
                    cake_details=json.dumps(item.get('cake_details'))
                )
                db.session.add(cart_item)
        
        db.session.commit()

# Routes
@bp.route('/')
def index():
    featured_items = MenuItem.query.filter_by(is_available=True).limit(6).all()
    return render_template('index.html', featured_items=featured_items)

@bp.route('/menu')
@bp.route('/menu/<category>')
def menu(category=None):
    if category and category not in [cat['id'] for cat in MENU_CATEGORIES]:
        return redirect(url_for('main.menu'))
    
    query = MenuItem.query.filter_by(is_available=True)
    
    if category:
        query = query.filter_by(category=category)
    
    menu_items = query.all()
    return render_template('menu.html', 
                          menu_items=menu_items, 
                          categories=MENU_CATEGORIES, 
                          current_category=category)

@bp.route('/cake', methods=['GET', 'POST'])
def cake():
    form = CakeCustomizationForm()
    
    if form.validate_on_submit():
        # Get the selected options
        flavor = next((f for f in CAKE_FLAVORS if f['id'] == form.flavor.data), None)
        size = next((s for s in CAKE_SIZES if s['id'] == form.size.data), None)
        frosting = next((f for f in CAKE_FROSTINGS if f['id'] == form.frosting.data), None)
        topping = next((t for t in CAKE_TOPPINGS if t['id'] == form.topping.data), None)
        
        # Calculate total price
        total_price = flavor['price'] + size['price'] + frosting['price'] + topping['price']
        
        # Create cake details dictionary
        cake_details = {
            'flavor': flavor,
            'size': size,
            'frosting': frosting,
            'topping': topping,
            'message': form.message.data,
            'total_price': total_price
        }
        
        # Add to cart
        if current_user.is_authenticated:
            cart_item = CartItem(
                user_id=current_user.id,
                quantity=form.quantity.data,
                item_type='cake',
                cake_details=json.dumps(cake_details)
            )
            db.session.add(cart_item)
            db.session.commit()
        else:
            if 'cart' not in session:
                session['cart'] = []
            
            session['cart'].append({
                'item_type': 'cake',
                'quantity': form.quantity.data,
                'cake_details': cake_details
            })
            session.modified = True
        
        flash('Cake added to cart successfully!', 'success')
        return redirect(url_for('main.cart'))
    
    return render_template('cake.html', 
                         form=form,
                         flavors=CAKE_FLAVORS,
                         sizes=CAKE_SIZES,
                         frostings=CAKE_FROSTINGS,
                         toppings=CAKE_TOPPINGS)

@bp.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if request.method == 'POST':
        if 'apply_coupon' in request.form:
            coupon_code = request.form.get('coupon_code', '').strip().upper()
            if not coupon_code:
                flash('Please enter a coupon code', 'error')
            else:
                # Check if the code matches any known coupon patterns
                valid_coupons = [
                    'WEEKEND20', 'MONDAYMAGIC', 'FLAT100', 'WEEKDAY10',
                    'FIRSTORDER', 'BIRTHDAY', 'FESTIVE50', 'LUNCHTIME',
                    'DINNER20', 'FLAT50'
                ]
                
                if coupon_code not in valid_coupons:
                    flash(f'"{coupon_code}" is not a valid coupon code. Try one of these: WEEKEND20, MONDAYMAGIC, FLAT100, WEEKDAY10, FIRSTORDER, BIRTHDAY, FESTIVE50, LUNCHTIME, DINNER20, FLAT50', 'error')
                else:
                    coupon = Coupon.query.filter_by(code=coupon_code).first()
                    if not coupon:
                        # Try to load the coupon from JSON if it doesn't exist in the database
                        try:
                            with open('data/coupons.json', 'r') as f:
                                data = json.load(f)
                                coupon_data = next((c for c in data['coupons'] if c['code'] == coupon_code), None)
                                if coupon_data:
                                    # Convert string dates to datetime objects
                                    coupon_data['valid_from'] = datetime.fromisoformat(coupon_data['valid_from'])
                                    coupon_data['valid_until'] = datetime.fromisoformat(coupon_data['valid_until'])
                                    
                                    # Create and save the coupon
                                    coupon = Coupon(**coupon_data)
                                    db.session.add(coupon)
                                    db.session.commit()
                                else:
                                    flash('This coupon is currently unavailable. Please try another one.', 'error')
                                    return redirect(url_for('main.cart'))
                        except Exception as e:
                            print(f"Error loading coupon: {e}")
                            flash('There was an error processing the coupon. Please try again later.', 'error')
                            return redirect(url_for('main.cart'))
                    
                    # Get cart total for validation
                    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
                    total = sum(item.calculate_price() for item in cart_items)
                    
                    # Validate coupon
                    is_valid, error_message = coupon.validate(total)
                    if is_valid:
                        session['applied_coupon'] = coupon.code
                        flash(f'Coupon applied successfully! {coupon.get_discount_description()}', 'success')
                    else:
                        flash(error_message, 'error')
        
        elif 'remove_coupon' in request.form:
            session.pop('applied_coupon', None)
            flash('Coupon removed', 'success')
    
    # Get cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.calculate_price() for item in cart_items)
    
    # Apply coupon if exists
    applied_coupon = None
    discount = 0
    if 'applied_coupon' in session:
        coupon = Coupon.query.filter_by(code=session['applied_coupon']).first()
        if coupon:
            is_valid, _ = coupon.validate(total)
            if is_valid:
                applied_coupon = coupon
                discount = coupon.calculate_discount(total)
            else:
                session.pop('applied_coupon', None)
    
    # Calculate final total
    delivery_fee = 40.00
    gst = (total - discount) * 0.18
    final_total = total - discount + delivery_fee + gst
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         total=total,
                         discount=discount,
                         delivery_fee=delivery_fee,
                         gst=gst,
                         final_total=final_total,
                         applied_coupon=applied_coupon)

@bp.route('/add-to-cart/<int:menu_item_id>', methods=['POST'])
def add_to_cart(menu_item_id):
    menu_item = MenuItem.query.get_or_404(menu_item_id)
    quantity = int(request.form.get('quantity', 1))
    
    if current_user.is_authenticated:
        # Check if item already exists in cart
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            menu_item_id=menu_item_id,
            item_type='menu'
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                user_id=current_user.id,
                menu_item_id=menu_item_id,
                quantity=quantity,
                item_type='menu'
            )
            db.session.add(cart_item)
        
        db.session.commit()
    else:
        if 'cart' not in session:
            session['cart'] = []
        
        # Check if item already exists in session cart
        for item in session['cart']:
            if item.get('menu_item_id') == menu_item_id and item.get('item_type') == 'menu':
                item['quantity'] += quantity
                break
        else:
            session['cart'].append({
                'menu_item_id': menu_item_id,
                'quantity': quantity,
                'item_type': 'menu'
            })
        
        session.modified = True
    
    flash(f'{menu_item.name} added to cart!', 'success')
    return redirect(url_for('main.menu'))

@bp.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id == current_user.id:
            db.session.delete(cart_item)
            db.session.commit()
    else:
        if 'cart' in session:
            session['cart'] = [item for item in session['cart'] if item.get('id') != item_id]
            session.modified = True
    
    flash('Item removed from cart!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()
    
    # Log form data for debugging
    if request.method == 'POST':
        current_app.logger.info(f"Form data: {request.form}")
        current_app.logger.info(f"Form validation: {form.validate()}")
        if not form.validate():
            current_app.logger.error(f"Form validation errors: {form.errors}")
            
            # Pre-fill form with submitted data to preserve user input
            form.first_name.data = request.form.get('first_name', '')
            form.last_name.data = request.form.get('last_name', '')
            form.email.data = request.form.get('email', '')
            form.phone.data = request.form.get('phone', '')
            form.address.data = request.form.get('address', '')
            form.payment_method.data = request.form.get('payment_method', 'card')
            form.upi_id.data = request.form.get('upi_id', '')
    
    if form.validate_on_submit():
        payment_method = form.payment_method.data
        shipping_address = form.address.data
        
        current_app.logger.info(f"Processing {payment_method} payment")
        current_app.logger.info(f"Shipping address: {shipping_address}")
        
        if payment_method == 'card':
            # Card payment logic remains the same
            payment_intent_id = request.form.get('payment_intent_id')
            if not payment_intent_id:
                current_app.logger.error("No payment_intent_id provided")
                flash('Payment information is missing. Please try again.', 'error')
                return redirect(url_for('main.checkout'))
            
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                current_app.logger.info(f"Retrieved payment intent: {intent.id} with status: {intent.status}")
                
                if intent.status == 'succeeded':
                    current_app.logger.info("Payment successful, creating order")
                    
                    order = Order(
                        user_id=current_user.id,
                        total_amount=calculate_cart_total(get_cart_items()),
                        payment_method='card',
                        payment_status='paid',
                        status='paid',
                        shipping_address=shipping_address,
                        payment_details=payment_intent_id
                    )
                    db.session.add(order)
                    current_app.logger.info(f"Created order with ID: {order.id}")
                    
                    # Add order items from cart
                    cart_items = get_cart_items()
                    current_app.logger.info(f"Found {len(cart_items)} cart items")
                    
                    for item in cart_items:
                        order_item = OrderItem(
                            order=order,
                            menu_item_id=item.menu_item_id,
                            quantity=item.quantity,
                            price=item.menu_item.price if item.menu_item else (json.loads(item.cake_details)['total_price'] if item.item_type == 'cake' else 0),
                            item_name=item.menu_item.name if item.menu_item else "Custom Cake",
                            item_type=item.item_type,
                            item_details=item.cake_details if item.item_type == 'cake' else None
                        )
                        db.session.add(order_item)
                        current_app.logger.info(f"Added order item: {order_item.item_name}")
                        
                        # Update product stock
                        if item.menu_item:
                            item.menu_item.stock -= item.quantity
                    
                    # Clear the cart
                    CartItem.query.filter_by(user_id=current_user.id).delete()
                    
                    # Commit the transaction before generating the URL
                    db.session.commit()
                    current_app.logger.info(f"Order committed to database with ID: {order.id}")
                    
                    confirmation_url = url_for('main.order_confirmation', order_id=order.id)
                    current_app.logger.info(f"Generated confirmation URL: {confirmation_url}")
                    
                    flash('Payment successful! Your order has been placed.', 'success')
                    return redirect(confirmation_url)
                else:
                    current_app.logger.error(f"Payment failed with status: {intent.status}")
                    flash('Payment failed. Please try again.', 'error')
                    return redirect(url_for('main.checkout'))
                    
            except stripe.error.StripeError as e:
                current_app.logger.error(f"Stripe error: {str(e)}")
                flash(f'Payment error: {str(e)}', 'error')
                return redirect(url_for('main.checkout'))
        
        elif payment_method == 'upi':
            current_app.logger.info("Processing UPI payment")
            upi_id = request.form.get('upi_id', '')  # Get UPI ID directly from form data
            current_app.logger.info(f"UPI ID: {upi_id}")
            
            # Create order even if UPI ID is empty
            order = Order(
                user_id=current_user.id,
                total_amount=calculate_cart_total(get_cart_items()),
                payment_method='upi',
                payment_status='pending',
                status='pending',
                shipping_address=shipping_address,
                payment_details=upi_id
            )
            db.session.add(order)
            current_app.logger.info(f"Created UPI order with ID: {order.id}")
            
            # Add order items from cart
            cart_items = get_cart_items()
            current_app.logger.info(f"Found {len(cart_items)} cart items")
            
            for item in cart_items:
                order_item = OrderItem(
                    order=order,
                    menu_item_id=item.menu_item_id,
                    quantity=item.quantity,
                    price=item.menu_item.price if item.menu_item else (json.loads(item.cake_details)['total_price'] if item.item_type == 'cake' else 0),
                    item_name=item.menu_item.name if item.menu_item else "Custom Cake",
                    item_type=item.item_type,
                    item_details=item.cake_details if item.item_type == 'cake' else None
                )
                db.session.add(order_item)
                current_app.logger.info(f"Added order item: {order_item.item_name}")
                
                # Update product stock
                if item.menu_item:
                    item.menu_item.stock -= item.quantity
            
            # Clear the cart
            CartItem.query.filter_by(user_id=current_user.id).delete()
            
            # Commit the transaction before generating the URL
            db.session.commit()
            current_app.logger.info(f"UPI order committed to database with ID: {order.id}")
            
            confirmation_url = url_for('main.order_confirmation', order_id=order.id)
            current_app.logger.info(f"Generated confirmation URL: {confirmation_url}")
            
            flash('Order placed successfully! Please complete the UPI payment.', 'success')
            return redirect(confirmation_url)
        
        elif payment_method == 'cod':
            current_app.logger.info("Processing Cash on Delivery order")
            
            order = Order(
                user_id=current_user.id,
                total_amount=calculate_cart_total(get_cart_items()),
                payment_method='cod',
                payment_status='pending',
                status='pending',
                shipping_address=shipping_address
            )
            db.session.add(order)
            current_app.logger.info(f"Created COD order with ID: {order.id}")
            
            # Add order items from cart
            cart_items = get_cart_items()
            current_app.logger.info(f"Found {len(cart_items)} cart items")
            
            for item in cart_items:
                order_item = OrderItem(
                    order=order,
                    menu_item_id=item.menu_item_id,
                    quantity=item.quantity,
                    price=item.menu_item.price if item.menu_item else (json.loads(item.cake_details)['total_price'] if item.item_type == 'cake' else 0),
                    item_name=item.menu_item.name if item.menu_item else "Custom Cake",
                    item_type=item.item_type,
                    item_details=item.cake_details if item.item_type == 'cake' else None
                )
                db.session.add(order_item)
                current_app.logger.info(f"Added order item: {order_item.item_name}")
                
                # Update product stock
                if item.menu_item:
                    item.menu_item.stock -= item.quantity
            
            # Clear the cart
            CartItem.query.filter_by(user_id=current_user.id).delete()
            
            # Commit the transaction before generating the URL
            db.session.commit()
            current_app.logger.info(f"COD order committed to database with ID: {order.id}")
            
            confirmation_url = url_for('main.order_confirmation', order_id=order.id)
            current_app.logger.info(f"Generated confirmation URL: {confirmation_url}")
            
            flash('Order placed successfully! You will pay upon delivery.', 'success')
            return redirect(confirmation_url)
    else:
        # If form validation failed, log the errors
        if request.method == 'POST':
            current_app.logger.error(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'error')
    
    # GET request - show checkout page
    cart_items = get_cart_items()
    if not cart_items:
        current_app.logger.warning("Attempted to access checkout with empty cart")
        flash('Your cart is empty!', 'error')
        return redirect(url_for('main.cart'))
        
    # Create a PaymentIntent for the card payment
    client_secret = None
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(calculate_cart_total(cart_items) * 100),  # Convert to cents
            currency='inr',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        client_secret = intent.client_secret
        current_app.logger.info(f"Created payment intent with ID: {intent.id}")
        
        # Create a pending order for card payments
        order = Order(
            user_id=current_user.id,
            total_amount=calculate_cart_total(cart_items),
            payment_method='card',
            payment_status='pending',
            status='pending',
            shipping_address='',  # Will be updated after payment
            payment_details=intent.id
        )
        db.session.add(order)
        current_app.logger.info(f"Created pending order with ID: {order.id}")
        
        # Add order items from cart
        for item in cart_items:
            order_item = OrderItem(
                order=order,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                price=item.menu_item.price if item.menu_item else (json.loads(item.cake_details)['total_price'] if item.item_type == 'cake' else 0),
                item_name=item.menu_item.name if item.menu_item else "Custom Cake",
                item_type=item.item_type,
                item_details=item.cake_details if item.item_type == 'cake' else None
            )
            db.session.add(order_item)
            current_app.logger.info(f"Added order item: {order_item.item_name}")
        
        db.session.commit()
        current_app.logger.info(f"Committed pending order with ID: {order.id}")
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Error creating payment intent: {str(e)}")
        flash(f'Error setting up payment: {str(e)}', 'error')
        return redirect(url_for('main.cart'))
    
    # Calculate totals
    subtotal = calculate_cart_total(cart_items)
    delivery_fee = 40.00
    gst = subtotal * 0.18
    total = subtotal + delivery_fee + gst
        
    return render_template('checkout.html',
                         form=form,
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_fee=delivery_fee,
                         gst=gst,
                         total=total,
                         stripe_public_key=current_app.config['STRIPE_PUBLIC_KEY'],
                         client_secret=client_secret)

@bp.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    current_app.logger.info(f"Accessing order confirmation for order ID: {order_id}")
    
    # Special case for Stripe payment confirmation
    if order_id == 0:
        # Get the payment intent ID from the session or query parameters
        payment_intent_id = request.args.get('payment_intent')
        current_app.logger.info(f"Payment intent ID from URL: {payment_intent_id}")
        
        if not payment_intent_id:
            current_app.logger.error("No payment_intent provided in the URL")
            flash('Payment information is missing. Please try again.', 'error')
            return redirect(url_for('main.checkout'))
        
        try:
            # Retrieve the payment intent
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            current_app.logger.info(f"Retrieved payment intent: {intent.id} with status: {intent.status}")
            
            if intent.status == 'succeeded':
                # Find the most recent order for this user
                order = Order.query.filter_by(
                    user_id=current_user.id,
                    payment_method='card',
                    payment_status='pending'
                ).order_by(Order.created_at.desc()).first()
                
                if order:
                    # Update the order status
                    order.payment_status = 'paid'
                    order.status = 'paid'
                    order.payment_details = payment_intent_id
                    db.session.commit()
                    current_app.logger.info(f"Updated order {order.id} to paid status")
                    
                    # Clear the cart after successful payment
                    CartItem.query.filter_by(user_id=current_user.id).delete()
                    db.session.commit()
                    current_app.logger.info("Cart cleared after successful payment")
                    
                    # Redirect to the actual order confirmation page
                    return redirect(url_for('main.order_confirmation', order_id=order.id))
                else:
                    current_app.logger.error(f"No pending order found for user {current_user.id}")
                    flash('Order not found. Please contact support.', 'error')
                    return redirect(url_for('main.profile'))
            else:
                current_app.logger.error(f"Payment failed with status: {intent.status}")
                flash('Payment failed. Please try again.', 'error')
                return redirect(url_for('main.checkout'))
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            flash(f'Payment error: {str(e)}', 'error')
            return redirect(url_for('main.checkout'))
    
    # Normal order confirmation flow
    order = Order.query.get_or_404(order_id)
    current_app.logger.info(f"Found order: {order.id} with status: {order.status}")
    
    # Ensure the user can only view their own orders
    if order.user_id != current_user.id:
        current_app.logger.warning(f"User {current_user.id} attempted to access order {order_id} belonging to user {order.user_id}")
        flash('You do not have permission to view this order.', 'error')
        return redirect(url_for('main.profile'))
    
    # Get order items
    order_items = order.get_order_items()
    current_app.logger.info(f"Found {len(order_items)} items for order {order_id}")
    
    return render_template('order_confirmation.html', 
                         order=order,
                         order_items=order_items)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            merge_session_cart_with_db()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Split username into first_name and last_name
        name_parts = form.username.data.strip().split()
        first_name = name_parts[0] if name_parts else form.username.data
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            first_name=first_name,
            last_name=last_name,
            address=''  # Initialize with empty string instead of None
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip() or current_user.username
        current_user.last_name = form.last_name.data.strip() or ''
        current_user.email = form.email.data.strip()
        current_user.phone = form.phone.data.strip()
        current_user.address = form.address.data.strip() or ''
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name or current_user.username
        form.last_name.data = current_user.last_name or ''
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.address.data = current_user.address or ''
    
    # Get user's order history
    orders = current_user.get_order_history()
    
    return render_template('profile.html', form=form, orders=orders)

@bp.route('/update-quantity/<int:item_id>/<action>')
@login_required
def update_quantity(item_id, action):
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id == current_user.id:
            if action == 'increase':
                cart_item.quantity += 1
            elif action == 'decrease' and cart_item.quantity > 1:
                cart_item.quantity -= 1
            db.session.commit()
            flash('Cart updated successfully!', 'success')
    else:
        if 'cart' in session:
            for item in session['cart']:
                if item.get('id') == item_id:
                    if action == 'increase':
                        item['quantity'] += 1
                    elif action == 'decrease' and item.get('quantity', 1) > 1:
                        item['quantity'] -= 1
                    break
            session.modified = True
            flash('Cart updated successfully!', 'success')
    
    return redirect(url_for('main.cart'))

@bp.route('/debug/order/<int:order_id>')
@login_required
def debug_order(order_id):
    order = Order.query.get_or_404(order_id)
    order_items = order.get_order_items()
    
    return jsonify({
        'order_id': order.id,
        'user_id': order.user_id,
        'total_amount': order.total_amount,
        'status': order.status,
        'payment_status': order.payment_status,
        'payment_method': order.payment_method,
        'shipping_address': order.shipping_address,
        'created_at': order.created_at.isoformat(),
        'items': [{
            'id': item.id,
            'item_name': item.item_name,
            'quantity': item.quantity,
            'price': item.price,
            'item_type': item.item_type,
            'item_details': item.item_details
        } for item in order_items]
    }) 