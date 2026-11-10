/**
 * Armazón de la aplicación: barra lateral, cabecera y enrutado por hash.
 */

import { api, sesion } from './api.js';
import { el, montar, icono } from './ui.js';
import { vistaPanel } from './views/panel.js';
import { vistaLotes } from './views/lotes.js';
import { vistaComercial } from './views/comercial.js';
import { vistaLogistica } from './views/logistica.js';
import { vistaUsuarios } from './views/usuarios.js';
import { vistaPortal } from './views/portal.js';
import { vistaFinanciero } from './views/financiero.js';
import { vistaNotificaciones } from './views/notificaciones.js';
import { vistaAuditoria } from './views/auditoria.js';
import { vistaSistema } from './views/sistema.js';

/* -------------------------------------------------------------------------- */
/* Mapa de vistas                                                              */
/* -------------------------------------------------------------------------- */
const VISTAS = {
  panel: { titulo: 'Panel general', eyebrow: 'RiTech SAS · Exportación', render: vistaPanel, icono: 'panel', grupo: 'General' },
  lotes: { titulo: 'Productores y lotes', eyebrow: 'Operación · Origen', render: vistaLotes, icono: 'lotes', grupo: 'Operación' },
  comercial: { titulo: 'Comercial', eyebrow: 'Operación · Mercado', render: vistaComercial, icono: 'comercial', grupo: 'Operación' },
  logistica: { titulo: 'Logística y envíos', eyebrow: 'Operación · Transporte', render: vistaLogistica, icono: 'logistica', grupo: 'Operación' },
  financiero: { titulo: 'Financiero', eyebrow: 'Operación · Cartera', render: vistaFinanciero, icono: 'financiero', grupo: 'Operación' },
  usuarios: { titulo: 'Usuarios y roles', eyebrow: 'Sistema · Seguridad', render: vistaUsuarios, icono: 'usuarios', grupo: 'Sistema' },
  notificaciones: { titulo: 'Notificaciones', eyebrow: 'Sistema · Avisos', render: vistaNotificaciones, icono: 'campana', grupo: 'Sistema' },
  auditoria: { titulo: 'Auditoría', eyebrow: 'Sistema · Seguridad', render: vistaAuditoria, icono: 'auditoria', grupo: 'Sistema' },
  sistema: { titulo: 'Sistema', eyebrow: 'Sistema · Integraciones y respaldos', render: vistaSistema, icono: 'sistema', grupo: 'Sistema' },
  portal: { titulo: 'Portal cliente UE', eyebrow: 'Sistema · Cliente europeo', render: vistaPortal, icono: 'portal', grupo: 'Sistema' },
};

/** Roles con acceso a cada vista (RR-004). */
const ACCESO = {
    panel: ['Administrador', 'Comercial', 'Calidad', 'Logística', 'Financiero'],
    lotes: ['Administrador', 'Comercial', 'Calidad', 'Logística', 'Financiero'],
    comercial: ['Administrador', 'Comercial', 'Logística', 'Financiero'],
    logistica: ['Administrador', 'Logística', 'Comercial', 'Financiero'],
    financiero: ['Administrador', 'Financiero', 'Comercial', 'Logística', 'Cliente europeo'],
    usuarios: ['Administrador'],
    notificaciones: ['Administrador', 'Comercial', 'Calidad', 'Logística', 'Financiero'],
    auditoria: ['Administrador'],
    sistema: ['Administrador', 'Financiero'],
    portal: ['Administrador', 'Cliente europeo'],
  };

  /**
   * Pantalla de inicio por rol. El cliente europeo no tiene acceso al panel
   * general, así que al abrir la aplicación tiene que caer en su portal; si no,
   * la vista por defecto lo dejaría en una pantalla prohibida.
   */
  const INICIO_POR_ROL = { 'Cliente europeo': 'portal' };

const ORDEN_NAV = [
  'panel', 'lotes', 'comercial', 'logistica', 'financiero',
  'usuarios', 'notificaciones', 'auditoria', 'sistema', 'portal',
];

/* -------------------------------------------------------------------------- */
/* Arranque                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * `navegar` y `contenedor` sobreviven entre navegaciones: sin ellos, cada
 * cambio de hash volvería a construir la aplicación y registrar OTRO
 * escuchador de `hashchange`, multiplicando las peticiones a la API.
 */
let navegar = null;

export function iniciarApp(contenedor) {
  if (!sesion.activo) {
    location.hash = '#/login';
    return;
  }

  // Ya está montada: solo hay que reaccionar al hash.
  if (navegar) {
    navegar();
    return;
  }

  const raiz = el('div.app');
  montar(contenedor, raiz);

  const contenido = el('main');
  const lateral = barraLateral();
  raiz.appendChild(lateral.nodo);
  raiz.appendChild(contenido);

  function rutaActual() {
    const hash = location.hash.replace(/^#\/?/, '');
    if (VISTAS[hash]) return hash;
    // Sin hash, cada rol entra por donde puede.
    const porRol = sesion.usuario && INICIO_POR_ROL[sesion.usuario.rol];
    if (porRol && VISTAS[porRol]) return porRol;
    return 'panel';
  }

  async function navigate() {
    const clave = rutaActual();
    const vista = VISTAS[clave];
    const permitidos = ACCESO[clave];

    if (permitidos && !sesion.puede(...permitidos)) {
      montar(
        contenido,
        cabecera(vista, clave),
        el(
          'div.panel',
          {},
          el(
            'div.alert.rust',
            {},
            icono('candado'),
            el(
              'div',
              {},
              el('strong', {}, 'Acceso restringido'),
              `Tu rol «${sesion.usuario.rol}» no tiene permisos para «${vista.titulo}».`
            )
          )
        )
      );
      lateral.activar(clave);
      return;
    }

    lateral.activar(clave);
    montar(contenido, cabecera(vista, clave), el('div'));
    const destino = contenido.lastElementChild;
    try {
      await vista.render(destino);
    } catch (e) {
      montar(destino, el('div.alert.rust', {}, icono('alerta'), el('div', {}, `Error al cargar: ${e.message}`)));
    }
  }

  navegar = navigate;
  window.addEventListener('hashchange', navigate);

  // Atajo: Cmd/Ctrl+K enfoca la búsqueda global.
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      document.getElementById('busqueda-global')?.focus();
    }
  });

  navigate();
}

/**
 * Olvida el armazón actual para que la próxima entrada lo reconstruya.
 * Se llama al cerrar sesión y tras iniciar sesión con otra cuenta, ya que
 * la barra lateral depende del rol.
 */
export function reiniciarApp() {
  navegar = null;
}

/* -------------------------------------------------------------------------- */
/* Piezas                                                                      */
/* -------------------------------------------------------------------------- */
function cabecera(vista, clave) {
  const usuario = sesion.usuario;
  return el(
    'div.topbar',
    {},
    el(
      'div',
      {},
      el('div.eyebrow', {}, vista.eyebrow),
      el('h1.display', {}, vista.titulo)
    ),
    el(
      'div.top-actions',
      {},
      el(
        'div.search',
        {},
        icono('buscar'),
        el('input', {
          id: 'busqueda-global',
          type: 'search',
          placeholder: 'Buscar lote, contenedor, cliente…',
          onkeydown: (e) => {
            if (e.key !== 'Enter') return;
            const q = e.target.value.trim();
            if (!q) return;
            location.hash = '#/lotes';
            setTimeout(() => {
              const input = document.querySelector('input[type=search]');
              if (input) {
                input.value = q;
                input.dispatchEvent(new Event('input'));
              }
            }, 120);
          },
        })
      ),
      botonAlertas(),
      clave === 'lotes' && sesion.puede('Administrador', 'Comercial', 'Calidad', 'Logística')
        ? el('a.btn.btn-primary', { href: '#/lotes' }, icono('mas'), 'Nuevo lote')
        : null,
      el(
        'button.btn',
        { title: 'Cerrar sesión', onclick: cerrarSesion },
        icono('salir'),
        'Salir'
      )
    )
  );
}

function botonAlertas() {
  const nodo = el(
    'div.bell',
    {
      title: 'Notificaciones',
      onclick: () => { location.hash = '#/notificaciones'; },
    },
    icono('campana')
  );
  // HU-16 · el contador de la bandeja es la fuente del punto rojo.
  api.notificaciones
    .contador()
    .then((c) => {
      if (c.no_leidas > 0) {
        nodo.classList.add('has-alerts');
        nodo.title = `${c.no_leidas} notificación(es) sin leer`;
      }
    })
    .catch(() => {});
  return nodo;
}

function barraLateral() {
  const items = {};
  const nav = el('nav');
  let grupoActual = null;

  for (const clave of ORDEN_NAV) {
    const vista = VISTAS[clave];
    const permitidos = ACCESO[clave];
    if (permitidos && !sesion.puede(...permitidos)) continue;

    if (vista.grupo !== grupoActual) {
      grupoActual = vista.grupo;
      nav.appendChild(el('div.nav-label', {}, grupoActual));
    }
    const nodo = el(
      'button.nav-item',
      { dataset: { vista: clave }, onclick: () => { location.hash = `#/${clave}`; } },
      icono(vista.icono),
      vista.titulo
    );
    items[clave] = nodo;
    nav.appendChild(nodo);
  }

  const usuario = sesion.usuario;
  const nodo = el(
    'aside.sidebar',
    {},
    el(
      'div.brand',
      {},
      el('div.brand-mark', {}, 'R'),
      el(
        'div',
        {},
        el('div.brand-name', {}, 'RiTech'),
        el('div.brand-sub', {}, 'Café · Cacao · UE')
      )
    ),
    nav,
    el(
      'div.sidebar-foot',
      {},
      el('div.avatar', {}, (usuario?.nombre || '?').split(' ').slice(0, 2).map((p) => p[0]).join('').toUpperCase()),
      el(
        'div',
        {},
        el('div.foot-name', {}, usuario?.nombre || '—'),
        el('div.foot-role', {}, usuario?.rol || '')
      )
    )
  );

  return {
    nodo,
    activar(clave) {
      for (const [k, item] of Object.entries(items)) item.classList.toggle('active', k === clave);
    },
  };
}

export async function cerrarSesion() {
  try {
    await api.auth.salir();
  } catch { /* el token es sin estado: se descarta igualmente */ }
  sesion.cerrar();
  reiniciarApp();
  location.hash = '#/login';
}
