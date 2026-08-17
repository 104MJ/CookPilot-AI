/**
 * Client API reel pour CookPilot — remplace le mock localStorage precedent
 * par de vrais appels fetch() vers les endpoints DRF (voir
 * backend/ai_engine/views.py + urls.py). Signatures et shapes de retour
 * inchangees : le reste du code (scan.js, result.js, history.js) n'a pas
 * a etre modifie.
 *
 * Contrat (identique au mock precedent) :
 *   Session (History):
 *     { id, status: "pending"|"processing"|"done"|"failed",
 *       photo_url, error_message,
 *       detected_ingredients: [{ name, expires_at }],
 *       manual_ingredients: [{ name, expires_at }],
 *       created_at,
 *       recipes: [Recipe] }
 *
 *   Recipe:
 *     { id, title, ingredients_used: [{name, quantity}], ingredients_missing: [string],
 *       steps: [string], rating: -1|1|null,
 *       total_calories, nutrition_breakdown: { protein_g, carbs_g, fat_g, fiber_g } }
 */

const CookPilotAPI = (function () {
  // lit le cookie csrftoken depose par Django ({% csrf_token %} dans base.html)
  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : null;
  }

  async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    if (options.method && options.method !== "GET") {
      headers["X-CSRFToken"] = getCookie("csrftoken");
    }

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: "same-origin",
    });

    if (!response.ok) {
      const error = new Error("api_error");
      error.status = response.status;
      try {
        error.data = await response.json();
      } catch (e) {
        error.data = null;
      }
      throw error;
    }
    return response.json();
  }

  /** GET /api/sessions/<id>/ */
  async function getSession(id) {
    return apiFetch(`/api/sessions/${id}/`);
  }

  /** GET /api/sessions/?page=N -> { count, next, previous, results } */
  async function listSessions(page) {
    return apiFetch(page ? `/api/sessions/?page=${page}` : `/api/sessions/`);
  }

  /** POST /api/sessions/  (multipart: photo | manual_ingredients) */
  async function submitScan({ photoFile, manualIngredients } = {}) {
    const formData = new FormData();
    if (photoFile) formData.append("photo", photoFile);
    if (manualIngredients && manualIngredients.length > 0) {
      formData.append("manual_ingredients", JSON.stringify(manualIngredients));
    }
    return apiFetch(`/api/sessions/`, { method: "POST", body: formData });
  }

  /**
   * Le backend traite tout de maniere synchrone pour l'instant (pas de
   * Celery encore branche), donc la session revenue de submitScan() est
   * deja "done" ou "failed". Cette fonction reste utile si l'async est
   * ajoute plus tard : elle poll tant que le statut n'est pas final.
   */
  async function pollSessionUntilDone(id, onUpdate) {
    let session = await getSession(id);
    onUpdate(session);
    while (session.status === "pending" || session.status === "processing") {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      session = await getSession(id);
      onUpdate(session);
    }
    return session;
  }

  /** POST /api/recipes/<id>/rating/  { value: -1 | 1 | null } */
  async function rateRecipe(recipeId, value) {
    return apiFetch(`/api/recipes/${recipeId}/rating/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
  }

  /** GET /api/profile/ */
  async function getProfile() {
    return apiFetch(`/api/profile/`);
  }

  /** PATCH /api/profile/  { diet, allergies, skill_level, time_available_minutes } */
  async function updateProfile(data) {
    return apiFetch(`/api/profile/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  return {
    getSession,
    listSessions,
    submitScan,
    pollSessionUntilDone,
    rateRecipe,
    getProfile,
    updateProfile,
  };
})();
