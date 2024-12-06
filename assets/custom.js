document.addEventListener("DOMContentLoaded", () => {
  const navItems = document.querySelectorAll(".md-nav__link");
  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      item.style.color = "#B91C1C"; // クリック時に赤色を強調
    });
  });
});
