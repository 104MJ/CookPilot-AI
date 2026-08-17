(function () {
  const skeleton = document.getElementById("history-skeleton");
  const list = document.getElementById("session-list");
  const errorSlot = document.getElementById("history-error-slot");
  const pagination = document.getElementById("history-pagination");
  const prevBtn = document.getElementById("history-prev");
  const nextBtn = document.getElementById("history-next");
  const pageLabel = document.getElementById("history-page-label");

  const STATUS_LABELS = {
    pending: "En attente",
    processing: "En cours",
    done: "Terminé",
    failed: "Échec",
  };

  let currentPage = 1;

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function renderSession(session) {
    const item = document.createElement("a");
    item.className = "session-item";
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

  async function loadPage(page) {
    skeleton.style.display = "block";
    list.style.display = "none";
    pagination.style.display = "none";

    try {
      const data = await CookPilotAPI.listSessions(page);
      currentPage = page;
      skeleton.style.display = "none";
      list.style.display = "flex";
      list.innerHTML = "";

      if (data.results.length === 0) {
        list.innerHTML = '<p class="hint" style="padding: var(--space-4)">Aucune analyse pour le moment.</p>';
        return;
      }

      data.results.forEach((session) => list.appendChild(renderSession(session)));

      pagination.style.display = data.next || data.previous ? "flex" : "none";
      prevBtn.disabled = !data.previous;
      nextBtn.disabled = !data.next;
      pageLabel.textContent = `Page ${currentPage}`;
    } catch (err) {
      skeleton.style.display = "none";
      renderAlert(errorSlot, {
        type: "danger",
        message: "Impossible de charger votre historique. Réessayez plus tard.",
      });
    }
  }

  prevBtn.addEventListener("click", () => loadPage(currentPage - 1));
  nextBtn.addEventListener("click", () => loadPage(currentPage + 1));

  loadPage(1);
})();
