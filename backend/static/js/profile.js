(function () {
  const form = document.getElementById("profile-form");
  const dietSelect = document.getElementById("diet-select");
  const skillSelect = document.getElementById("skill-select");
  const timeInput = document.getElementById("time-input");
  const allergyInput = document.getElementById("allergy-input");
  const addAllergyBtn = document.getElementById("add-allergy-btn");
  const allergyTags = document.getElementById("allergy-tags");
  const saveBtn = document.getElementById("profile-save-btn");
  const alertSlot = document.getElementById("profile-alert-slot");

  let allergies = [];

  function renderTags() {
    allergyTags.innerHTML = "";
    allergies.forEach((name, index) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.innerHTML = `${name} <button type="button" aria-label="Retirer ${name}">×</button>`;
      tag.querySelector("button").addEventListener("click", () => {
        allergies.splice(index, 1);
        renderTags();
      });
      allergyTags.appendChild(tag);
    });
  }

  function addAllergy() {
    const value = allergyInput.value.trim();
    if (!value || allergies.includes(value)) return;
    allergies.push(value);
    allergyInput.value = "";
    renderTags();
    allergyInput.focus();
  }

  addAllergyBtn.addEventListener("click", addAllergy);
  allergyInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addAllergy();
    }
  });

  // pre-remplissage depuis le profil existant
  async function loadProfile() {
    try {
      const profile = await CookPilotAPI.getProfile();
      dietSelect.value = profile.diet;
      skillSelect.value = profile.skill_level;
      timeInput.value = profile.time_available_minutes;
      allergies = profile.allergies || [];
      renderTags();
    } catch (err) {
      renderAlert(alertSlot, {
        type: "danger",
        message: "Impossible de charger votre profil.",
        actionLabel: "Réessayer",
        onAction: loadProfile,
      });
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert(alertSlot);

    const minutes = parseInt(timeInput.value, 10);
    if (!minutes || minutes <= 0) {
      renderAlert(alertSlot, {
        type: "warning",
        message: "Indiquez un temps disponible valide (en minutes).",
      });
      return;
    }

    saveBtn.disabled = true;
    saveBtn.textContent = "Enregistrement…";

    try {
      await CookPilotAPI.updateProfile({
        diet: dietSelect.value,
        allergies,
        skill_level: skillSelect.value,
        time_available_minutes: minutes,
      });
      renderAlert(alertSlot, { type: "success", message: "Profil enregistré." });
    } catch (err) {
      renderAlert(alertSlot, {
        type: "danger",
        message: "Impossible d'enregistrer votre profil. Vérifiez votre connexion et réessayez.",
        actionLabel: "Réessayer",
        onAction: () => form.requestSubmit(),
      });
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = "Enregistrer";
    }
  });

  loadProfile();
})();
