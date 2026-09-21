(() => {
  "use strict";

  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    if (!copied) throw new Error("copy_failed");
  };

  const activateTab = (root, tabName, updateHash = true) => {
    const tabs = [...root.querySelectorAll("[data-profile-tab]")];
    const panels = [...root.querySelectorAll("[data-profile-panel]")];
    const selected = tabs.find((tab) => tab.dataset.profileTab === tabName) || tabs[0];
    if (!selected) return;

    tabs.forEach((tab) => {
      const active = tab === selected;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });

    panels.forEach((panel) => {
      const active = panel.dataset.profilePanel === selected.dataset.profileTab;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });

    if (updateHash && window.history && window.history.replaceState) {
      const nextUrl = `${window.location.pathname}${window.location.search}#${selected.dataset.profileTab}`;
      window.history.replaceState(null, "", nextUrl);
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-profile-v2]").forEach((root) => {
      const requested = window.location.hash.replace("#", "").trim();
      activateTab(root, requested || "overview", false);
    });
  });

  document.addEventListener("click", async (event) => {
    const tab = event.target.closest("[data-profile-tab]");
    if (tab) {
      const root = tab.closest("[data-profile-v2]");
      if (root) activateTab(root, tab.dataset.profileTab);
      return;
    }

    const button = event.target.closest("[data-profile-share]");
    if (!button) return;
    const original = button.dataset.shareLabel || button.textContent.trim();
    try {
      await copyText(window.location.href.split("#")[0]);
      button.textContent = "✓ Đã sao chép liên kết";
      button.classList.add("is-copied");
      window.setTimeout(() => {
        button.textContent = original;
        button.classList.remove("is-copied");
      }, 2200);
    } catch (_error) {
      button.textContent = "Không thể sao chép";
      window.setTimeout(() => { button.textContent = original; }, 2200);
    }
  });
})();
