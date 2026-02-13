        document.addEventListener('DOMContentLoaded', function () {
    const dropArea   = document.getElementById('drop-area');
    const fileInput  = document.getElementById('file-input');
    const browseBtn  = document.getElementById('browse-btn');
    const fileListUl = document.getElementById('file-list');

    // Array donde vamos a guardar los archivos seleccionados
    let selectedFiles = [];

    // ---------------------------
    // helpers
    // ---------------------------
    function bytesToSize(bytes) {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return parseFloat((bytes / Math.pow(1024, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function rebuildInputFiles() {
        // Reconstruye fileInput.files con los archivos que quedan
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(f => dataTransfer.items.add(f));
        fileInput.files = dataTransfer.files;
    }

    function renderFileList() {
        fileListUl.innerHTML = '';

        if (selectedFiles.length === 0) {
            return;
        }

        selectedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            li.innerHTML = `
                <div class="text-start">
                    <strong>${file.name}</strong><br>
                    <small class="text-muted">${bytesToSize(file.size)}</small>
                </div>
                <button type="button" class="btn btn-rojo btn-tooltip" title="Quitar" data-index="${index}">
                    ​❌
                </button>
            `;

            fileListUl.appendChild(li);
        });

        // manejar clicks en botón "Quitar"
        fileListUl.querySelectorAll('button[data-index]').forEach(btn => {
            btn.addEventListener('click', function () {
                const idx = parseInt(this.getAttribute('data-index'));
                selectedFiles.splice(idx, 1);     // eliminar del array
                rebuildInputFiles();              // actualizar input.files
                renderFileList();                 // re-dibujar lista
            });
        });
    }

    function addFiles(files) {
        // files es un FileList o array-like
        Array.from(files).forEach(file => {
            // evitar duplicados por nombre + tamaño + fecha modif
            const exists = selectedFiles.some(f =>
                f.name === file.name &&
                f.size === file.size &&
                f.lastModified === file.lastModified
            );
            if (!exists) {
                selectedFiles.push(file);
            }
        });

        rebuildInputFiles();
        renderFileList();
    }

    // ---------------------------
    // Eventos
    // ---------------------------

    // click en el botón → abre selector de archivos
    browseBtn.addEventListener('click', () => fileInput.click());

    // click en el área completa → también abre selector
    dropArea.addEventListener('click', (e) => {
        // evitamos que el click en el botón se duplique
        if (e.target.id !== 'browse-btn') {
            fileInput.click();
        }
    });

    // cuando el usuario selecciona archivos por el input
    fileInput.addEventListener('change', function () {
        if (this.files && this.files.length > 0) {
            addFiles(this.files);
        }
    });

    // drag & drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropArea.classList.add('border-primary');
            dropArea.style.background = '#f8f9fa';
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropArea.classList.remove('border-primary');
            dropArea.style.background = '#fff';
        });
    });

    dropArea.addEventListener('drop', function (e) {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
            addFiles(dt.files);
        }
    });
});
