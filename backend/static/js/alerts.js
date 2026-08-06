/**
 * Shared error/alert banner helper. Renders a dismissible alert into a slot
 * element, with an optional action button (e.g. "Réessayer", "Saisir à la main").
 */
function renderAlert(slotEl, { type = "danger", message, actionLabel, onAction } = {}) {
  slotEl.innerHTML = "";
  const alert = document.createElement("div");
  alert.className = `alert alert-${type}`;
  alert.setAttribute("role", "alert");

  const body = document.createElement("div");
  const text = document.createElement("p");
  text.style.margin = "0";
  text.textContent = message;
  body.appendChild(text);

  if (actionLabel && onAction) {
    const actions = document.createElement("div");
    actions.className = "alert-actions";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = actionLabel;
    btn.addEventListener("click", onAction);
    actions.appendChild(btn);
    body.appendChild(actions);
  }

  alert.appendChild(body);
  slotEl.appendChild(alert);
}

function clearAlert(slotEl) {
  slotEl.innerHTML = "";
}
