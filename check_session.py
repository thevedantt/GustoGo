from app import app, db
from models import Cart, CartItem
from flask import session
import os

def create_test_cart():
    with app.app_context():
        # Generate a unique session ID
        session_id = os.urandom(16).hex()
        print(f"Generated session ID: {session_id}")
        
        # Create a new cart
        cart = Cart(session_id=session_id)
        db.session.add(cart)
        db.session.commit()
        
        print(f"Created new cart with ID: {cart.id}")
        
        # Add a test item to the cart
        cart_item = CartItem(
            cart_id=cart.id,
            item_type='menu_item',
            item_id=1,
            quantity=1
        )
        db.session.add(cart_item)
        db.session.commit()
        
        print(f"Added test item to cart with ID: {cart_item.id}")
        
        return cart.id, session_id

if __name__ == "__main__":
    cart_id, session_id = create_test_cart()
    print("\nTo use this cart in your browser session, run the following commands in the Flask shell:")
    print(f"session['_id'] = '{session_id}'")
    print(f"session['cart_id'] = {cart_id}")
    print("session.modified = True") 