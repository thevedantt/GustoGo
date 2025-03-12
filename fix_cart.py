from app import app, db
from models import Cart, CartItem, MenuItem, CakeFlavor
from models import with_menu_session, with_cake_session
import os

def fix_cart_database():
    with app.app_context():
        print("Fixing cart database...")
        
        # Clear all existing carts and cart items
        print("Clearing existing carts...")
        CartItem.query.delete()
        Cart.query.delete()
        db.session.commit()
        
        # Create a new cart
        print("Creating new cart...")
        session_id = os.urandom(16).hex()
        cart = Cart(session_id=session_id)
        db.session.add(cart)
        db.session.commit()
        
        # Add a test item to the cart
        print("Adding test item to cart...")
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
                print(f"Added test item: {test_item.name}")
        
        print(f"\nCart fixed successfully!")
        print(f"Cart ID: {cart.id}")
        print(f"Session ID: {session_id}")
        print(f"\nTo use this cart in your browser session, run the following commands in the Flask shell:")
        print(f"session['_id'] = '{session_id}'")
        print(f"session['cart_id'] = {cart.id}")
        print("session.modified = True")

if __name__ == "__main__":
    fix_cart_database() 