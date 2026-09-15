(() => {
  const stack = () => document.getElementById("avisos");

  function armToast(root) {
    const toast = root.querySelector(".toast");
    if (!toast) return;
    window.clearTimeout(toast._hideTimer);
    toast._hideTimer = window.setTimeout(() => {
      toast.classList.add("toast--out");
      window.setTimeout(() => {
        if (toast.parentElement) toast.remove();
      }, 220);
    }, 2600);
  }

  function pulseBadge() {
    const badge = document.querySelector("#carrito-badge .badge-carrito");
    if (!badge) return;
    badge.classList.remove("badge-carrito--pulse");
    // reflow
    void badge.offsetWidth;
    badge.classList.add("badge-carrito--pulse");
  }

  function setNavOpen(open) {
    const dash = document.getElementById("dash");
    const toggle = document.querySelector("[data-nav-toggle]");
    if (!dash) return;
    dash.classList.toggle("is-nav-open", open);
    if (toggle) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
    }
  }

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target && event.detail.target.id === "avisos") {
      armToast(event.detail.target);
      pulseBadge();
    }
  });

  document.addEventListener("click", (event) => {
    const t = event.target;
    if (!(t instanceof Element)) return;
    if (t.closest("[data-nav-toggle]")) {
      const dash = document.getElementById("dash");
      setNavOpen(!(dash && dash.classList.contains("is-nav-open")));
      return;
    }
    if (t.closest("[data-nav-close]")) {
      setNavOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setNavOpen(false);
  });
})();
