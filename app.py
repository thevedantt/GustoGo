import os
import logging
import json
from datetime import datetime

from flask import Flask, request, render_template, flash, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import stripe
from flask_login import LoginManager, login_required, current_user

from extensions import db, login_manager, migrate
from models import init_db, Coupon, User, MenuItem, CartItem, Order, OrderItem
from views import bp

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Load configuration
app.config.from_pyfile('config.py')

# Add fromjson filter to Jinja2 environment
@app.template_filter('fromjson')
def fromjson_filter(value):
    return json.loads(value)

# Test route for static files
@app.route('/test-image')
def test_image():
    return app.send_static_file('images/garlicbread.jpg')

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'main.login'
migrate.init_app(app, db)

# Setup Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_key')
logging.debug(f"Stripe Secret Key: {'*' * 10}{stripe.api_key[-4:] if stripe.api_key else 'Not set'}")
logging.debug(f"Stripe Public Key: {'*' * 10}{os.environ.get('STRIPE_PUBLIC_KEY', 'Not set')[-4:] if os.environ.get('STRIPE_PUBLIC_KEY') else 'Not set'}")

# Register the blueprints
app.register_blueprint(bp)

def load_coupons():
    try:
        with open('data/coupons.json', 'r') as f:
            data = json.load(f)
            for coupon_data in data['coupons']:
                # Remove date-related fields if they exist
                coupon_data.pop('valid_from', None)
                coupon_data.pop('valid_until', None)
                
                # Check if coupon already exists
                existing_coupon = Coupon.query.filter_by(code=coupon_data['code']).first()
                if not existing_coupon:
                    coupon = Coupon(**coupon_data)
                    db.session.add(coupon)
            db.session.commit()
            print("Coupons loaded successfully!")
    except Exception as e:
        print(f"Error loading coupons: {e}")

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'update':
            item_id = request.form.get('item_id')
            
            if current_user.is_authenticated:
                cart_item = CartItem.query.get_or_404(item_id)
                if cart_item.user_id == current_user.id:
                    if 'increase' in request.form:
                        cart_item.quantity += 1
                    elif 'decrease' in request.form and cart_item.quantity > 1:
                        cart_item.quantity -= 1
                    db.session.commit()
                    flash('Cart updated successfully!', 'success')
            else:
                if 'cart' in session:
                    for item in session['cart']:
                        if item.get('id') == item_id:
                            if 'increase' in request.form:
                                item['quantity'] += 1
                            elif 'decrease' in request.form and item.get('quantity', 1) > 1:
                                item['quantity'] -= 1
                            break
                    session.modified = True
                    flash('Cart updated successfully!', 'success')
            
            return redirect(url_for('main.cart'))
        
        elif 'apply_coupon' in request.form:
            coupon_code = request.form.get('coupon_code')
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            
            if not coupon:
                flash('Invalid coupon code', 'error')
            elif not coupon.is_valid():
                flash('Coupon is not valid or has expired', 'error')
            else:
                session['applied_coupon'] = coupon.code
                flash('Coupon applied successfully!', 'success')
        
        elif 'remove_coupon' in request.form:
            session.pop('applied_coupon', None)
            flash('Coupon removed', 'success')
    
    # Calculate cart total
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Apply coupon if exists
    applied_coupon = None
    discount = 0
    if 'applied_coupon' in session:
        coupon = Coupon.query.filter_by(code=session['applied_coupon']).first()
        if coupon and coupon.is_valid():
            applied_coupon = coupon
            discount = coupon.calculate_discount(total)
    
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

@app.route('/update-quantity/<int:item_id>/<action>')
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

with app.app_context():
    # Import models and create tables
    import models
    db.create_all()
    
    # Initialize the database with sample data
    init_db()
    
    # Load coupons
    load_coupons()
    
    # Setup user loader for flask-login
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
