$(document).ready(function () {

    // Placeholder del buscador
    setTimeout(function () {
        $('.dataTables_filter input').attr(
            'placeholder',
            'folio, oficio o materia'
        );
    }, 500);

let table = $('#registrosTable').DataTable({
    dom: 'frtip',
    language: { url: "/static/js/es-MX.json" },
    processing: true,
    serverSide: true,
    ajax: {
        url: "/api/registros/",
        type: "GET",
    },
    pageLength: 6,
    order: [[0, "desc"]],
    columns: [
        { data: "folio" },            // 0
        { data: "oficio" },           // 1
        {
            data: "materia",          // 2
            render: function (data, type, row) {
                if (!data) return "";
                if (type !== 'display') return data;
                return data.length > 40 ? data.substring(0, 40) + "..." : data;
            }
        },
        { data: "fecha_oficio" },     // 3
        { data: "fecha_respuesta" },  // 4
        {
            data: "dias_transcurridos", // 5
            render: function (data, type, row) {
                if (type !== 'display') return data;
                if (!data && data !== 0) return "—";
                let clase = (data >= 3) ? "bg-success" : "bg-danger";
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
                    <a href="/eliminar/${row.id}/" class="btn btn-rojo btn-tooltip" title="Eliminar oficio jurídico" onclick="return confirm('¿Eliminar registro?')">❌​</a>
                    <a href="/editar/${row.id}/" class="btn btn-naranja btn-tooltip" title="Editar oficio jurídico">✏️​</a>
                    <a href="/reiterar_oficio/${row.id}/" class="btn btn-azul btn-tooltip" title="Reiterar oficio jurídico">🕑​</a>
                    <a href="/reiterar_oficio/${row.id}/" class="btn btn-verde btn-tooltip" title=" oficio jurídico">✔️​​</a>
                `;
            }
        }
    ],
    columnDefs: [
        { orderable: false, targets: [6] }  // solo acciones
    ]
});

    // === Resaltado de búsqueda (oficio y materia) ===

    function highlightSearch() {
        let searchText = $('.dataTables_filter input').val().trim().toLowerCase();

        if (searchText.length === 0) {
            $('#registrosTable tbody td').removeClass('highlight-cell');
            return;
        }

        const highlightColumns = [0, 1,2]; // los índices que quieres revisar

        $('#registrosTable tbody tr').each(function () {
            let cells = $(this).find('td');

            highlightColumns.forEach(function(index) {
                let cell = cells.eq(index);
                let text = cell.text().toLowerCase();

                if (text.includes(searchText)) {
                    cell.addClass('highlight-cell');
                } else {
                    cell.removeClass('highlight-cell');
                }
            });
        });
    }


    $('.dataTables_filter input').on('keyup', function () {
        setTimeout(highlightSearch, 200);
    });

    table.on('draw.dt', function () {
        highlightSearch();
    });

    // Estilo para celdas resaltadas
    $('<style>')
        .prop('type', 'text/css')
        .html('.highlight-cell { background-color: #50d6ff7e !important; font-weight: bold !important; }')
        .appendTo('head');

});
