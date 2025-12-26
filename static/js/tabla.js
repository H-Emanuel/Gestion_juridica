$(document).ready(function () {

  // =========================
  // Pendientes (activos)
  // =========================
  const tablePendientes = $('#registrosTable').DataTable({
    dom: 'frtip',
    language: { url: "/static/js/es-MX.json" },
    processing: true,
    serverSide: true,
    ajax: { url: "/api/registros/", type: "GET" },
    pageLength: 6,
    order: [[0, "desc"]],
    columns: [
      { data: "folio" },
      { data: "oficio" },
      {
        data: "asignaciones",
        render: function (data, type, row) {
          if (type !== "display") {
            // Para orden/búsqueda devolvemos texto plano
            if (Array.isArray(data)) return data.join(", ");
            return data || "";
          }

          const asignaciones = Array.isArray(data) ? data : [];
          if (!asignaciones.length) return `<span class="text-muted">Sin asignación</span>`;

          const max = 3; // cuántas muestras antes de resumir
          const visibles = asignaciones.slice(0, max);
          const restantes = asignaciones.length - visibles.length;

          const chip = (txt) => `
            <span style="
              display:inline-block;
              background:#e9ecef;
              color:#000;
              border:1px solid #ced4da;
              border-radius:6px;
              padding:2px 6px;
              font-size:12px;
              margin-right:6px;
              margin-bottom:4px;
              white-space:nowrap;
            ">${String(txt)
                .replaceAll("&","&amp;")
                .replaceAll("<","&lt;")
                .replaceAll(">","&gt;")
                .replaceAll('"',"&quot;")
                .replaceAll("'","&#039;")
            }</span>
          `;

          let html = visibles.map(chip).join("");
          if (restantes > 0) html += `<span class="text-muted">+${restantes}</span>`;

          return html;
        }
      },
      { data: "fecha_oficio" },
      { data: "fecha_respuesta" },
      {
        data: "dias_transcurridos",
        render: function (data, type) {
          if (type !== 'display') return data;
          if (data === null || data === undefined || data === "") return "—";
          const clase = (data >= 3) ? "bg-success" : "bg-danger";
          return `<span class="badge ${clase}">${data} días</span>`;
        }
      },
      {
        data: null,
        orderable: false,
        searchable: false,
        render: function (data, type, row) {
          if (type !== 'display') return null;
          return `
            <a href="/eliminar/${row.id}/" class="btn btn-rojo btn-tooltip" title="Eliminar" onclick="return confirm('¿Eliminar registro?')">❌</a>
            <a href="/editar/${row.id}/" class="btn btn-naranja btn-tooltip" title="Editar">✏️</a>
            <a href="/reiterar_oficio/${row.id}/" class="btn btn-azul btn-tooltip" title="Reiterar">🕑</a>
            <a href="#" data-id="${row.id}" class="btn btn-verde btn-tooltip btn-respondido" title="Terminar">✔️</a>
            <a href="#" data-id="${row.id}" class="btn btn-gris btn-tooltip btn-detalle" title="Detalle">📋</a>
          `;
        }
      }
    ],
    columnDefs: [{ orderable: false, targets: [6] }],
    initComplete: function () {
      setTimeout(function () {
        $('#registrosTable_filter input').attr('placeholder', 'folio, oficio o materia');
      }, 50);
    }
  });

  // =========================
  // Histórico (terminados)
  // =========================
  const tableHistorico = $('#historicoTable').DataTable({
    dom: 'frtip',
    language: { url: "/static/js/es-MX.json" },
    processing: true,
    serverSide: true,
    ajax: { url: "/api/historico/", type: "GET" }, // ✅ tu ruta real
    pageLength: 6,
    order: [[4, "desc"]], // fecha_respuesta desc (si viene)
    columns: [
      { data: "folio" },
      { data: "oficio" },
      {
        data: "asignaciones",
        render: function (data, type, row) {
          if (type !== "display") {
            // Para orden/búsqueda devolvemos texto plano
            if (Array.isArray(data)) return data.join(", ");
            return data || "";
          }

          const asignaciones = Array.isArray(data) ? data : [];
          if (!asignaciones.length) return `<span class="text-muted">Sin asignación</span>`;

          const max = 3; // cuántas muestras antes de resumir
          const visibles = asignaciones.slice(0, max);
          const restantes = asignaciones.length - visibles.length;

          const chip = (txt) => `
            <span style="
              display:inline-block;
              background:#e9ecef;
              color:#000;
              border:1px solid #ced4da;
              border-radius:6px;
              padding:2px 6px;
              font-size:12px;
              margin-right:6px;
              margin-bottom:4px;
              white-space:nowrap;
            ">${String(txt)
                .replaceAll("&","&amp;")
                .replaceAll("<","&lt;")
                .replaceAll(">","&gt;")
                .replaceAll('"',"&quot;")
                .replaceAll("'","&#039;")
            }</span>
          `;

          let html = visibles.map(chip).join("");
          if (restantes > 0) html += `<span class="text-muted">+${restantes}</span>`;

          return html;
        }
      },
      { data: "fecha_oficio" },
      { data: "fecha_respuesta" },
      {
        data: null,
        orderable: false,
        searchable: false,
        render: function (data, type, row) {
          if (type !== 'display') return null;
          return `
            <a href="#" data-id="${row.id}" class="btn btn-gris btn-tooltip btn-detalle" title="Detalle">📋</a>
          `;
        }
      }
    ],
    initComplete: function () {
      setTimeout(function () {
        $('#historicoTable_filter input').attr('placeholder', 'folio, oficio o materia');
      }, 50);
    }
  });


  // =========================
  // Toggle entre tablas
  // =========================
  $('#tablaSelector').on('change', function () {
    const val = $(this).val();

    if (val === 'pendientes') {
        $('#wrapHistorico').addClass('d-none');
        $('#wrapPendientes').removeClass('d-none');

        tablePendientes.columns.adjust().draw(false);
        highlightPendientes(); // ✅ fuerza highlight en la visible
    } else {
        $('#wrapPendientes').addClass('d-none');
        $('#wrapHistorico').removeClass('d-none');

        tableHistorico.columns.adjust().draw(false);
        highlightHistorico(); // ✅ fuerza highlight en la visible
    }
    });

  // =========================
    // Highlight genérico para cualquier DataTable
    // =========================
    function setupHighlight(tableInstance, tableId, highlightColumns) {
    const filterSelector = `#${tableId}_filter input`;
    const tbodySelector  = `#${tableId} tbody`;

    function highlightSearch() {
        const searchText = ($(filterSelector).val() || '').trim().toLowerCase();

        if (!searchText) {
        $(`${tbodySelector} td`).removeClass('highlight-cell');
        return;
        }

        $(`${tbodySelector} tr`).each(function () {
        const cells = $(this).find('td');

        highlightColumns.forEach(function (index) {
            const cell = cells.eq(index);
            const text = cell.text().toLowerCase();

            if (text.includes(searchText)) cell.addClass('highlight-cell');
            else cell.removeClass('highlight-cell');
        });
        });
    }

    // al escribir en el buscador de ESA tabla
    $(document).on('keyup', filterSelector, function () {
        setTimeout(highlightSearch, 150);
    });

    // al redibujar ESA tabla (paginación, orden, ajax)
    tableInstance.on('draw.dt', function () {
        highlightSearch();
    });

    // devuelve la función para poder invocarla cuando cambies de tabla
    return highlightSearch;
    }

    // CSS (una vez)
    $('<style>')
    .prop('type', 'text/css')
    .html('.highlight-cell { background-color: #b7e4c7 !important; font-weight: bold !important; }')
    .appendTo('head');

    // Activar highlight para cada tabla (elige columnas)
    const highlightPendientes = setupHighlight(tablePendientes, 'registrosTable', [0, 1, 2]); // folio, oficio, materia
    const highlightHistorico  = setupHighlight(tableHistorico,  'historicoTable', [0, 1, 2]); // folio, oficio, materia


  // =========================
  // Al terminar oficio: recarga pendientes y (opcional) histórico
  // =========================
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  $('#registrosTable').on('click', '.btn-respondido', function (e) {
    e.preventDefault();

    const $btn = $(this);
    const id = $btn.data('id');

    // Abre el modal (cambia #miModalResponder por tu ID real)
    $('#miModalResponder').modal('show');
    
    // Guarda el ID en el modal para usarlo después
    $('#miModalResponder').data('registro-id', id);

    
  });

  // =========================
// Resaltado de búsqueda
// =========================
function highlightSearch() {
    const searchText = $('#registrosTable_filter input').val().trim().toLowerCase();

    if (!searchText) {
        $('#registrosTable tbody td').removeClass('highlight-cell');
        return;
    }

    const highlightColumns = [0, 1, 2]; // folio, oficio, materia

    $('#registrosTable tbody tr').each(function () {
        const cells = $(this).find('td');

        highlightColumns.forEach(function (index) {
            const cell = cells.eq(index);
            const text = cell.text().toLowerCase();

            if (text.includes(searchText)) {
                cell.addClass('highlight-cell');
            } else {
                cell.removeClass('highlight-cell');
            }
        });
    });
}



});
