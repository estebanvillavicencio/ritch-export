/**
 * Bandeja de notificaciones — HU-16.
 *
 * Reúne los avisos derivados (certificaciones, envíos y saldos) con los que
 * generan las operaciones. Se puede marcar una o todas como leídas.
 */

import { api } from '../api.js';
import {
  el, montar, icono, cargando, vacio, f, aviso, error,
} from '../ui.js';

const TONO = { verde: 'leaf', gold: 'gold', rust: 'rust', azul: '' };

export async function vistaNotificaciones(raiz) {
  montar(raiz, cargando('Cargando la bandeja…'));

  let soloNoLeidas = false;
  const contador = el('div.flex');
  const lista = el('div');

  async function cargar() {
    montar(lista, cargando('Actualizando avisos…'));
    try {
      const [avisos, cuenta] = await Promise.all([
        api.notificaciones.listar({ solo_no_leidas: soloNoLeidas ? 1 : undefined, limite: 100 }),
        api.notificaciones.contador(),
      ]);
      pintarContador(cuenta);
      montar(
        lista,
        avisos.length
          ? el('div', { style: { display: 'grid', gap: '10px' } }, ...avisos.map(tarjeta))
          : vacio('No hay notificaciones para mostrar.')
      );
    } catch (e) {
      montar(lista, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    }
  }

  function pintarContador(cuenta) {
    montar(
      contador,
      el('span.small.muted', {}, `${cuenta.no_leidas} sin leer de ${cuenta.total}`),
      el(
        'button.btn.btn-sm',
        { class: soloNoLeidas ? 'btn-primary' : '', onclick: () => { soloNoLeidas = !soloNoLeidas; cargar(); } },
        soloNoLeidas ? 'Ver todas' : 'Solo no leídas'
      ),
      el(
        'button.btn.btn-sm',
        {
          onclick: async () => {
            try {
              const r = await api.notificaciones.leerTodas();
              aviso(r.mensaje, 'ok');
              cargar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        icono('check'),
        'Marcar todas'
      )
    );
  }

  async function marcar(aviso) {
    if (aviso.leida) return;
    try {
      await api.notificaciones.leer(aviso.id_notificacion);
      cargar();
    } catch (e) {
      error(e.message);
    }
  }

  montar(
    raiz,
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el(
          'div',
          {},
          el('h3', {}, 'Bandeja de avisos'),
          el('p.muted.small', { style: { margin: '4px 0 0' } },
            'Vencimientos, envíos con incidencia, pagos y cambios de estado.')
        ),
        contador
      ),
      lista
    )
  );

  await cargar();
}

function tarjeta(aviso) {
  const clase = TONO[aviso.tono] ?? '';
  const nodo = el(
    'div.alert',
    { class: clase, style: { cursor: aviso.leida ? 'default' : 'pointer', opacity: aviso.leida ? '.7' : '1' } },
    icono(aviso.leida ? 'check' : 'campana'),
    el(
      'div',
      { style: { flex: '1' } },
      el(
        'div.flex-between',
        {},
        el('strong', {}, aviso.titulo),
        el('span.small.muted', {}, f.fechaHora(aviso.fecha))
      ),
      aviso.detalle ? el('div.small', { style: { marginTop: '2px' } }, aviso.detalle) : null,
      el(
        'div.flex',
        { style: { marginTop: '6px' } },
        el('span.status.gris', {}, aviso.tipo),
        !aviso.leida
          ? el('button.btn.btn-sm', { onclick: (e) => { e.stopPropagation(); marcar(aviso); } }, 'Marcar leída')
          : el('span.small.muted', {}, 'Leída'),
        aviso.enlace ? el('a.btn.btn-sm', { href: aviso.enlace }, 'Abrir') : null,
        aviso.rol_destino ? el('span.small.muted', {}, `Para: ${aviso.rol_destino}`) : null
      )
    )
  );
  if (!aviso.leida) nodo.addEventListener('click', () => marcar(aviso));
  return nodo;
}
