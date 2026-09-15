document.addEventListener("click", (event) => {
  document.querySelectorAll("details.admin-user__menu[open]").forEach((menu) => {
    if (!menu.contains(event.target)) {
      menu.removeAttribute("open");
    }
  });
});
