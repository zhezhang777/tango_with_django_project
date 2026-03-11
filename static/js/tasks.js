/**
 * tasks.js
 *  1. AJAX toggle task status — optimistic UI update + toast
 *  2. Delete modal — populate title & action URL
 *  3. Filter form — auto-submit on select change
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {

  /* ── 1. AJAX status toggle ─────────────────────────────── */
  document.querySelectorAll(".toggle-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const taskId   = btn.dataset.taskId;
      const url      = btn.dataset.url;
      const redirect = btn.dataset.redirect;

      // Optimistic visual feedback — disable while in-flight
      btn.disabled = true;

      try {
        const data = await ajaxPost(url);

        // Detail page: just navigate so all copy updates
        if (redirect) { window.location.href = redirect; return; }

        // ── Update list row ──
        const row   = document.getElementById(`task-row-${taskId}`);
        const icon  = btn.querySelector("i");

        if (data.is_done) {
          row.classList.add("task-row-done");
          icon.className = "bi bi-check-circle-fill text-success fs-5";
          btn.setAttribute("aria-pressed", "true");
          btn.setAttribute("aria-label", "Mark as not done");
          showToast("Task marked as done!", "success");
        } else {
          row.classList.remove("task-row-done");
          icon.className = "bi bi-circle text-muted fs-5";
          btn.setAttribute("aria-pressed", "false");
          btn.setAttribute("aria-label", "Mark as done");
          showToast("Task moved back to To-Do.", "info");
        }

        // Update the status badge in the row
        const statusBadge = row.querySelector(".status-badge");
        if (statusBadge) {
          statusBadge.textContent = data.status_label;
          statusBadge.className = `badge rounded-pill small status-badge ${
            data.is_done ? "bg-success" : "bg-secondary"
          }`;
        }

      } catch (err) {
        showToast("Could not update task. Please try again.", "error");
        console.error("Toggle error:", err);
      } finally {
        btn.disabled = false;
      }
    });
  });

  /* ── 2. Delete modal — wiring + focus management ──────── */
  const deleteModal = document.getElementById("deleteModal");
  if (deleteModal) {
    let _triggerEl = null;   // remember which button opened the modal

    deleteModal.addEventListener("show.bs.modal", (event) => {
      const trigger = event.relatedTarget;
      if (!trigger) return;
      _triggerEl = trigger;  // save for return-focus on close

      const taskTitle   = trigger.dataset.taskTitle;
      // Use the URL pre-rendered in data-delete-url — no path hard-coding
      const deleteUrl   = trigger.dataset.deleteUrl;

      const titleEl = deleteModal.querySelector("#deleteTaskTitle");
      if (titleEl) titleEl.textContent = taskTitle;

      const form = deleteModal.querySelector("#deleteForm");
      if (form && deleteUrl) form.action = deleteUrl;
    });

    /*
     * WCAG 2.4.3 Focus Order & 2.1.2 No Keyboard Trap:
     * After the modal closes without deleting, return focus to the
     * button that triggered it so keyboard users don't lose their place.
     */
    deleteModal.addEventListener("hidden.bs.modal", () => {
      if (_triggerEl) { _triggerEl.focus(); _triggerEl = null; }
    });

    // Move initial focus to the Cancel button when modal opens
    deleteModal.addEventListener("shown.bs.modal", () => {
      deleteModal.querySelector(".btn-outline-secondary")?.focus();
    });
  }

  /* ── 3. Auto-submit filter selects ────────────────────── */
  document.querySelectorAll(".filter-autosubmit").forEach((sel) => {
    sel.addEventListener("change", () => sel.closest("form").submit());
  });

});
