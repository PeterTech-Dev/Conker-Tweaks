let cart = []; // global cart

function updateCartDisplay() {
  const cartItemsDiv = document.getElementById('checkout-products');
  const cartTotalSpan = document.getElementById('cart-total');
  cartItemsDiv.innerHTML = '';
  let total = 0;

  if (cart.length === 0) {
    cartItemsDiv.innerHTML = '<p id="empty-cart-message">Your cart is empty.</p>';
    cartTotalSpan.textContent = '$0.00';
    return;
  }

  cart.forEach((item, index) => {
    total += item.price * item.quantity;

    const itemDiv = document.createElement('div');
    itemDiv.className = 'checkout-item';

    itemDiv.innerHTML = `
      <div class="item-name">${item.name}</div>
      <div class="quantity-controls">
        <button class="qty-btn decrease" data-index="${index}">-</button>
        <span class="qty-number" id="qty-${index}">${item.quantity}</span>
        <button class="qty-btn increase" data-index="${index}">+</button>
      </div>
      <div class="item-price" id="price-${index}">$${(item.price * item.quantity).toFixed(2)}</div>
    `;

    cartItemsDiv.appendChild(itemDiv);
  });

  cartTotalSpan.textContent = `$${total.toFixed(2)}`;
}

function handleCartButtonClick(event) {
  if (event.target.classList.contains('qty-btn')) {
    const index = parseInt(event.target.getAttribute('data-index'));

    if (!isNaN(index) && cart[index]) {
      if (event.target.classList.contains('increase')) {
        cart[index].quantity++;
      } else if (event.target.classList.contains('decrease') && cart[index].quantity > 1) {
        cart[index].quantity--;
      }

      // Save and Re-render
      localStorage.setItem('cart', JSON.stringify(cart));
      updateCartDisplay(); // 💥 FULL re-render the cart (qty, price, total)
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  cart = JSON.parse(localStorage.getItem('cart')) || [];
  updateCartDisplay();

  document.getElementById('checkout-products').addEventListener('click', handleCartButtonClick);
});

function directPurchase(id, name, price) {
  fetch(`https://conker-tweaks-production.up.railway.app/product/${id}`)
    .then(res => res.json())
    .then(product => {
      if (product.stock === 0) {
        alert("Sorry, this product is out of stock.");
        return;
      }

      // Continue with adding to cart...
      const cart = JSON.parse(localStorage.getItem('cart')) || [];
      const existingItem = cart.find(item => item.id === id);
      if (existingItem) {
        if (product.stock !== -1 && existingItem.quantity >= product.stock) {
          alert("You’ve reached the stock limit.");
          return;
        }
        existingItem.quantity += 1;
      } else {
        cart.push({ id, name, price, quantity: 1 });
      }

      localStorage.setItem('cart', JSON.stringify(cart));
      window.location.href = "/static/Cart/cart.html";
    });
}



