/**
 * GustoGo Food Ordering Platform
 * Main JavaScript file
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Navbar behavior - change background on scroll
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Quantity controls for menu items
    setupQuantityControls();

    // Handle special image error cases by replacing with SVG placeholder
    handleImageErrors();

    // Setup cake customization preview if on the cake page
    setupCakeCustomization();

    // Initialize any carousels
    initCarousels();
});

/**
 * Sets up quantity control buttons (+/-) for item quantities
 */
function setupQuantityControls() {
    // Get all quantity control buttons
    const minusButtons = document.querySelectorAll('.quantity-btn.minus');
    const plusButtons = document.querySelectorAll('.quantity-btn.plus');

    // Add event listeners to minus buttons
    minusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentNode.querySelector('.quantity-input');
            let value = parseInt(input.value);
            if (value > parseInt(input.min || 1)) {
                input.value = value - 1;
                // Trigger change event for any listeners
                input.dispatchEvent(new Event('change'));
            }
        });
    });

    // Add event listeners to plus buttons
    plusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentNode.querySelector('.quantity-input');
            let value = parseInt(input.value);
            const max = parseInt(input.max || 10);
            if (value < max) {
                input.value = value + 1;
                // Trigger change event for any listeners
                input.dispatchEvent(new Event('change'));
            }
        });
    });
}

/**
 * Handles image loading errors by replacing with SVG placeholders
 */
function handleImageErrors() {
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            // Check if this is a menu item image
            if (img.src.includes('menu')) {
                img.src = '/static/images/menu/placeholder.svg';
            } 
            // Check if this is a cake image
            else if (img.src.includes('cake')) {
                img.src = '/static/images/cakes/placeholder.svg';
            }
            // For any other image, use a general placeholder
            else {
                img.src = '/static/images/placeholder.svg';
            }
        });
    });
}

/**
 * Sets up cake customization preview on the cake page
 */
function setupCakeCustomization() {
    // Check if we're on the cake page
    const cakeSvg = document.getElementById('cake-svg');
    if (!cakeSvg) return;

    // Flavor change handlers
    const flavorInputs = document.querySelectorAll('input[name="flavor"]');
    flavorInputs.forEach(input => {
        input.addEventListener('change', updateCakePreview);
    });

    // Size change handlers
    const sizeInputs = document.querySelectorAll('input[name="size"]');
    sizeInputs.forEach(input => {
        input.addEventListener('change', updateCakePreview);
    });

    // Frosting change handlers
    const frostingInputs = document.querySelectorAll('input[name="frosting"]');
    frostingInputs.forEach(input => {
        input.addEventListener('change', updateCakePreview);
    });

    // Topping change handlers
    const toppingInputs = document.querySelectorAll('input[name="topping"]');
    toppingInputs.forEach(input => {
        input.addEventListener('change', updateCakePreview);
    });

    // Message change handler
    const messageInput = document.getElementById('message');
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            const messageElement = document.getElementById('cake-message');
            if (messageElement) {
                messageElement.textContent = this.value.slice(0, 100);
            }
        });
    }

    // Initial update
    updateCakePreview();
}

/**
 * Updates the cake preview SVG based on the selected options
 */
function updateCakePreview() {
    // Get selected options
    const selectedFlavor = document.querySelector('input[name="flavor"]:checked');
    const selectedSize = document.querySelector('input[name="size"]:checked');
    const selectedFrosting = document.querySelector('input[name="frosting"]:checked');
    const selectedTopping = document.querySelector('input[name="topping"]:checked');
    
    if (!selectedFlavor || !selectedSize || !selectedFrosting || !selectedTopping) return;
    
    // Get SVG elements
    const cakeBottom = document.getElementById('cake-bottom');
    const cakeTop = document.getElementById('cake-top');
    const cakeFrosting = document.getElementById('cake-frosting');
    const cakeLayers = document.getElementById('cake-layers');
    const toppingContainer = document.getElementById('cake-topping');
    
    if (!cakeBottom || !cakeTop || !cakeFrosting || !cakeLayers || !toppingContainer) return;
    
    // Update cake flavor (color)
    let cakeColor;
    switch (selectedFlavor.value) {
        case 'vanilla':
            cakeColor = '#f8e8c4';
            break;
        case 'chocolate':
            cakeColor = '#5c3a21';
            break;
        case 'strawberry':
            cakeColor = '#ffcdd2';
            break;
        case 'red-velvet':
            cakeColor = '#b71c1c';
            break;
        default:
            cakeColor = '#f8e8c4';
    }
    
    cakeBottom.setAttribute('fill', cakeColor);
    cakeTop.setAttribute('fill', cakeColor);
    
    // Update cake size
    let scale;
    switch (selectedSize.value) {
        case 'small':
            scale = 1.0;
            break;
        case 'medium':
            scale = 1.2;
            break;
        case 'large':
            scale = 1.4;
            break;
        default:
            scale = 1.0;
    }
    
    cakeLayers.setAttribute('transform', `scale(${scale}) translate(${(1-scale)*200}, ${(1-scale)*250})`);
    
    // Update frosting color
    let frostingColor;
    switch (selectedFrosting.value) {
        case 'buttercream':
            frostingColor = '#fff9e6';
            break;
        case 'cream-cheese':
            frostingColor = '#f5f5f5';
            break;
        case 'fondant':
            frostingColor = '#ffecb3';
            break;
        default:
            frostingColor = '#fff9e6';
    }
    
    cakeFrosting.setAttribute('fill', frostingColor);
    
    // Update topping
    // Clear previous toppings
    while (toppingContainer.firstChild) {
        toppingContainer.removeChild(toppingContainer.firstChild);
    }
    
    // Add selected topping
    switch (selectedTopping.value) {
        case 'sprinkles':
            for (let i = 0; i < 30; i++) {
                const sprinkle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                sprinkle.setAttribute('cx', 140 + Math.random() * 120);
                sprinkle.setAttribute('cy', 190 + Math.random() * 20);
                sprinkle.setAttribute('r', 2 + Math.random() * 2);
                sprinkle.setAttribute('fill', ['#ff6b6b', '#48dbfb', '#1dd1a1', '#feca57', '#ff9ff3'][Math.floor(Math.random() * 5)]);
                toppingContainer.appendChild(sprinkle);
            }
            break;
        case 'fruit':
            const fruits = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f'];
            for (let i = 0; i < 8; i++) {
                const fruit = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                fruit.setAttribute('cx', 160 + (i * 10) + Math.random() * 10);
                fruit.setAttribute('cy', 185 + Math.random() * 10);
                fruit.setAttribute('r', 5 + Math.random() * 3);
                fruit.setAttribute('fill', fruits[Math.floor(Math.random() * fruits.length)]);
                toppingContainer.appendChild(fruit);
            }
            break;
        case 'chocolate-chips':
            for (let i = 0; i < 15; i++) {
                const chip = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                chip.setAttribute('cx', 160 + Math.random() * 80);
                chip.setAttribute('cy', 185 + Math.random() * 15);
                chip.setAttribute('r', 3 + Math.random() * 2);
                chip.setAttribute('fill', '#3d240b');
                toppingContainer.appendChild(chip);
            }
            break;
        case 'nuts':
            for (let i = 0; i < 12; i++) {
                const nut = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
                nut.setAttribute('cx', 160 + Math.random() * 80);
                nut.setAttribute('cy', 185 + Math.random() * 15);
                nut.setAttribute('rx', 4 + Math.random() * 2);
                nut.setAttribute('ry', 2 + Math.random() * 1);
                nut.setAttribute('fill', '#c68642');
                nut.setAttribute('transform', `rotate(${Math.random() * 360} ${parseFloat(nut.getAttribute('cx'))} ${parseFloat(nut.getAttribute('cy'))})`);
                toppingContainer.appendChild(nut);
            }
            break;
        case 'none':
        default:
            // No topping
            break;
    }
    
    // Update price information
    updatePricePreview(selectedFlavor, selectedSize, selectedFrosting, selectedTopping);
}

/**
 * Updates the price breakdown preview
 */
function updatePricePreview(flavor, size, frosting, topping) {
    const basePrice = parseFloat(flavor.dataset.price || 0);
    const sizePrice = parseFloat(size.dataset.price || 0);
    const frostingPrice = parseFloat(frosting.dataset.price || 0);
    const toppingPrice = parseFloat(topping.dataset.price || 0);
    const totalPrice = basePrice + sizePrice + frostingPrice + toppingPrice;
    
    // Update price display
    document.getElementById('flavor-name').textContent = flavor.dataset.name;
    document.getElementById('size-name').textContent = size.dataset.name;
    document.getElementById('frosting-name').textContent = frosting.dataset.name;
    document.getElementById('topping-name').textContent = topping.dataset.name;
    
    document.getElementById('base-price').textContent = basePrice.toFixed(2);
    document.getElementById('size-price').textContent = sizePrice.toFixed(2);
    document.getElementById('frosting-price').textContent = frostingPrice.toFixed(2);
    document.getElementById('topping-price').textContent = toppingPrice.toFixed(2);
    document.getElementById('total-price').textContent = totalPrice.toFixed(2);
}

/**
 * Initializes any Bootstrap carousels on the page
 */
function initCarousels() {
    var carouselElements = document.querySelectorAll('.carousel');
    carouselElements.forEach(function(carousel) {
        new bootstrap.Carousel(carousel, {
            interval: 5000,
            wrap: true
        });
    });
}

/**
 * Updates the cart count in the navbar
 * @param {number} count - New cart count
 */
function updateCartCount(count) {
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
    }
}

/**
 * Validates a form by checking required fields
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateForm(form) {
    let isValid = true;
    
    // Check all required inputs
    const requiredInputs = form.querySelectorAll('[required]');
    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Formats a number as a currency string
 * @param {number} value - The number to format
 * @returns {string} - Formatted currency string
 */
function formatCurrency(value) {
    return '₹' + value.toFixed(2);
}
