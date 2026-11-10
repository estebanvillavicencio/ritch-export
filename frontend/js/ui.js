/**
 * Utilidades de interfaz: creación de elementos, formato, iconos y avisos.
 *
 * Todo se construye con DOM nativo para no depender de un paso de compilación;
 * los módulos se cargan como ES Modules desde el navegador.
 */

/* -------------------------------------------------------------------------- */
/* Creación de elementos                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Crea un elemento.
 * @param {string} tag  Etiqueta, admite `div.clase#id`.
 * @param {object} props Atributos, `class`, `style`, `dataset`, `on*`, `html`.
 * @param {...any} hijos Hijos: nodos, cadenas, arrays o null.
 */
export function el(tag, props = {}, ...hijos) {
  const [nombre, ...resto] = tag.split(/(?=[.#])/);
  const nodo = document.createElement(nombre || 'div');

  for (const token of resto) {
    if (token.startsWith('.')) nodo.classList.add(token.slice(1));
    else if (token.startsWith('#')) nodo.id = token.slice(1);
  }

  for (const [clave, valor] of Object.entries(props || {})) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (clave === 'class' || clave === 'className') {
      String(valor).split(/\s+/).filter(Boolean).forEach((c) => nodo.classList.add(c));
    } else if (clave === 'html') {
      nodo.innerHTML = valor;
    } else if (clave === 'text') {
      nodo.textContent = valor;
    } else if (clave === 'style' && typeof valor === 'object') {
      Object.assign(nodo.style, valor);
    } else if (clave === 'dataset') {
      Object.assign(nodo.dataset, valor);
    } else if (clave.startsWith('on') && typeof valor === 'function') {
      nodo.addEventListener(clave.slice(2).toLowerCase(), valor);
    } else if (valor === true) {
      nodo.setAttribute(clave, '');
    } else {
      nodo.setAttribute(clave, valor);
    }
  }

  agregar(nodo, hijos);
  return nodo;
}

function agregar(nodo, hijos) {
  for (const hijo of hijos.flat(4)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    nodo.appendChild(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
}

export function vaciar(nodo) {
  while (nodo.firstChild) nodo.removeChild(nodo.firstChild);
  return nodo;
}

export function montar(contenedor, ...hijos) {
  vaciar(contenedor);
  agregar(contenedor, hijos);
  return contenedor;
}

/* -------------------------------------------------------------------------- */
/* Formato                                                                     */
/* -------------------------------------------------------------------------- */

const fmtNum = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const fmtNum2 = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtMoneda = new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: 'EUR', maximumFractionDigits: 0,
});

export const f = {
  entero: (v) => (v === null || v === undefined ? '—' : fmtNum.format(Math.round(v))),
  decimal: (v) => (v === null || v === undefined ? '—' : fmtNum2.format(v)),
  kilos: (v) => (v === null || v === undefined ? '—' : `${fmtNum.format(Math.round(v))} kg`),
  kilos2: (v) => (v === null || v === undefined ? '—' : `${fmtNum2.format(v)} kg`),
  euros: (v) => (v === null || v === undefined ? '—' : fmtMoneda.format(v)),
  moneda: (v, m) =>
    v === null || v === undefined
      ? '—'
      : `${new Intl.NumberFormat('es-CO', { style: 'currency', currency: m || 'EUR', maximumFractionDigits: 0 }).format(v)}`,
  /** Kilos con divisor: 12000 → «12,0 t» */
  toneladas: (v) =>
    v === null || v === undefined ? '—' : `${fmtNum2.format(v / 1000)} t`,
  fecha: (v) => {
    if (!v) return '—';
    const d = new Date(`${String(v).slice(0, 10)}T00:00:00`);
    return Number.isNaN(d.getTime())
      ? '—'
      : d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
  },
  fechaCorta: (v) => {
    if (!v) return '—';
    const d = new Date(`${String(v).slice(0, 10)}T00:00:00`);
    return Number.isNaN(d.getTime())
      ? '—'
      : d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
  },
  fechaHora: (v) => {
    if (!v) return '—';
    const d = new Date(v);
    return Number.isNaN(d.getTime())
      ? '—'
      : d.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' });
  },
  texto: (v) => (v === null || v === undefined || v === '' ? '—' : String(v)),
  iniciales: (nombre) =>
    (nombre || '?')
      .split(/\s+/)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase() || '')
      .join(''),
  /** Plural sencillo: f.plural(1,'lote','lotes') → «1 lote» */
  plural: (n, singular, plural) => `${fmtNum.format(n)} ${n === 1 ? singular : plural}`,
};

/* -------------------------------------------------------------------------- */
/* Estados visuales                                                            */
/* -------------------------------------------------------------------------- */

const CLASES_ESTADO = {
  'Entregado': 'verde', 'Aprobado': 'verde', 'Vigente': 'verde', 'Aceptada': 'verde',
  'Validado': 'verde', 'Aprobado con reserva': 'oro', 'Por renovar': 'oro',
  'En tránsito': 'azul', 'En puerto': 'azul', 'En aduana': 'azul', 'En destino': 'azul',
  'En preparación': 'azul', 'En producción': 'azul', 'Pedido recibido': 'azul',
  'Enviada': 'azul', 'Programado': 'gris', 'En análisis': 'oro', 'Pendiente': 'gris',
  'Rechazado': 'rust', 'Vencida': 'rust', 'Aprobado con reserva ': 'oro',
  'Incidencia': 'rust', 'Demorado': 'rust', 'Anulado': 'gris', 'Borrador': 'gris',
  'Rechazada': 'rust', 'Aprobado con reserva': 'oro', 'Desconocido': 'gris',
};

/** Etiqueta de estado con el color correspondiente. */
export function pill(estado) {
  const texto = estado ?? '—';
  return el('span.status', { class: CLASES_ESTADO[texto] || 'gris' }, texto);
}

export function vacio(mensaje = 'No hay registros para mostrar') {
  return el('div.empty', {}, icono('caja'), el('div', {}, mensaje));
}

export function cargando(texto = 'Cargando…') {
  return el('div.loading', {}, el('span.spinner'), ` ${texto}`);
}

export function errorBox(mensaje) {
  return el('div.alert.rust', {}, icono('alerta'), el('div', {}, mensaje));
}

/* -------------------------------------------------------------------------- */
/* Avisos flotantes                                                           */
/* -------------------------------------------------------------------------- */

let contenedorToasts = null;

export function aviso(mensaje, tipo = 'ok') {
  if (!contenedorToasts) {
    contenedorToasts = el('div.toasts');
    document.body.appendChild(contenedorToasts);
  }
  const nodo = el('div.toast', { class: tipo }, el('span', {}, mensaje));
  contenedorToasts.appendChild(nodo);
  setTimeout(() => {
    nodo.style.transition = 'opacity .3s';
    nodo.style.opacity = '0';
    setTimeout(() => nodo.remove(), 300);
  }, tipo === 'err' ? 6000 : 3500);
  return nodo;
}

export const ok = (m) => aviso(m, 'ok');
export const error = (m) => aviso(m, 'err');

/* -------------------------------------------------------------------------- */
/* Modal                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Abre un modal. Devuelve `{ cerrar }`.
 * @param {object} cfg { titulo, cuerpo, ancho, pie, alCerrar }
 */
export function modal({ titulo, cuerpo, ancho = '', pie, alCerrar }) {
  const cerrar = () => {
    document.removeEventListener('keydown', alTeclear);
    fondo.remove();
    if (alCerrar) alCerrar();
  };
  const alTeclear = (e) => {
    if (e.key === 'Escape') cerrar();
  };

  const caja = el(
    'div.modal',
    { class: ancho, onclick: (e) => e.stopPropagation() },
    el(
      'div.modal-head',
      {},
      el('h3', {}, titulo),
      el('button.modal-close', { onclick: () => cerrar(), 'aria-label': 'Cerrar' }, '×')
    ),
    el('div.modal-body', {}, cuerpo),
    pie ? el('div.modal-foot', {}, pie) : null
  );

  const fondo = el('div.modal-backdrop', { onclick: () => cerrar() }, caja);
  document.body.appendChild(fondo);
  document.addEventListener('keydown', alTeclear);

  const primero = caja.querySelector('input, select, textarea');
  if (primero) setTimeout(() => primero.focus(), 40);

  return { cerrar, caja };
}

export function confirmar({ titulo, mensaje, textoOk = 'Confirmar', peligro = false }) {
  return new Promise((resolver) => {
    let decidido = false;
    const { cerrar } = modal({
      titulo,
      cuerpo: el('p', { style: { margin: 0, fontSize: '13.5px' } }, mensaje),
      pie: [
        el('button.btn', { onclick: () => { decidido = true; cerrar(); resolver(false); } }, 'Cancelar'),
        el(
          'button.btn',
          { class: peligro ? 'btn-danger' : 'btn-primary', onclick: () => { decidido = true; cerrar(); resolver(true); } },
          textoOk
        ),
      ],
      alCerrar: () => { if (!decidido) resolver(false); },
    });
  });
}

/* -------------------------------------------------------------------------- */
/* Formularios                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Construye un campo de formulario.
 * @param {object} cfg { etiqueta, nombre, tipo, valor, opciones, requerido,
 *                       placeholder, pista, atributos, min, max, step, fila }
 */
export function campo(cfg) {
  const {
    etiqueta, nombre, tipo = 'text', valor = '', opciones, requerido = false,
    placeholder = '', pista = '', atributos = {}, min, max, step, ancho,
  } = cfg;

  let control;
  if (tipo === 'select') {
    control = el(
      'select',
      { name: nombre, id: `c-${nombre}`, ...atributos },
      ...(opciones || []).map((o) => {
        const valorOpt = typeof o === 'object' ? o.valor : o;
        const texto = typeof o === 'object' ? o.texto : o;
        return el('option', { value: valorOpt, selected: String(valorOpt) === String(valor) }, texto);
      })
    );
  } else if (tipo === 'textarea') {
    control = el('textarea', { name: nombre, id: `c-${nombre}`, placeholder, ...atributos }, valor ?? '');
  } else {
    control = el('input', {
      name: nombre, id: `c-${nombre}`, type: tipo, value: valor ?? '',
      placeholder, min, max, step, ...atributos,
    });
  }
  if (requerido) control.required = true;

  return el(
    'div.field',
    { class: ancho === 'full' ? 'full' : '' },
    etiqueta ? el('label', { for: `c-${nombre}` }, etiqueta, requerido ? ' *' : '') : null,
    control,
    pista ? el('div.hint', {}, pista) : null
  );
}

export function filaCampos(...campos) {
  const n = campos.filter(Boolean).length;
  if (n === 3) return el('div.field-row-3', {}, ...campos);
  return el('div.field-row', {}, ...campos);
}

/** Lee un `<form>` como objeto plano. */
export function leerFormulario(form) {
  const datos = {};
  for (const [clave, valor] of new FormData(form).entries()) {
    datos[clave] = typeof valor === 'string' ? valor.trim() : valor;
  }
  for (const checkbox of form.querySelectorAll('input[type=checkbox]')) {
    datos[checkbox.name] = checkbox.checked;
  }
  return datos;
}

/** Marca visualmente los campos requeridos sin enviar el formulario. */
/** Retrasa la ejecución de `fn` hasta que pasen `ms` sin nuevas llamadas. */
export function debounce(fn, ms = 280) {
  let temporizador = null;
  return (...args) => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => fn(...args), ms);
  };
}

/* -------------------------------------------------------------------------- */
/* Iconos (SVG inline, trazo de 2 px como en el mockup)                       */
/* -------------------------------------------------------------------------- */

const TRAZOS = {
  panel: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  lotes: '<path d="M3 20l4-9 4 5 3-4 7 8"/><circle cx="12" cy="7" r="2.5"/>',
  calidad: '<path d="M9 3h6l1 4-4 5-4-5 1-4z"/><path d="M8 12l-3 8h14l-3-8"/>',
  comercial: '<path d="M4 4h16v13H8l-4 4z"/>',
  logistica: '<rect x="1" y="7" width="14" height="10" rx="1"/><path d="M15 10h4l3 3v4h-7z"/><circle cx="6" cy="19" r="1.6"/><circle cx="17.5" cy="19" r="1.6"/>',
  financiero: '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h3.2a2 2 0 010 4H9.3a2 2 0 000 4H15"/>',
  usuarios: '<circle cx="9" cy="8" r="3.2"/><path d="M2.5 20c1-4 3.4-6 6.5-6s5.5 2 6.5 6"/><circle cx="18" cy="7" r="2.4"/><path d="M15.5 12.2c2.5.2 4 2 4.8 4.8"/>',
  portal: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.5 4 5.7 4 9s-1.5 6.5-4 9c-2.5-2.5-4-5.7-4-9s1.5-6.5 4-9z"/>',
  buscar: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  campana: '<path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 0 01-3.4 0"/>',
  mas: '<path d="M12 5v14M5 12h14"/>',
  alerta: '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L14.7 3.9a2 2 0 00-3.4 0z"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  documento: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M9 13h6M9 17h6"/>',
  etiqueta: '<path d="M20.6 13.4L12 22l-9-9V3h10l7.6 7.6a2 2 0 010 2.8z"/><circle cx="7.5" cy="7.5" r="1.3"/>',
  candado: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>',
  salir: '<path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/>',
  descargar: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/>',
  editar: '<path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.1 2.1 0 013 3L12 15l-4 1 1-4z"/>',
  contenedor: '<path d="M2 7h13v10H2z"/><path d="M15 10h4l3 3v4h-7z"/><circle cx="6" cy="19" r="1.4"/><circle cx="17" cy="19" r="1.4"/>',
  filtro: '<path d="M22 3H2l8 9.5V19l4 2v-8.5z"/>',
  hoja: '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M16 13H8M16 17H8M10 9H8"/>',
  euro: '<path d="M17 7a6 6 0 000 10M4 10h9M4 14h9"/>',
  hojaCheck: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>',
  grafico: '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
  caja: '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
  sistema: '<path d="M12 15.2a3.2 3.2 0 100-6.4 3.2 3.2 0 000 6.4z"/><path d="M19.4 15a1.7 1.7 0 00.3 1.9l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.9-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.9.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.9 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.9l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.9.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.9-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.9V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"/>',
  auditoria: '<path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
  refrescar: '<path d="M21 12a9 9 0 11-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
};

export function icono(nombre, extra = '') {
  const d = TRAZOS[nombre];
  if (!d) return el('span');
  return el('svg', {
    viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
    'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    class: extra, 'aria-hidden': 'true',
    html: d,
  });
}

/* -------------------------------------------------------------------------- */
/* Utilidades varias                                                           */
/* -------------------------------------------------------------------------- */

/** Fecha de hoy en formato ISO (YYYY-MM-DD). */
export const hoy = () => new Date().toISOString().slice(0, 10);

/** Escapa el texto antes de insertarlo como HTML. */
export function escapar(texto) {
  const div = document.createElement('div');
  div.textContent = String(texto ?? '');
  return div.innerHTML;
}
