document.addEventListener('DOMContentLoaded', function() {
    // Toggle mobile navigation
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('show');
        });
    }
    
    // Add scroll effect to navbar
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Add to cart animation
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.add('added');
            
            setTimeout(() => {
                this.classList.remove('added');
            }, 1500);
        });
    });

    // Prevent adding items to cart when navigating home
    const homeLinks = document.querySelectorAll('a[href="/"], a[href="/index"]');
    
    homeLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const cartItems = document.querySelectorAll('.cart-item'); // Adjust selector as needed
            if (cartItems.length > 0) {
                const confirmLeave = confirm("You have items in your cart. Are you sure you want to leave?");
                if (!confirmLeave) {
                    e.preventDefault(); // Prevent navigation
                }
            }
        });
    });

    // Stripe Payment Logic
    const stripe = Stripe('{{ stripe_publishable_key }}'); // Use the publishable key from the server
    const elements = stripe.elements();
    const cardElement = elements.create('card');
    cardElement.mount('#card-element');

    const form = document.getElementById('payment-form');
    form.addEventListener('submit', function(event) {
        event.preventDefault();

        stripe.createToken(cardElement).then(function(result) {
            if (result.error) {
                // Show error in #card-errors
                const errorElement = document.getElementById('card-errors');
                errorElement.textContent = result.error.message;
            } else {
                // Send the token to your server
                const hiddenInput = document.createElement('input');
                hiddenInput.setAttribute('type', 'hidden');
                hiddenInput.setAttribute('name', 'stripeToken');
                hiddenInput.setAttribute('value', result.token.id);
                form.appendChild(hiddenInput);

                // Submit the form
                form.submit();
            }
        });
    });
});
