// detalle.js
(function () {
  const MODAL_ID = "modal-detalle-registro";
  const BODY_ID  = "modal-detalle-registro-body";

  // 1) Abrir modal al click en el botón Detalle
  $(document).on("click", ".btn-detalle", function (e) {
    e.preventDefault();

    const id = $(this).data("id");
    if (!id) return;

    const $modal = $("#" + MODAL_ID);
    $modal.attr("data-registro-id", id);
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
      const res = await fetch(`/api/registro/${id}/detalle/`, {
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

    const respuestaJ = d.respuesta_juridica; // puede ser null

    const reiteraciones = Array.isArray(d.reiteraciones) ? d.reiteraciones : [];

    return `
      <div style="color: #000;">
      <div class="row">
      <div class="col-md-6">
      <p><strong>Folio:</strong> ${esc(d.folio)}</p>
      <p><strong>Oficio:</strong> ${esc(d.oficio)}</p>
      <p><strong>Fecha oficio:</strong> ${esc(d.fecha_oficio)}</p>
      <p><strong>Fecha Respuesta Prevista:</strong> ${esc(d.fecha_respuesta || "—")}</p>
      </div>
      <div class="col-md-6">
      <p><strong>Dirigido a:</strong> ${esc(d.dirigido_a || "—")}</p>
      <p><strong>CC:</strong> ${esc(d.cc || "—")}</p>
      <p><strong>Días transcurridos:</strong> ${esc(d.dias_transcurridos)}</p>
      <p><strong>Estado:</strong> ${d.terminado ? "Terminado ✅" : "Pendiente ⏳"}</p>
      </div>
      </div>

      <hr>

      <p><strong>Materia:</strong></p>
      <div style="white-space:pre-wrap;">${esc(d.materia)}</div>

      <hr>

      <p><strong>Asignaciones:</strong></p>
      <div>
      ${asignaciones.length ? asignaciones.map(badge).join("") : `<span class="text-muted">Sin asignación</span>`}
      </div>

      <hr>

      <p><strong>Respuesta:</strong></p>
      <div style="white-space:pre-wrap;">${esc(d.respuesta || "—")}</div>

      <hr>

      <p><strong>Respuesta jurídica:</strong></p>
      ${
      respuestaJ
      ? ` 
        <p><strong>Fecha término:</strong> ${esc(respuestaJ.fecha_termino || "—")}</p>
        <p><strong>Respuesta:</strong></p>
        <div style="white-space:pre-wrap;">${esc(respuestaJ.respuesta || "—")}</div>
        ${
        respuestaJ.archivo
        ? `<p style="margin-top:10px;"><a class="btn btn-azul" href="${esc(respuestaJ.archivo)}" target="_blank">📎 Ver archivo</a></p>`
        : `<p class="text-muted">Sin archivo adjunto</p>`
        }
      `
      : `<p class="text-muted">No hay respuesta jurídica asociada.</p>`
      }

      <hr>

      <p><strong>Reiteraciones:</strong></p>
      ${
      reiteraciones.length
      ? `
        <ul style="padding-left:18px;">
        ${reiteraciones.map(reitero => `
        <li>
          <strong>Fecha de envío:</strong> ${esc(reitero.fecha_de_envio || "—")}<br>
          <strong>Respuesta:</strong> ${esc(reitero.respuesta || "—")}<br>
          <strong>Correos:</strong> ${esc(reitero.correos || "—")}<br>
          <strong>Copias:</strong> ${esc(reitero.copias_correos || "—")}<br>
          ${reitero.archivos.length ? `
          <strong>Archivos:</strong>
          <ul>
            ${reitero.archivos.map(archivo => `
            <li><a href="${esc(archivo.archivo)}" target="_blank">Descargar archivo</a></li>
            `).join("")}
          </ul>
          ` : `<p class="text-muted">Sin archivos.</p>`}
        </li>
        `).join("")}
        </ul>
      `
      : `<p class="text-muted">Sin reiteraciones.</p>`
      }

      <hr>

      <p><strong>Documentos:</strong></p>
      ${
      docs.length
      ? `
        <ul style="padding-left:18px;">
        ${docs.map(doc => `
        <li>
        ${esc(doc.nombre || "Documento")}
        ${doc.archivo ? ` - <a href="${esc(doc.archivo)}" target="_blank">descargar</a>` : ""} 
        ${doc.fecha_subida ? ` <small class="text-muted">(${esc(doc.fecha_subida)})</small>` : ""}
        </li>
        `).join("")}
        </ul>
      `
      : `<p class="text-muted">Sin documentos.</p>`
      }
      </div>
    `;
  }
})();
