from app import app, db
from models import Cart, CartItem

with app.app_context():
    print('Total carts in database:', Cart.query.count())
    print('Cart items in database:', CartItem.query.count())
    
    for cart in Cart.query.all():
        print(f'Cart ID: {cart.id}, Session ID: {cart.session_id}, Items: {len(cart.items)}')
        
        for item in cart.items:
            print(f'  - Item ID: {item.id}, Type: {item.item_type}, Item ID: {item.item_id}, Quantity: {item.quantity}') 