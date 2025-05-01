const token = localStorage.getItem("access_token");

if (!token) {
  window.location.href = "/static/Login/Login.html";
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
  fetch("https://conker-tweaks-production.up.railway.app/admin/dashboard", {
    headers: { "Authorization": "Bearer " + token }
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("dashboard-container").innerHTML = `
      <div class="card"><strong>Users:</strong> ${data.users}</div>
      <div class="card"><strong>Products:</strong> ${data.products}</div>
      <div class="card"><strong>Purchases:</strong> ${data.purchases}</div>
    `;
  });
}
