document.addEventListener('DOMContentLoaded', () => {
  const inputsFecha = Array.from(document.querySelectorAll('.fecha-nohabiles'));
  if (inputsFecha.length === 0) return; // esta página no tiene fechas, chao

  const feriados = new Set();
  let feriadosCargados = false;

  function normalizarFechaLocal(dateObj) {
    const y = dateObj.getFullYear();
    const m = String(dateObj.getMonth() + 1).padStart(2, '0');
    const d = String(dateObj.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  // Cargar feriados una vez
  fetch('https://api.boostr.cl/holidays.json')
    .then(r => r.json())
    .then(data => {
      let lista = Array.isArray(data) ? data : Object.values(data).find(v => Array.isArray(v)) || [];
      lista.forEach(item => item?.date && feriados.add(item.date));
      feriadosCargados = true;
    })
    .catch(err => {
      console.error('No se pudieron cargar los feriados:', err);
    });

  function esFechaInvalida(valorFecha) {
    if (!valorFecha) return false;

    const [y, m, d] = valorFecha.split('-').map(Number);
    const fecha = new Date(y, m - 1, d); // local, sin desfase
    const dia = fecha.getDay(); // 0 dom, 6 sab

    if (dia === 0 || dia === 6) return 'No se permiten sábados ni domingos.';
    if (feriados.has(valorFecha)) return 'La fecha seleccionada es un día feriado.';
    return false;
  }

  function validarInput(input, mostrarAlert = false) {
    const valor = input.value;
    const msg = esFechaInvalida(valor);

    if (msg) {
      input.value = '';
      input.setCustomValidity(msg);
      input.reportValidity();
      if (mostrarAlert) alert(msg.includes('feriado') ? 'No se puede guardar en un día feriado.' : msg);
      return false;
    }
    input.setCustomValidity('');
    return true;
  }

  // Validar al cambiar
  inputsFecha.forEach(input => {
    input.addEventListener('change', () => validarInput(input, false));
  });

  // Validar al enviar cualquier form que contenga esos inputs
  const forms = new Set(inputsFecha.map(i => i.form).filter(Boolean));
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      // Si aún no cargaron feriados, igual bloquea fines de semana.
      // (si quieres bloquear TODO hasta cargar feriados, te lo ajusto)
      const ok = inputsFecha
        .filter(i => i.form === form)
        .every(i => validarInput(i, true));

      if (!ok) e.preventDefault();
    });
  });
});
