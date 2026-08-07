/**
 * Mock API layer — matches the shape of ai_engine.models.History /
 * ai_engine.models.Recipe as of the "dee10d6" commit on main.
 *
 * Every function here returns a Promise, same as a real `fetch(...).then(r => r.json())`
 * would. Once Membre 1 exposes the real DRF endpoints, swap the body of each
 * function for the commented-out fetch call — call sites (scan.js, history.js,
 * result rendering) do not need to change.
 *
 * Sessions are persisted in localStorage (not just an in-memory object):
 * scan.html and result.html are separate page loads (no SPA router yet), so
 * an in-memory store would reset between "submit scan" and "view result".
 * localStorage survives navigation and stands in for the real backend's DB.
 *
 * Contract:
 *   Session (History):
 *     { id, status: "pending"|"processing"|"done"|"failed",
 *       photo_url, error_message,
 *       detected_ingredients: [{ name, expires_at }],
 *       manual_ingredients: [{ name, expires_at }],
 *       created_at,
 *       recipes: [Recipe] }
 *
 *   Recipe:
 *     { id, title, ingredients_used: [string], ingredients_missing: [string],
 *       steps: [string], rating: -1|1|null,
 *       total_calories, nutrition_breakdown: { protein_g, carbs_g, fat_g, fiber_g } }
 */

const CookPilotAPI = (function () {
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const STORAGE_KEY = "cookpilot-mock-store";

  const SEED_SESSIONS = {
    1: {
      id: 1,
      status: "done",
      photo_url: null,
      error_message: "",
      detected_ingredients: [
        { name: "tomate", expires_at: "2026-08-10" },
        { name: "oeuf", expires_at: "2026-08-15" },
        { name: "oignon", expires_at: null },
        { name: "fromage râpé", expires_at: "2026-08-09" },
      ],
      manual_ingredients: [{ name: "basilic", expires_at: null }],
      created_at: "2026-08-05T18:32:00Z",
      recipes: [
        {
          id: 10,
          title: "Omelette tomate-fromage anti-gaspi",
          ingredients_used: ["tomate", "oeuf", "oignon", "fromage râpé", "basilic"],
          ingredients_missing: [],
          steps: [
            "Émincer l'oignon et couper les tomates en dés.",
            "Faire revenir l'oignon 3 min dans une poêle huilée.",
            "Ajouter les tomates, cuire 2 min.",
            "Battre les oeufs, verser dans la poêle, parsemer de fromage.",
            "Cuire 4 à 5 min à feu doux, plier l'omelette et servir avec le basilic.",
          ],
          rating: null,
          total_calories: 420,
          nutrition_breakdown: { protein_g: 24, carbs_g: 12, fat_g: 30, fiber_g: 3 },
        },
      ],
    },
    2: {
      id: 2,
      status: "failed",
      photo_url: null,
      error_message: "Le moteur de vision n'a détecté aucun ingrédient exploitable sur cette photo.",
      detected_ingredients: [],
      manual_ingredients: [],
      created_at: "2026-08-04T09:12:00Z",
      recipes: [],
    },
  };

  function loadStore() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (err) {
      // corrupted storage — fall through and reseed
    }
    const fresh = { sessions: structuredClone(SEED_SESSIONS), nextId: 100 };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));
    return fresh;
  }

  function saveStore(store) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  }

  /** GET /api/sessions/<id>/ */
  async function getSession(id) {
    await delay(300);
    const store = loadStore();
    const session = store.sessions[id];
    if (!session) {
      const error = new Error("not_found");
      error.status = 404;
      throw error;
    }
    return structuredClone(session);
  }

  /** GET /api/sessions/ */
  async function listSessions() {
    await delay(300);
    const store = loadStore();
    return Object.values(store.sessions).sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
  }

  /**
   * POST /api/sessions/  (multipart: photo | manual_ingredients)
   * Simulates the async pipeline: pending -> processing -> done/failed.
   * `simulateFailure` lets the UI be tested against quota/detection errors
   * without waiting for the real backend.
   */
  async function submitScan({ photoFile, manualIngredients } = {}) {
    await delay(400);
    const store = loadStore();
    const id = store.nextId++;
    const session = {
      id,
      status: "pending",
      // A real backend returns a permanent media URL here. `URL.createObjectURL`
      // blob URLs die with the page that created them, so they can't survive
      // the navigation to result.html — left null until the real upload exists.
      photo_url: null,
      error_message: "",
      detected_ingredients: [],
      manual_ingredients: (manualIngredients || []).map((name) => ({ name, expires_at: null })),
      created_at: new Date().toISOString(),
      recipes: [],
    };
    store.sessions[id] = session;
    saveStore(store);
    return structuredClone(session);
  }

  /**
   * Simulates the backend moving a session through its states, calling
   * `onUpdate(session)` at each step — this is what a poll loop (or later,
   * a real SSE/WebSocket stream for LLM tokens) will drive.
   */
  async function pollSessionUntilDone(id, onUpdate, { simulateFailure } = {}) {
    const store = loadStore();
    const session = store.sessions[id];

    await delay(900);
    session.status = "processing";
    saveStore(store);
    onUpdate(structuredClone(session));

    await delay(1200);

    if (simulateFailure === "quota") {
      session.status = "failed";
      session.error_message = "Quota de l'API IA dépassé. Réessayez dans quelques minutes.";
      saveStore(store);
      onUpdate(structuredClone(session));
      return structuredClone(session);
    }

    if (simulateFailure === "detection") {
      session.status = "failed";
      session.error_message = "Aucun ingrédient reconnaissable sur cette photo. Essayez la saisie manuelle.";
      saveStore(store);
      onUpdate(structuredClone(session));
      return structuredClone(session);
    }

    // Pas de vraie vision cote client : si des ingredients manuels ont ete
    // saisis on s'en sert tels quels ; sinon (photo seule) on simule une
    // detection en tirant un sous-ensemble aleatoire d'un pool d'ingredients
    // courants, plutot qu'une paire fixe qui reviendrait a chaque fois.
    if (session.manual_ingredients.length === 0) {
      session.detected_ingredients = simulateDetection();
    }
    session.status = "done";
    session.recipes = [buildMockRecipe(session, store.nextId + 900)];
    saveStore(store);
    onUpdate(structuredClone(session));
    return structuredClone(session);
  }

  const COMMON_INGREDIENT_POOL = [
    "tomate",
    "oeuf",
    "oignon",
    "poivron",
    "courgette",
    "carotte",
    "fromage râpé",
    "riz",
    "pâtes",
    "poulet",
    "champignon",
    "épinard",
  ];

  function simulateDetection() {
    const shuffled = [...COMMON_INGREDIENT_POOL].sort(() => Math.random() - 0.5);
    const count = 2 + Math.floor(Math.random() * 2); // 2 ou 3 ingredients
    return shuffled.slice(0, count).map((name) => ({ name, expires_at: null }));
  }

  /**
   * Builds a recipe title/steps from whatever ingredients the session
   * actually has (detected + manual), instead of a fixed dish — so testing
   * the scan form with different ingredients gives a different result.
   * `ingredients_used` matches the real API shape: [{ name, quantity }].
   */
  function buildMockRecipe(session, recipeId) {
    const names = [
      ...session.detected_ingredients.map((i) => i.name),
      ...session.manual_ingredients.map((i) => i.name),
    ];
    const pool = names.length > 0 ? names : ["ingrédients du frigo"];
    const title =
      pool.length >= 2 ? `Poêlée de ${pool[0]} et ${pool[1]}` : `Recette rapide au ${pool[0]}`;

    return {
      id: recipeId,
      title,
      ingredients_used: pool.map((name) => ({ name, quantity: "" })),
      ingredients_missing: [],
      steps: [
        `Laver et préparer : ${pool.join(", ")}.`,
        "Faire chauffer un filet d'huile dans une poêle.",
        `Faire revenir ${pool.join(", ")} pendant 8 à 10 minutes à feu moyen.`,
        "Assaisonner selon votre goût et servir chaud.",
      ],
      rating: null,
      total_calories: null,
      nutrition_breakdown: {},
    };
  }

  /** POST /api/recipes/<id>/rating/  { value: -1 | 1 } */
  async function rateRecipe(recipeId, value) {
    await delay(250);
    const store = loadStore();
    for (const session of Object.values(store.sessions)) {
      const recipe = session.recipes.find((r) => r.id === recipeId);
      if (recipe) {
        recipe.rating = value;
        saveStore(store);
        return structuredClone(recipe);
      }
    }
    throw new Error("recipe_not_found");
  }

  return { getSession, listSessions, submitScan, pollSessionUntilDone, rateRecipe };
})();
