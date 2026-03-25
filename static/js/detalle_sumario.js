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
  const reiteraciones = Array.isArray(d.reiteraciones) ? d.reiteraciones : [];
  const documentos = Array.isArray(d.documentos) ? d.documentos : [];

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
          ${(d.nombre_apellido_grado_imputado || []).map(item => `
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

    <p><strong>Notificación fiscal:</strong> ${esc(d.fecha_notificacion_fiscal || "—")}</p>
    <p><strong>Adjunto notificación:</strong> ${d.adjunto_not_fiscalia ? `<a href="${esc(d.adjunto_not_fiscalia)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

    <hr>

    <p><strong>Fecha DAJ:</strong> ${esc(d.fecha_daj || "—")}</p>
    <p><strong>Adjunto DAJ:</strong> ${d.adjunto_daj ? `<a href="${esc(d.adjunto_daj)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

    <hr>

    <p><strong>Sanción:</strong> ${esc(d.sancion || "—")}</p>
    <p><strong>Adjunto sanción:</strong> ${d.adjunto_sancion ? `<a href="${esc(d.adjunto_sancion)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

    <hr>

    <p><strong>Oficio:</strong> ${esc(d.oficio_fecha || "—")}</p>
    <p><strong>Adjunto oficio:</strong> ${d.oficio_adjunto ? `<a href="${esc(d.oficio_adjunto)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>

    <hr>

    <p><strong>Etapa:</strong> ${esc(d.etapa || "—")}</p>
    <p><strong>Respuesta:</strong> ${esc(d.respuesta || "—")}</p>

    <hr>

    <p><strong>Documentos:</strong></p>
    ${documentos.length ? `
      <table class="table table-sm">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Fecha</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          ${documentos.map(doc => `
            <tr>
              <td>${esc(doc.nombre)}</td>
              <td>${esc(doc.fecha_subida || "—")}</td>
              <td>${doc.archivo ? `<a href="${esc(doc.archivo)}" target="_blank">Descargar</a>` : "—"}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    ` : `<p style="color: #999;">Sin documentos</p>`}

    <hr>

    <p><strong>Reiteraciones:</strong></p>
    ${reiteraciones.length ? `
      <div>
        ${reiteraciones.map((r, i) => `
          <div style="border: 1px solid #dee2e6; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
            <p><strong>Etapa:</strong> ${esc(r.etapa || "—")}</p>
            <p><strong>Fecha envío:</strong> ${esc(r.fecha_de_envio || "—")}</p>
            <p><strong>Correos:</strong> ${esc(r.correos || "—")}</p>
            <p><strong>Respuesta:</strong> ${esc(r.respuesta || "—")}</p>
          </div>
        `).join('')}
      </div>
    ` : `<p style="color: #999;">Sin reiteraciones</p>`}

    <hr>

    <p><strong>Fecha contrata:</strong> ${esc(d.fecha_contrata || "—")}</p>
    <p><strong>Archivo final:</strong> ${d.archivo_final ? `<a href="${esc(d.archivo_final)}" target="_blank">Ver archivo</a>` : "Sin archivo adjunto"}</p>
    <p><strong>Finalizado:</strong> ${d.finalizado ? "Sí ✅" : "No ❌"}</p>
    </div>
  `;
}
})();
