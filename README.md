# GustoGo - Food Delivery Application

GustoGo is a modern food delivery web application built with Flask, featuring a user-friendly interface for ordering food, customizing cakes, and managing orders.

## 🌟 Unique Features

### 🎂 Advanced Cake Customization
- **Complete Cake Builder**: Design your perfect cake from scratch
- **Multiple Customization Options**:
  - Flavors: Chocolate, Vanilla, Red Velvet, and more
  - Sizes: Various sizes to suit any occasion
  - Frostings: Buttercream, Cream Cheese, Fondant options
  - Toppings: Fresh Fruits, Sprinkles, Chocolate Chips
  - Custom Messages: Add personalized messages to your cake
- **Real-time Price Calculation**: See the price update as you customize
- **Visual Preview**: Get a preview of your customized cake

### 🎟️ Smart Coupon System
- **Flexible Coupon Types**:
  - Percentage discounts (e.g., 20% off)
  - Fixed amount discounts (e.g., ₹100 off)
  - Minimum order value requirements
  - Maximum discount limits
- **Usage Controls**:
  - Set usage limits per coupon
  - Track number of times used
  - Applicable on specific days
- **Automatic Validation**:
  - Real-time coupon validation
  - Clear error messages for invalid coupons
  - Automatic discount calculation

## Core Features

- 🍽️ **Menu Browsing**: Browse through various food categories and items
- 🛒 **Shopping Cart**: Add items to cart and manage quantities
- 💳 **Multiple Payment Options**: 
  - Credit/Debit Card (Stripe)
  - UPI Payment
  - Cash on Delivery
- 👤 **User Profiles**: Save delivery information and view order history
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite (with Flask-SQLAlchemy)
- **Authentication**: Flask-Login
- **Payment Processing**: Stripe
- **Frontend**: HTML5, CSS3, JavaScript
- **Templates**: Jinja2
- **Database Migrations**: Flask-Migrate

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/thevedantt/GustoGo.git
cd GustoGo
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key
SESSION_SECRET=your_session_secret
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure

```
gustogo/
├── app.py              # Main application file
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions initialization
├── forms.py            # WTForms definitions
├── models.py           # Database models
├── views.py            # Route handlers
├── data/
│   └── coupons.json    # Coupon data
├── static/
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Image assets
├── templates/          # HTML templates
├── migrations/         # Database migrations
└── certs/             # SSL certificates
```

## Features in Detail

### 🎂 Cake Customization System
- **Interactive Cake Builder**: A step-by-step interface for designing custom cakes
- **Comprehensive Options**:
  - **Flavors**: Choose from premium flavors like Chocolate, Vanilla, Red Velvet, and more
  - **Sizes**: Select from multiple size options to suit any gathering
  - **Frostings**: Premium frosting options including Buttercream, Cream Cheese, and Fondant
  - **Toppings**: Add fresh fruits, sprinkles, chocolate chips, and more
  - **Personalization**: Add custom messages and special instructions
- **Real-time Updates**:
  - Live price calculation as you customize
  - Visual preview of your cake design
  - Instant availability checking
- **Order Management**:
  - Save favorite cake designs
  - Reorder previous designs
  - Schedule cake orders in advance

### 🎟️ Intelligent Coupon Management
- **Diverse Coupon Types**:
  - Percentage-based discounts (e.g., "WEEKEND20" for 20% off)
  - Fixed amount discounts (e.g., "FLAT100" for ₹100 off)
  - Special occasion coupons (e.g., "BIRTHDAY" for birthday discounts)
  - Time-specific offers (e.g., "LUNCHTIME" for lunch discounts)
- **Advanced Validation Rules**:
  - Minimum order value requirements
  - Maximum discount limits
  - Day-specific validity
  - Usage count tracking
- **User Experience**:
  - Real-time validation feedback
  - Clear error messages
  - Automatic discount application
  - Multiple coupon support
  - Coupon history tracking

### 🍽️ Menu System
- Browse food items by category
- View item details and prices
- Add items to cart

### 🛒 Shopping Cart
- Add/remove items
- Update quantities
- Apply coupon codes
- View order summary

### 💳 Payment Processing
- Secure card payments via Stripe
- UPI payment integration
- Cash on Delivery option
- Order confirmation emails

### 👤 User Management
- User registration and login
- Profile management
- Order history
- Saved delivery addresses

## Security Features

- Password hashing
- CSRF protection
- Secure session management
- HTTPS support
- Input validation
- SQL injection prevention

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask framework
- Stripe for payment processing
- Font Awesome for icons
- Bootstrap for UI components

## Support

For support, email support@gustogo.com or create an issue in the repository.