/**
 * Auditoría y seguridad — HU-21.
 *
 * Rastro de las acciones críticas: quién, qué, cuándo, sobre qué entidad y
 * con qué resultado. Solo el administrador entra a esta vista.
 */

import { api } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, modal, campo, ok,
} from '../ui.js';

export async function vistaAuditoria(raiz) {
  montar(raiz, cargando('Cargando el registro de auditoría…'));

  let filtros = { q: '', accion: '' };
  const contTabla = el('div');

  async function cargar() {
    montar(contTabla, cargando('Consultando el rastro…'));
    try {
      const datos = await api.auditoria.listar({ ...filtros, tamano: 100 });
      montar(
        contTabla,
        datos.items.length
          ? tabla(datos)
          : vacio('No hay registros que coincidan con el filtro.')
      );
    } catch (e) {
      montar(contTabla, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    }
  }

  const form = el(
    'form.panel.mb-2',
    {
      onsubmit: (e) => {
        e.preventDefault();
        const datos = new FormData(form);
        filtros = { q: datos.get('q')?.trim() || '', accion: datos.get('accion')?.trim() || '' };
        cargar();
      },
    },
    el(
      'div.panel-head',
      {},
      el('h3', {}, 'Filtrar'),
      el('span.small.muted', {}, 'Solo administradores')
    ),
    el(
      'div.field-row',
      {},
      campo({ etiqueta: 'Buscar', nombre: 'q', placeholder: 'Acción, correo, entidad o detalle' }),
      campo({ etiqueta: 'Acción', nombre: 'accion', placeholder: 'Iniciar sesión, Registrar pago…' }),
      el(
        'div.field',
        {},
        el('label', {}, ' '),
        el('button.btn.btn-primary', { type: 'submit' }, icono('buscar'), 'Buscar')
      )
    )
  );

  montar(
    raiz,
    form,
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el('div', {}, el('h3', {}, 'Acciones registradas'),
          el('p.muted.small', { style: { margin: '4px 0 0' } },
            'Los cambios de estado, pagos, accesos y operaciones sobre el sistema.'))
      ),
      contTabla
    )
  );

  await cargar();
}

function tabla(datos) {
  return el(
    'div',
    {},
    el(
      'div.table-wrap',
      {},
      el(
        'table',
        {},
        el(
          'thead',
          {},
          el(
            'tr',
            {},
            el('th', {}, 'Fecha'),
            el('th', {}, 'Usuario'),
            el('th', {}, 'Acción'),
            el('th', {}, 'Entidad'),
            el('th', {}, 'Detalle'),
            el('th', {}, 'Resultado'),
            el('th', {}, '')
          )
        ),
        el(
          'tbody',
          {},
          ...datos.items.map((r) =>
            el(
              'tr',
              {},
              el('td', {}, f.fechaHora(r.fecha)),
              el('td', {}, r.usuario_correo || '—'),
              el('td.cell-main', {}, r.accion),
              el(
                'td',
                {},
                r.entidad
                  ? el('span.status.gris', {}, `${r.entidad}${r.id_entidad ? ` #${r.id_entidad}` : ''}`)
                  : '—'
              ),
              el('td.small', {}, r.detalle || '—'),
              el('td', {}, pill(String(r.estado_http || '—'))),
              el(
                'td',
                {},
                el(
                  'button.btn.btn-sm',
                  { onclick: () => detalle(r) },
                  icono('documento'),
                  'Ver'
                )
              )
            )
          )
        )
      )
    ),
    el('p.small.muted', { style: { padding: '10px 20px 0' } },
      `${datos.total} registro(s). Página ${datos.pagina} de ${Math.max(1, Math.ceil(datos.total / datos.tamano))}.`)
  );
}

function detalle(r) {
  const filas = [
    ['Fecha', f.fechaHora(r.fecha)],
    ['Usuario', r.usuario_correo || '—'],
    ['Acción', r.accion],
    ['Entidad', r.entidad ? `${r.entidad}${r.id_entidad ? ` #${r.id_entidad}` : ''}` : '—'],
    ['Método y ruta', [r.metodo, r.ruta].filter(Boolean).join(' · ') || '—'],
    ['Estado HTTP', r.estado_http || '—'],
    ['IP', r.ip || '—'],
    ['Detalle', r.detalle || '—'],
  ];
  modal({
    titulo: `Registro #${r.id_auditoria}`,
    cuerpo: el(
      'div',
      { style: { display: 'grid', gap: '8px' } },
      ...filas.map(([k, v]) =>
        el(
          'div',
          { style: { display: 'grid', gridTemplateColumns: '120px 1fr', gap: '10px' } },
          el('span.small.muted', {}, k),
          el('span.small', {}, String(v))
        )
      )
    ),
  });
  return ok;
}
