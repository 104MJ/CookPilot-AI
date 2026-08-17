(function () {
  const scene = document.getElementById("fridge-scene");
  if (!scene) return;
  const door = document.getElementById("fridge-door");

  function open() {
    door.classList.add("is-closing");
    setTimeout(function () {
      scene.classList.add("is-open");
    }, 220);
  }

  door.addEventListener("click", open);
  door.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      open();
    }
  });
})();
