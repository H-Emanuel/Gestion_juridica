(function () {
    const MODAL_ID = "ModalFinal_sumario";
    const FORM_ID = "formSumario";
    let currentSumarioId = null;

    // Event delegation para botón de apertura del modal
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-respondido-sumario')) {
            const sumarioId = e.target.closest('.btn-respondido-sumario').getAttribute('data-id');
            loadFinalSumarioModal(sumarioId);
        }
    });

    function loadFinalSumarioModal(sumarioId) {
        currentSumarioId = sumarioId;
        const modalElement = document.getElementById(MODAL_ID);
        if (modalElement) {
            const myModal = new bootstrap.Modal(modalElement);
            myModal.show();
        }
    }

    async function Termina_sumario() {
        const respuesta = document.getElementById('respuesta_sumario').value;
        const archivoInput = document.getElementById('archivo_sumario');
        
        if (!respuesta.trim() || !archivoInput.files[0]) {
            alert('Por favor completa todos los campos');
            return;
        }

        const formData = new FormData();
        formData.append('sumario_id', currentSumarioId);
        formData.append('respuesta', respuesta);
        formData.append('archivo', archivoInput.files[0]);

        try {
            const response = await fetch(`/api/sumario/${currentSumarioId}/finalizar/`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            alert(result.mensaje || 'Respuesta enviada con éxito');
            location.reload();
        } catch (error) {
            console.error('Error enviando respuesta:', error);
            alert('Error al enviar la respuesta');
        }
    }

    function cerrarModal() {
        const modalElement = document.getElementById(MODAL_ID);
        const myModal = bootstrap.Modal.getInstance(modalElement);
        if (myModal) {
            myModal.hide();
        }
        document.getElementById(FORM_ID).reset();
        currentSumarioId = null;
    }

    // Exportar funciones
    window.loadFinalSumarioModal = loadFinalSumarioModal;
    window.Termina_sumario = Termina_sumario;
    window.cerrarModal = cerrarModal;
})();