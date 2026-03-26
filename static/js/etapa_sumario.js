(function () {
    const MODAL_ID = "modal-etapas";
    const BODY_ID = "modal-etapas-body";
    let currentSumarioId = null;

    document.addEventListener('DOMContentLoaded', function() {
        document.addEventListener('click', function(e) {
            if (e.target.closest('.btn-etapas')) {
                const sumarioId = e.target.closest('.btn-etapas').getAttribute('data-id');
                loadEtapasModal(sumarioId);
            }
        });
    });

    async function loadEtapasModal(sumarioId) {
        try {
            currentSumarioId = sumarioId;
            const response = await fetch(`/api/sumario/${sumarioId}/etapas`);
            
            const data = await response.json();
            console.log('data:', data);
            
            renderEtapasModal(data);
            const modalElement = document.getElementById(MODAL_ID);
            if (modalElement) {
                const myModal = new bootstrap.Modal(modalElement);
                myModal.show();
            }
        } catch (error) {
            console.error('Error cargando etapas:', error);
        }
    }

    function renderEtapasModal(data) {
        const etapas = [
            { id: 1, nombre: 'Indagatoria o investigación', tipo: 'archivo' },
            { id: 2, nombre: 'Formulación de cargos o etapa acusatoria', tipo: 'boolean' },
            { id: 3, nombre: 'Periodo de descargos y/o periodo de prueba', tipo: 'boolean' },
            { id: 4, nombre: 'Informe del fiscal', tipo: 'archivo' }
        ];

        let html = '<div class="etapas-container">';
        
        etapas.forEach(etapa => {
            const valor = data[`archivo_${etapa.id}`];
            
            if (etapa.tipo === 'archivo') {
                const archivoUrl = valor;
                const nombreArchivo = archivoUrl?.split('/').pop() || 'archivo';
                
                html += `
                    <div class="etapa-section mb-4 p-3 border rounded">
                        <h5>${etapa.id}.- ${etapa.nombre}</h5>
                        <div class="archivo-section mt-3">
                            ${archivoUrl ? 
                                `<p><strong>Archivo:</strong> <a href="${archivoUrl}" target="_blank">${nombreArchivo}</a></p>` 
                                : '<p class="text-muted">Sin archivos adjuntos</p>'
                            }
                            <input type="file" class="form-control mt-2" id="etapa_${etapa.id}" accept=".pdf,.doc,.docx,.jpg,.png">
                            <small class="text-muted">Subir evidencia de avance</small>
                        </div>
                    </div>
                `;
            } else if (etapa.tipo === 'boolean') {
                const isChecked = valor ? 'checked' : '';
                
                html += `
                    <div class="etapa-section mb-4 p-3 border rounded">
                        <h5>${etapa.id}.- ${etapa.nombre}</h5>
                        <div class="mt-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="etapa_${etapa.id}" ${isChecked}>
                                <label class="form-check-label" for="etapa_${etapa.id}">
                                    Completada
                                </label>
                            </div>
                        </div>
                    </div>
                `;
            }
        });
        
        html += '</div>';
        document.getElementById(BODY_ID).innerHTML = html;
    }

    async function guardarEtapas() {
        const formData = new FormData();
        formData.append('sumario_id', currentSumarioId);
        
        for (let i = 1; i <= 4; i++) {
            const input = document.getElementById(`etapa_${i}`);
            
            if (i === 1 || i === 4) {
                // Archivo
                if (input.files[0]) {
                    formData.append(`etapa_${i}`, input.files[0]);
                }
            } else {
                // Boolean
                formData.append(`etapa_${i}`, input.checked);
            }
        }
        
        try {
            const response = await fetch(`/api/sumario/${currentSumarioId}/etapas/guardar/`, {
            method: 'POST',
            body: formData
            });
            const result = await response.json();
            alert(result.mensaje || 'Guardado con éxito');
            location.reload();
        } catch (error) {
            console.error('Error guardando:', error);
        }
    }

    window.loadEtapasModal = loadEtapasModal;
    window.guardarEtapas = guardarEtapas;
})();