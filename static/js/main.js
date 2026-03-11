/**
 * main.js — Study Planner core JavaScript
 *
 * Responsibilities:
 *  - CSRF helper & shared ajaxPost()
 *  - Toast notification system
 *  - Auto-dismiss Django flash messages
 *  - Countdown timers for due dates
 *  - Stat counter animation on dashboard
 */

"use strict";

/* ──────────────────────────────────────────
   CSRF helper
────────────────────────────────────────── */
function getCookie(name) {
  for (const cookie of document.cookie.split(";")) {
    const [k, v] = cookie.trim().split("=");
    if (k === name) return decodeURIComponent(v);
  }
  return null;
}
const CSRF_TOKEN = getCookie("csrftoken");

/**
 * POST JSON to a URL, return parsed response JSON.
 * @param {string} url
 * @param {object} [data]
 * @returns {Promise<object>}
 */
function ajaxPost(url, data = {}) {
  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
    },
    body: JSON.stringify(data),
  }).then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  });
}

/* ──────────────────────────────────────────
   Toast notification system
────────────────────────────────────────── */
let toastContainer = null;

/**
 * Show a lightweight toast message.
 * @param {string} message
 * @param {'success'|'error'|'info'} [type]
 * @param {number} [duration] ms before auto-removing
 */
function showToast(message, type = "success", duration = 3200) {
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    document.body.appendChild(toastContainer);
  }

  const icons = { success: "bi-check-circle-fill", error: "bi-x-circle-fill", info: "bi-info-circle-fill" };
  const toast = document.createElement("div");
  toast.className = `sp-toast ${type}`;
  // WCAG 4.1.3 Status Messages — errors are assertive, others polite
  toast.setAttribute("role", type === "error" ? "alert" : "status");
  toast.setAttribute("aria-live", type === "error" ? "assertive" : "polite");
  toast.setAttribute("aria-atomic", "true");
  toast.innerHTML = `<i class="bi ${icons[type] || icons.info}" aria-hidden="true"></i> ${message}`;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity .3s, transform .3s";
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

/* ──────────────────────────────────────────
   Auto-dismiss Django flash messages
────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert.alert-dismissible").forEach((el) => {
    setTimeout(() => {
      bootstrap.Alert.getOrCreateInstance(el)?.close();
    }, 4500);
  });

  /* ── Countdown timers ── */
  initCountdowns();

  /* ── Animated stat counters ── */
  initStatCounters();
});

/* ──────────────────────────────────────────
   Due-date countdown timers
   Looks for elements: <time data-due="ISO-string">
────────────────────────────────────────── */
function initCountdowns() {
  const elements = document.querySelectorAll("[data-due]");
  if (!elements.length) return;

  function render() {
    const now = Date.now();
    elements.forEach((el) => {
      const due  = new Date(el.dataset.due).getTime();
      const diff = due - now;                     // ms remaining
      const mins  = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days  = Math.floor(diff / 86400000);

      let label, cls;
      if (diff < 0) {
        const absDays  = Math.abs(days);
        label = absDays > 0 ? `${absDays}d overdue` : "Overdue";
        cls = "overdue";
      } else if (hours < 24) {
        label = hours < 1 ? `${mins}m left` : `${hours}h left`;
        cls = hours < 6 ? "urgent" : "warning";
      } else if (days <= 3) {
        label = `${days}d left`;
        cls = "warning";
      } else {
        label = `${days}d left`;
        cls = "normal";
      }

      el.textContent = label;
      el.className   = `countdown-badge ${cls}`;
    });
  }

  render();
  setInterval(render, 30000);   // refresh every 30 s
}

/* ──────────────────────────────────────────
   Animated stat counter (dashboard)
   Looks for: <span data-count="42">
────────────────────────────────────────── */
function initStatCounters() {
  const els = document.querySelectorAll("[data-count]");
  if (!els.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(({ isIntersecting, target }) => {
      if (!isIntersecting) return;
      observer.unobserve(target);

      const end      = parseInt(target.dataset.count, 10);
      const duration = 600;
      const start    = performance.now();

      function step(now) {
        const progress = Math.min((now - start) / duration, 1);
        // Ease-out quad
        const eased = 1 - (1 - progress) * (1 - progress);
        target.textContent = Math.round(eased * end);
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }, { threshold: 0.3 });

  els.forEach((el) => observer.observe(el));
}
