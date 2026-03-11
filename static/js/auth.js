/**
 * auth.js — Authentication & registration page interactions.
 *
 * Fully decoupled from Django template variables.
 * All input IDs are read from `data-input-id` attributes on buttons,
 * so this file needs zero modifications if form field IDs change.
 *
 * Features:
 *  1. Password visibility toggles — works on any button with class `pw-toggle-btn`
 *  2. Live password-match feedback — wired via `data-match-target-id`
 *  3. Client-side form submission guard — focuses first invalid field on error
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {

  /* ── 1. Password visibility toggles ────────────────────────
   *
   * Pattern:
   *   <button class="pw-toggle-btn" data-input-id="id_password">
   *
   * Optional: data-match-target-id on the confirm-password toggle
   * button (not used functionally here — kept for semantic clarity).
   */
  document.querySelectorAll(".pw-toggle-btn").forEach((btn) => {
    const inputId = btn.dataset.inputId;
    const input   = inputId ? document.getElementById(inputId) : null;
    if (!input) return;

    const icon = btn.querySelector("i");

    btn.addEventListener("click", function () {
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      if (icon) icon.className = isHidden ? "bi bi-eye-slash" : "bi bi-eye";
      // WCAG 4.1.2 — keep aria-label and aria-pressed in sync with state
      this.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
      this.setAttribute("aria-pressed", isHidden ? "true" : "false");
    });
  });

  /* ── 2. Live password-match feedback (WCAG 3.3.1) ──────────
   *
   * Pattern: the confirm-password button carries `data-match-target-id`
   * pointing at the first password input. The hint <div> must have id="pw2-hint".
   */
  const pw2Btn = document.querySelector(".pw-toggle-btn[data-match-target-id]");
  const hint   = document.getElementById("pw2-hint");

  if (pw2Btn && hint) {
    const pw1 = document.getElementById(pw2Btn.dataset.matchTargetId);
    const pw2 = document.getElementById(pw2Btn.dataset.inputId);

    function checkMatch() {
      if (!pw2 || !pw2.value) {
        hint.textContent = "";
        pw2?.setCustomValidity("");
        return;
      }
      if (pw1.value !== pw2.value) {
        hint.textContent = "Passwords do not match.";
        hint.style.color = "#991b1b";
        pw2.setCustomValidity("Passwords do not match.");
      } else {
        hint.textContent = "Passwords match.";
        hint.style.color = "#15803d";
        pw2.setCustomValidity("");
      }
    }

    pw1?.addEventListener("input", checkMatch);
    pw2?.addEventListener("input", checkMatch);
  }

  /* ── 3. Form submission guard ───────────────────────────────
   * Prevents submitting if browser-native constraint validation fails,
   * and moves focus to the first invalid field for keyboard users.
   */
  document.querySelectorAll("form[novalidate]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!form.checkValidity()) {
        e.preventDefault();
        const firstInvalid = form.querySelector(":invalid");
        firstInvalid?.focus();
      }
    });
  });

});
