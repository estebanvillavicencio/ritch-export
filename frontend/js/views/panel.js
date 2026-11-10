/**
 * Panel general — reproducción de la pantalla del mockup.
 *
 * Reúne las tarjetas KPI, la línea de tiempo del envío, las barras de
 * cumplimiento, la tabla de pedidos recientes, la ficha de lote y las alertas.
 */

import { api } from '../api.js';
import {
  el, montar, icono, pill, vacio, f, errorBox,
} from '../ui.js';

const ICONO_KPI = {
  'Lotes activos': 'lotes',
  'Contenedores en tránsito': 'logistica',
  'Certificaciones vigentes': 'calidad',
  'Contratos abiertos': 'comercial',
};

export async function vistaPanel(raiz) {
  montar(raiz, el('div.loading', {}, el('span.spinner'), ' Cargando el panel…'));

  let panel;
  try {
    panel = await api.panel.datos();
  } catch (e) {
    montar(raiz, errorBox(`No se pudo cargar el panel: ${e.message}`));
    return;
  }

  const alertas = panelAlertas(panel.alertas || []);

  montar(
    raiz,
    alertas,
    seccionKpis(panel.tarjetas),
    rejilla(
      panelEnvio(panel.envio_destacado),
      panelCumplimiento(panel.cumplimiento)
    ),
    rejilla(
      panelPedidos(panel.pedidos_recientes),
      panelFichaLote(panel.ficha_lote)
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Alertas (HU-16)                                                             */
/* -------------------------------------------------------------------------- */
function panelAlertas(alertas) {
  if (!alertas.length) return null;
  return el(
    'div.panel',
    { style: { marginBottom: '14px' } },
    el(
      'div.panel-head',
      {},
      el('h3', {}, 'Alertas y vencimientos'),
      el('span.status.rust', {}, String(alertas.length))
    ),
    ...alertas.slice(0, 6).map((a) =>
      el(
        `div.alert.${a.tono || 'oro'}`,
        {},
        icono('alerta'),
        el('div', {}, el('strong', {}, a.titulo), a.detalle)
      )
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Tarjetas KPI                                                                */
/* -------------------------------------------------------------------------- */
function seccionKpis(tarjetas) {
  return el(
    'div.kpis',
    {},
    ...tarjetas.map((t) =>
      el(
        'div.kpi',
        {},
        el(
          'div.kpi-top',
          {},
          el('span.kpi-label', {}, t.etiqueta),
          el('div.kpi-icon', { class: `tono-${t.tono}` }, icono(ICONO_KPI[t.etiqueta] || 'panel'))
        ),
        el('div.kpi-value', {}, t.valor),
        t.detalle
          ? el(
              'div.kpi-delta',
              { class: t.tono === 'rust' ? 'rust' : t.tono === 'leaf' ? 'leaf' : '' },
              t.detalle
            )
          : null
      )
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Línea de tiempo del envío                                                    */
/* -------------------------------------------------------------------------- */
function panelEnvio(envio) {
  const cuerpo = [];

  if (!envio) {
    cuerpo.push(
      vacio('Todavía no hay envíos registrados. Crea uno desde el módulo de Logística.')
    );
  } else {
    const iconosEtapa = {
      Finca: 'lotes',
      Beneficio: 'calidad',
      'Puerto origen': 'logistica',
      'Tránsito marítimo': 'logistica',
      'Aduana UE': 'documento',
      Cliente: 'comercial',
    };
    cuerpo.push(
      el(
        'div.timeline',
        {},
        ...envio.etapas.map((etapa) =>
          el(
            `div.t-step.${etapa.estado}`,
            { title: etapa.ubicacion || '' },
            el('div.t-dot', {}, etapa.estado === 'done' ? '✓' : etapa.estado === 'current' ? '●' : ''),
            el('div.t-step-label', {}, etapa.etapa),
            etapa.fecha ? el('div.small.muted', {}, f.fechaCorta(etapa.fecha)) : null
          )
        )
      )
    );
    cuerpo.push(
      el(
        'dl.mt-2',
        {},
        el('dt', {}, 'Transporte'),
        el('dd', {}, envio.transporte),
        el('dt', {}, 'Seguimiento'),
        el('dd.mono', {}, envio.numero_seguimiento),
        el('dt', {}, 'Ruta'),
        el('dd', {}, `${envio.puerto_origen || '—'} → ${envio.puerto_destino || '—'}`),
        el('dt', {}, 'Salida'),
        el('dd', {}, f.fecha(envio.fecha_salida)),
        el('dt', {}, 'Llegada estimada'),
        el('dd', {}, f.fecha(envio.fecha_llegada)),
        el('dt', {}, 'Estado'),
        el('dd', {}, pill(envio.estado))
      )
    );
  }

  return el(
    'div.panel',
    {},
    el(
      'div.panel-head',
      {},
      el('h3', {}, envio ? envio.etiqueta : 'Seguimiento del envío'),
      envio ? el('span.status.azul', {}, envio.estado) : null
    ),
    ...cuerpo
  );
}

/* -------------------------------------------------------------------------- */
/* Cumplimiento normativo                                                      */
/* -------------------------------------------------------------------------- */
const COLOR_BARRA = {
  EUDR: 'var(--eu-blue)',
  Orgánico: 'var(--leaf)',
  Fairtrade: 'var(--gold)',
};

function panelCumplimiento(items) {
  return el(
    'div.panel',
    {},
    el('div.panel-head', {}, el('h3', {}, 'Cumplimiento normativo')),
    ...items.map((item) =>
      el(
        'div.comp-item',
        {},
        el(
          'div.comp-top',
          {},
          el('span', {}, item.normativa),
          el('span.mono', {}, `${item.porcentaje}%`)
        ),
        el(
          'div.bar-track',
          {},
          el('div.bar-fill', {
            style: {
              width: `${item.porcentaje}%`,
              background: COLOR_BARRA[item.normativa] || 'var(--gold)',
            },
          })
        ),
        el(
          'div.comp-note',
          {},
          item.detalle,
          item.vencen_pronto
            ? ` · ${item.vencen_pronto} por renovar`
            : ''
        )
      )
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Pedidos recientes                                                            */
/* -------------------------------------------------------------------------- */
function panelPedidos(pedidos) {
  if (!pedidos.length) {
    return el(
      'div.panel',
      {},
      el('div.panel-head', {}, el('h3', {}, 'Pedidos recientes')),
      vacio('Aún no hay exportaciones registradas.')
    );
  }

  return el(
    'div.panel',
    {},
    el(
      'div.panel-head',
      {},
      el('h3', {}, 'Pedidos recientes'),
      el('a.panel-link', { href: '#/comercial' }, 'Ver todos →')
    ),
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
            el('th', {}, 'Cliente'),
            el('th', {}, 'Producto'),
            el('th', {}, 'Estado'),
            el('th.tnum', {}, 'Valor')
          )
        ),
        el(
          'tbody',
          {},
          ...pedidos.map((p) =>
            el(
              'tr',
              {},
              el(
                'td',
                {},
                el('div.cell-main', {}, p.cliente),
                el('div.cell-sub', {}, p.cliente_pais)
              ),
              el(
                'td',
                {},
                el('div', {}, p.producto),
                el('div.cell-sub', {}, f.toneladas(p.cantidad_kg))
              ),
              el('td', {}, pill(p.estado)),
              el('td.tnum.mono', {}, f.moneda(p.valor, p.moneda))
            )
          )
        )
      )
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Ficha de lote (el ticket con troquel)                                        */
/* -------------------------------------------------------------------------- */
const CLASE_TAG = {
  EUDR: 'eudr',
  Orgánico: 'organic',
  Fairtrade: 'fair',
  'Rainforest Alliance': 'fair',
};

function panelFichaLote(ficha) {
  if (!ficha) {
    return el(
      'div.panel',
      {},
      el('div.panel-head', {}, el('h3', {}, 'Ficha de lote')),
      vacio('No hay lotes registrados.')
    );
  }

  const vigente = ficha.certificaciones.filter((c) => c.estado === 'Vigente');

  return el(
    'div.panel',
    {},
    el(
      'div.panel-head',
      {},
      el('h3', {}, 'Ficha de lote'),
      el('span.panel-link', { onclick: () => { location.hash = '#/lotes'; } }, 'Ver lotes →')
    ),
    el(
      'div.ticket',
      {},
      el(
        'div.ticket-row',
        {},
        el('div.ticket-code', {}, 'Lote', el('br'), el('b.mono', {}, ficha.codigo_lote)),
        el(
          'div.ticket-stamp',
          { class: vigente.length ? '' : 'rust' },
          vigente.length === ficha.certificaciones.length && ficha.certificaciones.length
            ? 'Verificado'
            : 'Revisión'
        )
      ),
      el('div.ticket-farm', {}, ficha.finca),
      el('div.ticket-loc', {}, ficha.ubicacion),
      el(
        'div.ticket-tags',
        {},
        el('span.tag', { class: ficha.tipo_producto === 'Cacao' ? 'cacao' : 'cafe' }, ficha.tipo_producto || ''),
        el('span.tag.fair', {}, `${f.entero(ficha.peso_kg)} kg`),
        ...ficha.certificaciones.map((c) =>
          el('span.tag', { class: CLASE_TAG[c.tipo] || 'fair' }, c.tipo)
        )
      ),
      el(
        'div.ticket-loc.mt-2',
        { style: { marginBottom: 0 } },
        `${ficha.variedad || ''} · Cosecha ${f.fecha(ficha.fecha_cosecha)} · ${f.entero(ficha.disponible_kg)} kg disponibles`
      ),
      el('div.mt-1', {}, pill(ficha.estado_calidad))
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Utilidad                                                                    */
/* -------------------------------------------------------------------------- */
function rejilla(...paneles) {
  return el('div.grid2', {}, ...paneles);
}
