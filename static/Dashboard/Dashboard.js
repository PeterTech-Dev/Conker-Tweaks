const token = localStorage.getItem("access_token"); // ✅ available globally

window.addEventListener("DOMContentLoaded", () => {
  if (!token) {
    window.location.href = "/static/Login/Login.html";
    return;
  }

  fetch("https://conker-tweaks-production.up.railway.app/auth/profile", {
    headers: {
      "Authorization": "Bearer " + token
    }
  })
    .then(res => res.json())
    .then(user => {
      if (!user.is_admin || !user.has_2fa) {
        window.location.href = "/static/Landing/Landing.html";
      } else {
        document.getElementById("admin-main").style.display = "block";
        loadAdminData();
      }
    })
    .catch(() => {
      window.location.href = "/static/Login/Login.html";
    });

  function loadAdminData() {
    fetch("https://conker-tweaks-production.up.railway.app/owner/dashboard", {
      headers: { "Authorization": "Bearer " + token }
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("stats").innerHTML = `
          <div class="card"><strong>Users:</strong> ${data.users}</div>
          <div class="card"><strong>Products:</strong> ${data.products}</div>
          <div class="card"><strong>Purchases:</strong> ${data.purchases}</div>
        `;
      });

    fetch("https://conker-tweaks-production.up.railway.app/owner/list-products", {
      headers: { "Authorization": "Bearer " + token }
    })
      .then(res => res.json())
      .then(products => {
        const list = document.getElementById("product-list");
        list.innerHTML = "";
        products.forEach(product => {
          const div = document.createElement("div");
          div.classList.add("card");
          div.innerHTML = `
            <strong>${product.name}</strong><br>
            Price: R${product.price}<br>
            Stock: ${product.stock}<br>
            License: ${product.needs_license ? "Yes" : "No"}<br>
            <button onclick="addKey(${product.id})">Add License Key</button>
            <button onclick="deleteProduct(${product.id})">Delete</button>
          `;
          list.appendChild(div);
        });
      });
  }

  document.getElementById("add-product-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const product = {
      name: document.getElementById("name").value,
      description: document.getElementById("description").value,
      price: parseFloat(document.getElementById("price").value),
      stock: parseInt(document.getElementById("stock").value),
      download_link: document.getElementById("download_link").value,
      needs_license: document.getElementById("needs_license").checked
    };

    const res = await fetch("https://conker-tweaks-production.up.railway.app/owner/add_product", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(product)
    });

    if (res.ok) {
      alert("Product added");
      loadAdminData();
      e.target.reset();
    } else {
      const err = await res.json();
      alert("Error: " + err.detail);
    }
  });

  window.addKey = function (productId) {
    const key = prompt("Enter license key:");
    if (!key) return;

    fetch("https://conker-tweaks-production.up.railway.app/owner/add_license_key", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ product_id: productId, key: key })
    })
      .then(res => res.json())
      .then(() => {
        alert("License key added");
      });
  };

  window.deleteProduct = function (productId) {
    if (!confirm("Are you sure you want to delete this product?")) return;

    fetch(`https://conker-tweaks-production.up.railway.app/owner/delete-product/${productId}`, {
      method: "DELETE",
      headers: { "Authorization": "Bearer " + token }
    })
      .then(res => res.json())
      .then(() => {
        alert("Product deleted");
        loadAdminData();
      });
  };
});
