document.addEventListener("DOMContentLoaded", function () {
  const loginIcon = document.getElementById("login-icon");
  const loginButton = document.getElementById("login-button");
  const loginLink = document.getElementById("login-link");
  const loginText = document.getElementById("login-text");

  const isLoggedIn = localStorage.getItem("access_token") !== null;

  if (isLoggedIn) {
    // Change the text separately
    if (loginText) loginText.textContent = "Profile";

    // Optionally change the icon if you want (or skip if the same icon)
    if (loginIcon) {
      const newSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      newSvg.setAttribute("class", "icon-img");
      newSvg.setAttribute("viewBox", "0 0 512 512");
      newSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");

      // Add circle
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", "256");
      circle.setAttribute("cy", "128");
      circle.setAttribute("r", "128");
      newSvg.appendChild(circle);

      // Add path
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M256,298.667c-105.99,0.118-191.882,86.01-192,192C64,502.449,73.551,512,85.333,512h341.333c11.782,0,21.333-9.551,21.333-21.333C447.882,384.677,361.99,298.784,256,298.667z");
      newSvg.appendChild(path);

      // ✅ Replace the old icon
      loginIcon.replaceWith(newSvg);
    }

    // Change button link to Profile
    if (loginLink) loginLink.href = "/static//viewprofile/viewprofile.html";

    // ⛔ Prevent button submitting, and manually redirect
      loginButton.addEventListener("click", function (e) {
        e.preventDefault(); // stop default button behavior
        window.location.href = loginLink.href; // manually go to the updated href
      });
  }
});
