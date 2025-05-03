const token = localStorage.getItem("access_token");

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
            const descLines = product.description
              .split('\n')
              .filter(line => line.trim() !== '');
            const descHTML = descLines.map(line => `<li>${line}</li>`).join('');
    
            const isInfinite = product.stock === -1;
    
            const div = document.createElement("div");
            div.classList.add("pricing-card");
            div.innerHTML = `
              <h3>${product.name}</h3>
              <h2 class="price">$${Number(product.price).toFixed(2)}</h2>
              <div class="stock-available">${isInfinite ? "∞ Available" : `${product.stock} Available`}</div>
              <ul>${descHTML}</ul>
              <button class="purchase-btn" onclick="addKey(${product.id})">Add License Key</button>
              <button class="purchase-btn" onclick="deleteProduct(${product.id})">Delete</button>
              <button class="purchase-btn" onclick="setInfiniteStock(${product.id})">Set Infinite Stock</button>
              <button class="purchase-btn" onclick="editProduct(${product.id}, '${product.name}', \`${product.description}\`, ${product.price}, ${product.stock}, '${product.download_link}', ${product.needs_license})">Edit</button>
            `;
            list.appendChild(div);
          });
        });
    }
    

  document.getElementById("add-product-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const infiniteStock = document.getElementById("infinite_stock").checked;

    const product = {
      name: document.getElementById("name").value,
      description: document.getElementById("description").value,
      price: parseFloat(document.getElementById("price").value),
      stock: infiniteStock ? -1 : parseInt(document.getElementById("stock").value),
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

window.setInfiniteStock = function(productId) {
  fetch(`https://conker-tweaks-production.up.railway.app/owner/set-stock/${productId}`, {
    method: "PATCH",
    headers: {
      "Authorization": "Bearer " + token
    }
  })
    .then(res => {
      if (!res.ok) throw new Error("Failed to update stock");
      return res.json();
    })
    .then(() => {
      alert("Stock set to infinite");
      loadAdminData();
    })
    .catch(err => {
      console.error(err);
      alert("Failed to set stock to infinite");
    });
};

window.editProduct = function (id, name, description, price, stock, link, needsLicense) {
  const newName = prompt("Edit name:", name);
  if (!newName) return;

  const newDesc = prompt("Edit description (\\n for new lines):", description);
  if (newDesc === null) return;

  const newPrice = parseFloat(prompt("Edit price:", price));
  if (isNaN(newPrice)) return;

  const newStock = parseInt(prompt("Edit stock (-1 for infinite):", stock));
  if (isNaN(newStock)) return;

  const newLink = prompt("Edit download link:", link);
  if (!newLink) return;

  const newNeedsLicense = confirm("Does this require a license key?");

  fetch(`https://conker-tweaks-production.up.railway.app/owner/update-product/${productId}`, {
    method: "PATCH",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: newName,
      description: newDesc,
      price: newPrice,
      stock: newStock,
      download_link: newLink,
      needs_license: newNeedsLicense
    })
  })
    .then(res => {
      if (!res.ok) throw new Error("Update failed");
      return res.json();
    })
    .then(() => {
      alert("Product updated");
      loadAdminData();
    })
    .catch(err => {
      console.error(err);
      alert("Error updating product");
    });
};


