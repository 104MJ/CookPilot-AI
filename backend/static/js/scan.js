(function () {
  const form = document.getElementById("scan-form");
  const uploadZone = document.getElementById("upload-zone");
  const uploadZoneText = document.getElementById("upload-zone-text");
  const photoInput = document.getElementById("photo-input");
  const preview = document.getElementById("upload-preview");
  const ingredientInput = document.getElementById("ingredient-input");
  const addIngredientBtn = document.getElementById("add-ingredient-btn");
  const tagsContainer = document.getElementById("ingredient-tags");
  const submitBtn = document.getElementById("submit-btn");
  const errorSlot = document.getElementById("scan-error-slot");
  const mockFailureSelect = document.getElementById("mock-failure");

  let selectedFile = null;
  const manualIngredients = [];

  function openFilePicker() {
    photoInput.click();
  }

  function setFile(file) {
    if (!file) return;
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.style.display = "block";
      uploadZoneText.textContent = file.name;
    };
    reader.readAsDataURL(file);
  }

  uploadZone.addEventListener("click", openFilePicker);
  uploadZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openFilePicker();
    }
  });
  photoInput.addEventListener("change", (e) => setFile(e.target.files[0]));

  ["dragenter", "dragover"].forEach((evt) =>
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.add("is-dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    uploadZone.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadZone.classList.remove("is-dragover");
    })
  );
  uploadZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  function renderTags() {
    tagsContainer.innerHTML = "";
    manualIngredients.forEach((name, index) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.innerHTML = `${name} <button type="button" aria-label="Retirer ${name}">×</button>`;
      tag.querySelector("button").addEventListener("click", () => {
        manualIngredients.splice(index, 1);
        renderTags();
      });
      tagsContainer.appendChild(tag);
    });
  }

  function addIngredient() {
    const value = ingredientInput.value.trim();
    if (!value) return;
    manualIngredients.push(value);
    ingredientInput.value = "";
    renderTags();
    ingredientInput.focus();
  }

  addIngredientBtn.addEventListener("click", addIngredient);
  ingredientInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addIngredient();
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert(errorSlot);

    if (!selectedFile && manualIngredients.length === 0) {
      renderAlert(errorSlot, {
        type: "warning",
        message: "Ajoutez une photo ou au moins un ingrédient manuel avant de continuer.",
      });
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Envoi en cours…";

    try {
      const session = await CookPilotAPI.submitScan({
        photoFile: selectedFile,
        manualIngredients,
      });
      const simulateFailure = mockFailureSelect.value || undefined;
      const url = simulateFailure
        ? `/sessions/${session.id}/?mock=${simulateFailure}`
        : `/sessions/${session.id}/`;
      window.location.href = url;
    } catch (err) {
      renderAlert(errorSlot, {
        type: "danger",
        message: "Impossible d'envoyer votre demande. Vérifiez votre connexion et réessayez.",
        actionLabel: "Réessayer",
        onAction: () => form.requestSubmit(),
      });
      submitBtn.disabled = false;
      submitBtn.textContent = "Analyser mes ingrédients";
    }
  });
})();
