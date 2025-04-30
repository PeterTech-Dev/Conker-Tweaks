window.addEventListener("load", () => {
  console.log(
    "%cDesigned by %cPeter Papasotiriou",
    "color: #ccc; font-size: 20px;",
    "color: #00e0ff; font-size: 20px; font-weight: bold;"
  );
  console.log(
    "%c📎 GitHub: %chttps://github.com/PeterTech-Dev",
    "color: #ccc; font-size: 13px;",
    "color: #00e0ff; font-size: 13px;"
  );
  console.log(
    "%c💬 Discord: %cmrmaniti",
    "color: #ccc; font-size: 13px;",
    "color: #00e0ff; font-size: 13px;"
  );

  const loader = document.querySelector(".loader-wrapper");
  if (loader) {
    loader.style.display = "none";
  }
});

const circles = document.querySelectorAll(".glow-circle");

function getRandomPosition() {
  return {
    top: `${Math.random() * 100 - 20}%`,
    left: `${Math.random() * 100 - 20}%`
  };
}

function scheduleFade(circle) {
  const delay = Math.random() * 5000 + 5000; // 5–10 seconds

  setTimeout(() => {
    circle.style.opacity = "0";

    setTimeout(() => {
      const { top, left } = getRandomPosition();
      circle.style.transition = "none"; 
      circle.style.top = top;
      circle.style.left = left;

      void circle.offsetWidth; // trigger reflow

      circle.style.transition = "opacity 1.2s ease";
      circle.style.opacity = "0.1";

      scheduleFade(circle);
    }, 1200);
  }, delay);
}

circles.forEach((circle) => {
  const { top, left } = getRandomPosition();
  circle.style.top = top;
  circle.style.left = left;
  circle.style.opacity = "0.1";
  scheduleFade(circle);
});

const yearSpan = document.getElementById("year");
if (yearSpan) {
  yearSpan.textContent = new Date().getFullYear();
}

document.addEventListener("DOMContentLoaded", function () {
  if (localStorage.getItem("just_logged_in") === "true") {
    const popup = document.getElementById("login-popup");
    if (popup) {
      popup.style.display = "block";

      setTimeout(() => {
        popup.style.display = "none";
        localStorage.removeItem("just_logged_in");
      }, 4000);
    }
  }
});
