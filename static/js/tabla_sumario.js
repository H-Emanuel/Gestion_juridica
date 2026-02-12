$(document).ready(function () {

  // =========================
  // Pendientes (activos)
  // =========================
  const tablePendientes = $('#SumarioTable').DataTable({
    dom: 'frtip',
    language: { url: "/static/js/es-MX.json" },
    processing: true,
    serverSide: true,
    ajax: { url: "/api/sumario/", type: "GET" },
    pageLength: 4,
    order: [[0, "desc"]],
    columns: [
      { data: "id" },
      { data: "Fecha_creacion" },
      { data: "n_da" },
      { data: "fiscal_acargo" },
      {
        data: null,
        orderable: false,
        searchable: false,
        render: function (data, type, row) {
          if (type !== 'display') return null;
          return `
            <a href="/eliminar_sumario/${row.id}/" class="btn btn-rojo btn-tooltip" title="Eliminar" onclick="return confirm('¿Eliminar registro?')">❌</a>
            <a href="/reiterar_oficio/${row.id}/" class="btn btn-azul btn-tooltip" title="Reiterar">🕑</a>
            <a href="#" data-id="${row.id}" class="btn btn-verde btn-tooltip btn-respondido" title="Terminar">✔️</a>
            <a href="#" data-id="${row.id}" class="btn btn-gris btn-tooltip btn-detalle-sumario" title="Detalle">📋</a>
          `;
        }
      }
    ],
    columnDefs: [{ orderable: false, targets: [0] }],
    initComplete: function () {
      setTimeout(function () {
        $('#SumarioTable_filter input').attr('placeholder', 'N° de DA, Fiscal a cargo').css('width', '250px');
      }, 50);
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
