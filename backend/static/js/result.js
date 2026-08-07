(function () {
  const root = document.getElementById("result-page");
  const sessionId = Number(root.dataset.sessionId);
  const mockFailure = new URLSearchParams(window.location.search).get("mock") || undefined;

  const statusBadge = document.getElementById("status-badge");
  const skeleton = document.getElementById("result-skeleton");
  const skeletonStatusText = document.getElementById("skeleton-status-text");
  const content = document.getElementById("result-content");
  const errorSlot = document.getElementById("result-error-slot");
  const ingredientTags = document.getElementById("ingredient-tags");
  const recipeList = document.getElementById("recipe-list");

  const STATUS_LABELS = {
    pending: "En attente",
    processing: "En cours d'analyse",
    done: "Terminé",
    failed: "Échec",
  };

  function setStatusBadge(status) {
    statusBadge.textContent = STATUS_LABELS[status] || status;
    statusBadge.className = `badge badge-${status}`;
  }

  function renderIngredients(session) {
    ingredientTags.innerHTML = "";
    const all = [...session.detected_ingredients, ...session.manual_ingredients];
    if (all.length === 0) {
      ingredientTags.innerHTML = '<p class="hint">Aucun ingrédient identifié.</p>';
      return;
    }
    all.forEach((ing) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = ing.expires_at ? `${ing.name} (péremption ${ing.expires_at})` : ing.name;
      ingredientTags.appendChild(tag);
    });
  }

  function renderRating(container, recipe) {
    container.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "rating";

    const likeBtn = document.createElement("button");
    likeBtn.type = "button";
    likeBtn.className = "btn-icon" + (recipe.rating === 1 ? " is-active" : "");
    likeBtn.setAttribute("aria-label", "J'aime cette recette");
    likeBtn.textContent = "👍";

    const dislikeBtn = document.createElement("button");
    dislikeBtn.type = "button";
    dislikeBtn.className = "btn-icon" + (recipe.rating === -1 ? " is-active" : "");
    dislikeBtn.setAttribute("aria-label", "Je n'aime pas cette recette");
    dislikeBtn.textContent = "👎";

    async function rate(value) {
      const previous = recipe.rating;
      recipe.rating = recipe.rating === value ? null : value;
      try {
        await CookPilotAPI.rateRecipe(recipe.id, recipe.rating);
        renderRating(container, recipe);
      } catch (err) {
        recipe.rating = previous;
        renderAlert(errorSlot, {
          type: "danger",
          message: "La notation n'a pas pu être enregistrée. Réessayez.",
        });
      }
    }

    likeBtn.addEventListener("click", () => rate(1));
    dislikeBtn.addEventListener("click", () => rate(-1));

    wrapper.appendChild(likeBtn);
    wrapper.appendChild(dislikeBtn);
    container.appendChild(wrapper);
  }

  function renderRecipe(recipe) {
    const card = document.createElement("article");
    card.className = "card";
    card.style.marginBottom = "var(--space-4)";

    const title = document.createElement("h2");
    title.style.marginTop = "0";
    title.textContent = recipe.title;
    card.appendChild(title);

    if (recipe.ingredients_missing.length > 0) {
      const missing = document.createElement("p");
      missing.className = "hint";
      missing.textContent = `Il vous manque : ${recipe.ingredients_missing.join(", ")}`;
      card.appendChild(missing);
    }

    if (recipe.total_calories) {
      const grid = document.createElement("div");
      grid.className = "nutrition-grid";
      const stats = [
        { label: "kcal", value: recipe.total_calories },
        { label: "protéines (g)", value: recipe.nutrition_breakdown?.protein_g ?? "–" },
        { label: "glucides (g)", value: recipe.nutrition_breakdown?.carbs_g ?? "–" },
        { label: "lipides (g)", value: recipe.nutrition_breakdown?.fat_g ?? "–" },
      ];
      stats.forEach((s) => {
        const stat = document.createElement("div");
        stat.className = "nutrition-stat";
        stat.innerHTML = `<span class="nutrition-stat__value">${s.value}</span><span class="nutrition-stat__label">${s.label}</span>`;
        grid.appendChild(stat);
      });
      card.appendChild(grid);
    }

    const steps = document.createElement("ol");
    steps.className = "recipe-steps";
    recipe.steps.forEach((step) => {
      const li = document.createElement("li");
      li.textContent = step;
      steps.appendChild(li);
    });
    card.appendChild(steps);

    if (recipe.personalization_notes) {
      const notes = document.createElement("p");
      notes.className = "hint";
      notes.textContent = `💡 Adapté à votre profil : ${recipe.personalization_notes}`;
      card.appendChild(notes);
    }

    const ratingContainer = document.createElement("div");
    card.appendChild(ratingContainer);
    renderRating(ratingContainer, recipe);

    return card;
  }

  function renderRecipes(session) {
    recipeList.innerHTML = "";
    session.recipes.forEach((recipe) => recipeList.appendChild(renderRecipe(recipe)));
  }

  function showFailed(session) {
    skeleton.style.display = "none";
    content.style.display = "none";
    renderAlert(errorSlot, {
      type: "danger",
      message: session.error_message || "Une erreur est survenue pendant l'analyse.",
      actionLabel: "Réessayer avec une autre photo ou en saisie manuelle",
      onAction: () => {
        window.location.href = "/";
      },
    });
  }

  function showDone(session) {
    skeleton.style.display = "none";
    content.style.display = "block";
    renderIngredients(session);
    renderRecipes(session);
  }

  async function init() {
    setStatusBadge("pending");
    let session;
    try {
      session = await CookPilotAPI.getSession(sessionId);
    } catch (err) {
      renderAlert(errorSlot, { type: "danger", message: "Cette session est introuvable." });
      skeleton.style.display = "none";
      return;
    }

    setStatusBadge(session.status);

    if (session.status === "done") {
      showDone(session);
      return;
    }
    if (session.status === "failed") {
      showFailed(session);
      return;
    }

    // pending / processing -> keep polling (stand-in for a real SSE/stream)
    await CookPilotAPI.pollSessionUntilDone(
      sessionId,
      (updated) => {
        setStatusBadge(updated.status);
        if (updated.status === "processing") {
          skeletonStatusText.textContent = "Génération de la recette par l'IA…";
        }
        if (updated.status === "done") {
          showDone(updated);
        }
        if (updated.status === "failed") {
          showFailed(updated);
        }
      },
      { simulateFailure: mockFailure }
    );
  }

  init();
})();
