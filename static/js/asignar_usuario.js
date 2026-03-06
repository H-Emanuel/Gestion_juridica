// detalle.js
(function () {
  const MODAL_ID = "modal-Seleccionar";
  const BODY_ID  = "modal-detalle-seleccionar-body";

  // 1) Abrir modal al click en el botón Asignar
  $(document).on("click", ".btn-asignar", function (e) {
    e.preventDefault();

    const id = $(this).data("id");
    if (!id) return;

    const $modal = $("#" + MODAL_ID);
    $modal.attr("data-registro-id", id);
    $modal.attr("data-funcionario", $(this).data("funcionario") || "");

    $modal.modal("show");

    // pinta loading al tiro
    const body = document.getElementById(BODY_ID);
    if (body) body.innerHTML = `<div class="text-muted">Cargando usuarios...</div>`;

    // dispara carga
    document.dispatchEvent(new CustomEvent("registro:usuarios:open", { detail: { id } }));
  });

$(document).on("registro:usuarios:open", async function (e) {
    const { id } = e.detail;
    const body = document.getElementById(BODY_ID);
    if (!body) return;

    try {
        const res = await fetch(`api/usuarios/`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        body.innerHTML = renderDetalle(data);

    } catch (err) {
        console.error(err);
        body.innerHTML = `
            <div class="alert alert-danger" style="margin:0;">
                No se pudo cargar el detalle del registro.
            </div>
        `;
    }
});

    function renderDetalle(usuarios) {
        if (!usuarios || usuarios.length === 0) {
            return `<div class="alert alert-info">No hay usuarios disponibles.</div>`;
        }

        const options = usuarios
            .map(u => `<option value="${u.id}">${u.username} (${u.email})</option>`)
            .join("");

        return `
            <div class="form-group">
                <label for="usuario-select">Seleccionar Usuario</label>
                <select id="usuario-select" class="form-control">
                    <option value="">-- Selecciona un usuario --</option>
                    ${options}
                </select>
            </div>
            <br>
            <button type="button" class="btn btn-primary" id="btn-confirmar-asignar">
                Asignar
            </button>
        `;
    }

    $(document).on("click", "#btn-confirmar-asignar", function () {
        const usuarioId = document.getElementById("usuario-select").value;
        const registroId = $("#" + MODAL_ID).attr("data-registro-id");

        if (!usuarioId) {
            alert("Selecciona un usuario");
            return;
        }

        fetch(`api/asignar/`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest" 
            },
            body: JSON.stringify({ registro_id: registroId, usuario_id: usuarioId })
        })
        .then(res => res.ok ? res.json() : Promise.reject(`HTTP ${res.status}`))
        .then(() => {
            $("#" + MODAL_ID).modal("hide");
            location.reload();
        })
        .catch(err => console.error(err));
    });

})();
