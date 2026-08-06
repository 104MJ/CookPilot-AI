(function () {
  const skeleton = document.getElementById("history-skeleton");
  const list = document.getElementById("session-list");
  const errorSlot = document.getElementById("history-error-slot");

  const STATUS_LABELS = {
    pending: "En attente",
    processing: "En cours",
    done: "Terminé",
    failed: "Échec",
  };

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function renderSession(session) {
    const item = document.createElement("a");
    item.className = "card session-item";
    item.href = `/sessions/${session.id}/`;

    const left = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent =
      session.recipes[0]?.title || (session.status === "failed" ? "Analyse échouée" : "Analyse en cours");
    const meta = document.createElement("div");
    meta.className = "session-item__meta";
    meta.textContent = formatDate(session.created_at);
    left.appendChild(title);
    left.appendChild(meta);

    const badge = document.createElement("span");
    badge.className = `badge badge-${session.status}`;
    badge.textContent = STATUS_LABELS[session.status] || session.status;

    item.appendChild(left);
    item.appendChild(badge);
    return item;
  }

  async function init() {
    try {
      const sessions = await CookPilotAPI.listSessions();
      skeleton.style.display = "none";
      list.style.display = "flex";

      if (sessions.length === 0) {
        list.innerHTML = '<p class="hint">Aucune analyse pour le moment.</p>';
        return;
      }

      sessions.forEach((session) => list.appendChild(renderSession(session)));
    } catch (err) {
      skeleton.style.display = "none";
      renderAlert(errorSlot, {
        type: "danger",
        message: "Impossible de charger votre historique. Réessayez plus tard.",
      });
    }
  }

  init();
})();
