document.querySelectorAll('.attach-col').forEach(col => {
    const attachBtn = col.querySelector('.btn-attach');
    const changeBtn = col.querySelector('.btn-change');
    const input = col.querySelector('input[type="file"]');
    const status = col.querySelector('.upload-status');
    const fileNameEl = col.querySelector('.file-name');

    const openPicker = () => input.click();

    if (attachBtn) attachBtn.addEventListener('click', openPicker);
    if (changeBtn) changeBtn.addEventListener('click', openPicker);

    if (input) {
      input.addEventListener('change', () => {
        const file = input.files && input.files[0];

      if (file) {
        // Mostrar visto + nombre
        fileNameEl.textContent = file.name;
        status.hidden = false;

        // Mostrar botón "Cambiar"
        changeBtn.hidden = false;

        // (Opcional) cambiar texto del botón principal
        attachBtn.textContent = "📎 Adjuntado";
      } else {
        // Si no hay archivo (por ejemplo canceló)
        status.hidden = true;
        changeBtn.hidden = true;
        fileNameEl.textContent = "";
        attachBtn.textContent = "📎 Adjuntar";
      }
      });
    }
  });

  (function () {
    function initFileAttach(root) {
      const input = root.querySelector(".file-attach__input");
      const btnSelect = root.querySelector(".file-attach__btn--select");
      const btnChange = root.querySelector(".file-attach__btn--change");
      const fileNameEl = root.querySelector(".file-attach__filename");

      if (!input || !btnSelect || !btnChange || !fileNameEl) return;

      // Si quieres asegurar que el name venga de data-name
      const dataName = root.getAttribute("data-name");
      if (dataName && !input.name) input.name = dataName;

      function openPicker() {
        input.click();
      }

      function updateUI() {
        const file = input.files && input.files[0];
        if (file) {
          root.classList.add("is-ok");
          fileNameEl.textContent = file.name;
        } else {
          root.classList.remove("is-ok");
          fileNameEl.textContent = "";
        }
      }

      btnSelect.addEventListener("click", openPicker);
      btnChange.addEventListener("click", openPicker);
      input.addEventListener("change", updateUI);

      // estado inicial
      updateUI();
    }

    // Inicializa todos los que existan en la página
    document.querySelectorAll(".file-attach").forEach(initFileAttach);
  })();

document.getElementById('btn-add-inculpado').addEventListener('click', () => {
    const container = document.getElementById('inculpados-container');
    const newRow = container.querySelector('.row').cloneNode(true);
    newRow.querySelectorAll('input').forEach(input => input.value = '');
    newRow.querySelector('.btn-remove').style.display = 'block';
    newRow.querySelector('.btn-remove').addEventListener('click', () => newRow.remove());
    container.appendChild(newRow);
});