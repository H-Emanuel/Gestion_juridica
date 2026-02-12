// detalle.js
(function () {
  const MODAL_ID = "modal-detalle-Sumario";
  const BODY_ID  = "modal-detalle-sumario-body";

  // 1) Abrir modal al click en el botón Detalle
  $(document).on("click", ".btn-detalle-sumario", function (e) {
    e.preventDefault();

    const id = $(this).data("id");
    if (!id) return;

    const $modal = $("#" + MODAL_ID);
    $modal.attr("data-sumario-id", id);
    $modal.modal("show");

    // pinta loading al tiro
    const body = document.getElementById(BODY_ID);
    if (body) body.innerHTML = `<div class="text-muted">Cargando detalle...</div>`;

    // dispara carga
    document.dispatchEvent(new CustomEvent("registro:detalle:open", { detail: { id } }));
  });

  // 2) Escuchar el evento y cargar el detalle
  document.addEventListener("registro:detalle:open", async (e) => {
    const { id } = e.detail;
    const body = document.getElementById(BODY_ID);
    if (!body) return;

    try {
      const res = await fetch(`/api/sumario/${id}/detalle/`, {
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

  // 3) Render HTML del cuerpo del modal
  function esc(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function badge(text) {
  return `
    <span
      style="
        display:inline-block;
        background:#e9ecef;
        color:#000;
        border:1px solid #ced4da;
        border-radius:6px;
        padding:4px 8px;
        font-size:12px;
        margin-right:6px;
        margin-bottom:4px;
      "
    >
      ${esc(text)}
    </span>
  `;
}


function renderDetalle(d) {
    const asignaciones = Array.isArray(d.asignaciones) ? d.asignaciones : [];
    const docs = Array.isArray(d.documentos) ? d.documentos : [];

    return `
        <div style="color: #000;">
        <div class="row">
            <div class="col-md-6">
            <p><strong>ID:</strong> ${esc(d.id)}</p>
            <p><strong>Fecha creación:</strong> ${esc(d.fecha_creacion || "—")}</p>
            <p><strong>N° DA:</strong> ${esc(d.n_da)}</p>
            <p><strong>Fecha DA:</strong> ${esc(d.fecha_da || "—")}</p>
            </div>
            <div class="col-md-6">
            <p><strong>Fiscal a cargo:</strong> ${esc(d.fiscal_acargo || "—")}</p>
            <p><strong>Grado fiscal:</strong> ${esc(d.grado_fiscal || "—")}</p>
            </div>
        </div>

        <hr>

        <p><strong>Materia:</strong></p>
        <div style="border: 1px solid #ced4da; padding: 10px; border-radius: 5px; background-color: #f8f9fa;">
            ${esc(d.materia)}
        </div>

        <hr>

        <p><strong>Nombre y apellido del imputado:</strong></p>
        <div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Grado</th>
                        <th>Nombre</th>
                    </tr>
                </thead>
                <tbody>
                    ${d.nombre_apellido_grado_imputado.map(item => `
                        <tr>
                            <td>${esc(item.grado)}</td>
                            <td>${esc(item.nombre)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>

        <hr>

        <p><strong>Oficio fiscalía:</strong> ${esc(d.oficio_fiscalia || "—")}</p>
        <p><strong>Fecha fiscalía:</strong> ${esc(d.fecha_fiscalia || "—")}</p>
        <p><strong>Adjunto fiscalía:</strong> ${d.adjunto_fiscalia ? `<a href="${esc(d.adjunto_fiscalia)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

        <hr>

        <p><strong>Oficio jurídico:</strong> ${esc(d.oficio_juridico || "—")}</p>
        <p><strong>Fecha jurídico:</strong> ${esc(d.fecha_juridico || "—")}</p>
        <p><strong>Adjunto jurídico:</strong> ${d.adjunto_juridico ? `<a href="${esc(d.adjunto_juridico)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

        <hr>

        <p><strong>Sanción:</strong> ${esc(d.sancion || "—")}</p>
        <p><strong>Adjunto sanción:</strong> ${d.adjunto_sancion ? `<a href="${esc(d.adjunto_sancion)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

        <hr>

        <p><strong>Fecha contrata:</strong> ${esc(d.fecha_contrata || "—")}</p>
        <p><strong>Finalizado:</strong> ${d.finalizado ? "Sí ✅" : "No ❌"}</p>
        </div>
    `;
}
})();
