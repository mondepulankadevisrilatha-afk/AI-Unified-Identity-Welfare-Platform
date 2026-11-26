/* Front-end niceties — progressive enhancement only. The app works
   without JavaScript; this just improves the experience. */
(function () {
  "use strict";

  // --- Mobile menu toggle ---
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // --- Dismiss flash messages ---
  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });

  // --- Auto fade-out flashes after 6s ---
  setTimeout(function () {
    document.querySelectorAll(".flash").forEach(function (f) {
      f.style.transition = "opacity .5s";
      f.style.opacity = "0";
      setTimeout(function () { f.remove(); }, 500);
    });
  }, 6000);

  // --- Live password-match hint on the register form ---
  var pw = document.querySelector('input[name="password"]');
  var confirm = document.querySelector('input[name="confirm"]');
  var hint = document.getElementById("pw-hint");
  if (pw && confirm && hint) {
    function checkMatch() {
      if (!confirm.value) { hint.textContent = ""; return; }
      if (pw.value === confirm.value) {
        hint.textContent = "✓ Passwords match";
        hint.style.color = "#34d399";
      } else {
        hint.textContent = "✗ Passwords do not match";
        hint.style.color = "#f87171";
      }
    }
    pw.addEventListener("input", checkMatch);
    confirm.addEventListener("input", checkMatch);
  }

  // --- Scroll reveal for feature cards ---
  if ("IntersectionObserver" in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.style.opacity = "1";
          e.target.style.transform = "none";
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll(".feature, .scheme-card").forEach(function (el) {
      el.style.opacity = "0";
      el.style.transform = "translateY(12px)";
      el.style.transition = "opacity .5s, transform .5s";
      obs.observe(el);
    });
  }

  // --- Loading state on submit buttons ---
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector('button[type="submit"], .btn[type="submit"]');
      if (btn && !form.hasAttribute("onsubmit")) {
        setTimeout(function () { btn.classList.add("loading"); }, 10);
      }
    });
  });
})();
