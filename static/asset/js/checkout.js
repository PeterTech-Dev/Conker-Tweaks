function renderCart() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const checkoutContainer = document.getElementById('checkout-products');
  
    if (cart.length === 0) {
      checkoutContainer.innerHTML = "<p>Your cart is empty.</p>";
      return;
    }
  
    let html = "";
    cart.forEach((item, index) => {
      html += `
        <div class="checkout-item">
            <span class="item-name">${item.name || 'Unnamed Product'}</span>
            <span class="item-price">$${(item.price * item.quantity).toFixed(2)}</span>
            <div class="quantity-controls">
                <button type="button" class="qty-btn" onclick="updateQuantity(${index}, -1)">-</button>
                <span class="qty-number">${item.quantity}</span>
                <button type="button" class="qty-btn" onclick="updateQuantity(${index}, 1)">+</button>
            </div>
        </div>
      `;
    });
  
    checkoutContainer.innerHTML = html;
  }
  
  window.addEventListener("DOMContentLoaded", function () {
    renderCart(); // ✅ Render cart when page loads
  });
  
  function updateQuantity(index, change) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    if (cart[index]) {
      cart[index].quantity += change;
      if (cart[index].quantity <= 0) {
        cart.splice(index, 1);
      }
      localStorage.setItem('cart', JSON.stringify(cart));
      renderCart(); // ✅ Re-render cart after quantity changes
    }
  }
  