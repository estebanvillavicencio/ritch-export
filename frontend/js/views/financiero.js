/**
 * Módulo financiero — HU-14.
 *
 * Cartera consolidada, registro de anticipos y pagos, cartas de crédito y
 * anulación con rastro. El cliente europeo ve solo su propia cartera.
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, hoy, modal, campo,
  filaCampos, leerFormulario, ok, error, confirmar,
} from '../ui.js';

const TIPOS = ['Anticipo', 'Pago parcial', 'Pago final', 'Saldo', 'Reembolso'];
const METODOS = ['Transferencia', 'Carta de crédito', 'Cheque', 'Efectivo', 'Otro'];
const MONEDAS = ['EUR', 'USD', 'COP'];

const puedeEditar = () => sesion.puede('Administrador', 'Financiero');
const puedeAnular = () => sesion.puede('Administrador');

export async function vistaFinanciero(raiz) {
  montar(raiz, cargando('Cargando el módulo financiero…'));

  let resumen, pagos, exportaciones;
  try {
    [resumen, pagos, exportaciones] = await Promise.all([
      api.financiero.resumen(),
      api.financiero.pagos({ tamano: 100 }),
      api.comercial.exportaciones({ tamano: 100 }),
    ]);
  } catch (e) {
    montar(raiz, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    return;
  }

  const contPagos = el('div');
  const contResumen = el('div');

  const opcionesExportacion = exportaciones.items
    .filter((x) => x.estado !== 'Anulado')
    .map((x) => ({
      valor: x.id_exportacion,
      texto:
        `${x.numero_contrato || `EXP-${x.id_exportacion}`} · ` +
        `${x.cliente?.nombre_empresa || ''} · ${f.moneda(x.valor_total, x.moneda)}`,
    }));

  function pintarResumen(datos) {
    montar(contResumen, tarjetas(datos), resumenPorMoneda(datos));
  }

  function pintarPagos(lista) {
    montar(
      contPagos,
      lista.items.length
        ? tablaPagos(lista.items, refrescar)
        : vacio('No hay pagos registrados todavía.')
    );
  }

  async function refrescar() {
    const [r, p] = await Promise.all([
      api.financiero.resumen(),
      api.financiero.pagos({ tamano: 100 }),
    ]);
    resumen = r;
    pagos = p;
    pintarResumen(r);
    pintarPagos(p);
  }

  pintarResumen(resumen);
  pintarPagos(pagos);

  montar(
    raiz,
    contResumen,
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el(
          'div',
          {},
          el('h3', {}, 'Pagos y anticipos'),
          el('p.muted.small', { style: { margin: '4px 0 0' } },
            `${pagos.total} movimiento(s) · moneda del contrato y conversión a EUR`)
        ),
        puedeEditar()
          ? el(
              'button.btn.btn-primary.btn-sm',
              { onclick: () => formularioPago(opcionesExportacion, refrescar) },
              icono('mas'),
              'Registrar pago'
            )
          : null
      ),
      contPagos
    ),
    resumen.por_exportacion.length
      ? el(
          'div.panel',
          { style: { marginTop: '14px' } },
          el('div.panel-head', {}, el('h3', {}, 'Saldo por contrato')),
          tablaSaldos(resumen.por_exportacion)
        )
      : null
  );
}

/* -------------------------------------------------------------------------- */
/* Resumen                                                                     */
/* -------------------------------------------------------------------------- */
function tarjetas(datos) {
  const items = [
    ['Contratado', f.euros(datos.total_contratado), 'Valor de los contratos vigentes'],
    ['Cobrado', f.euros(datos.total_cobrado), `${datos.pagos_confirmados} pago(s) confirmado(s)`],
    ['Pendiente', f.euros(datos.total_pendiente), `${datos.contratos_con_saldo} contrato(s) con saldo`, 'oro'],
    ['Cartera vencida', f.euros(datos.cartera_vencida), 'Saldo con más de 30 días', datos.cartera_vencida > 0 ? 'rust' : ''],
  ];

  return el(
    'div.kpis',
    {},
    ...items.map(([label, valor, detalle, tono]) =>
      el(
        'div.kpi',
        {},
        el(
          'div.kpi-top',
          {},
          el('div.kpi-label', {}, label),
          el('div.kpi-icon', {}, icono('euro'))
        ),
        el('div.kpi-value', {}, valor),
        el('div.kpi-delta', { class: tono }, detalle)
      )
    )
  );
}

function resumenPorMoneda(datos) {
  if (!datos.por_moneda?.length) return null;
  return el(
    'div.panel.mb-2',
    {},
    el('div.panel-head', {}, el('h3', {}, 'Cartera por moneda')),
    el(
      'div.table-wrap',
      {},
      el(
        'table',
        {},
        el('thead', {}, el('tr', {}, ...['Moneda', 'Contratado', 'Cobrado', 'Pendiente', 'Anticipos']
          .map((t, i) => el('th', { class: i ? 'tnum' : '' }, t)))),
        el(
          'tbody',
          {},
          ...datos.por_moneda.map((m) =>
            el(
              'tr',
              {},
              el('td', {}, el('span.status.azul', {}, m.moneda)),
              el('td.tnum', {}, f.moneda(m.contratado, m.moneda)),
              el('td.tnum', {}, f.moneda(m.cobrado, m.moneda)),
              el('td.tnum', {}, f.moneda(m.pendiente, m.moneda)),
              el('td.tnum', {}, f.moneda(m.anticipos, m.moneda))
            )
          )
        )
      )
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Tablas                                                                      */
/* -------------------------------------------------------------------------- */
function tablaPagos(pagos, refrescar) {
  return el(
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
          el('th', {}, 'Contrato'),
          el('th', {}, 'Cliente'),
          el('th', {}, 'Tipo'),
          el('th', {}, 'Método'),
          el('th.tnum', {}, 'Valor'),
          el('th', {}, 'Estado'),
          puedeEditar() ? el('th', {}, 'Acciones') : null
        )
      ),
      el(
        'tbody',
        {},
        ...pagos.map((p) =>
          el(
            'tr',
            {},
            el('td', {}, f.fecha(p.fecha)),
            el('td.mono.cell-main', {}, p.numero_contrato || `EXP-${p.id_exportacion}`),
            el('td', {}, f.texto(p.cliente)),
            el('td', {}, el('span.status.gris', {}, p.tipo)),
            el('td', {}, p.metodo),
            el('td.tnum', {}, f.moneda(p.valor, p.moneda)),
            el('td', {}, pill(p.estado)),
            puedeEditar() ? el('td', {}, accionesPago(p, refrescar)) : null
          )
        )
      )
    )
  );
}

function accionesPago(pago, refrescar) {
  const nodos = [];
  if (pago.estado === 'Registrado') {
    nodos.push(
      el(
        'button.btn.btn-sm',
        {
          title: 'Confirmar el pago',
          onclick: async () => {
            try {
              await api.financiero.actualizarPago(pago.id_pago, { estado: 'Confirmado' });
              ok('Pago confirmado');
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        icono('check'),
        'Confirmar'
      )
    );
  }
  if (pago.estado !== 'Anulado' && puedeAnular()) {
    nodos.push(
      el(
        'button.btn.btn-sm.btn-danger',
        {
          title: 'Anular el pago',
          onclick: async () => {
            const seguro = await confirmar({
              titulo: 'Anular pago',
              mensaje: 'El pago dejará de contar para el saldo del contrato, pero se conserva en el historial.',
              textoOk: 'Anular',
              peligro: true,
            });
            if (!seguro) return;
            try {
              await api.financiero.anularPago(pago.id_pago);
              ok('Pago anulado');
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Anular'
      )
    );
  }
  return nodos.length ? el('div.flex', {}, ...nodos) : el('span.muted', {}, '—');
}

function tablaSaldos(filas) {
  return el(
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
          el('th', {}, 'Contrato'),
          el('th', {}, 'Cliente'),
          el('th', {}, 'Estado'),
          el('th.tnum', {}, 'Valor total'),
          el('th.tnum', {}, 'Cobrado'),
          el('th.tnum', {}, 'Pendiente'),
          el('th', {}, 'Avance')
        )
      ),
      el(
        'tbody',
        {},
        ...filas.map((x) =>
          el(
            'tr',
            {},
            el('td.mono.cell-main', {}, x.numero_contrato || `EXP-${x.id_exportacion}`),
            el('td', {}, x.cliente),
            el('td', {}, pill(x.estado)),
            el('td.tnum', {}, f.moneda(x.valor_total, x.moneda)),
            el('td.tnum', {}, f.moneda(x.cobrado, x.moneda)),
            el('td.tnum', {}, f.moneda(x.pendiente, x.moneda)),
            el(
              'td',
              {},
              el(
                'div',
                { style: { display: 'flex', alignItems: 'center', gap: '8px', minWidth: '120px' } },
                el(
                  'div',
                  {
                    style: {
                      flex: '1', height: '6px', borderRadius: '999px',
                      background: 'var(--paper-2)', overflow: 'hidden',
                    },
                  },
                  el('div', {
                    style: {
                      width: `${Math.min(100, x.porcentaje)}%`, height: '100%',
                      background: 'var(--leaf)',
                    },
                  })
                ),
                el('span.small.muted', {}, `${x.porcentaje}%`)
              )
            )
          )
        )
      )
    )
  );
}

/* -------------------------------------------------------------------------- */
/* Formulario                                                                  */
/* -------------------------------------------------------------------------- */
function formularioPago(opcionesExportacion, refrescar) {
  if (!opcionesExportacion.length) {
    error('No hay contratos disponibles para registrar pagos');
    return;
  }

  const cuerpo = el(
    'form#form-pago',
    {},
    filaCampos(
      campo({
        etiqueta: 'Contrato', nombre: 'id_exportacion', tipo: 'select',
        opciones: opcionesExportacion, requerido: true,
      }),
      campo({ etiqueta: 'Fecha', nombre: 'fecha', tipo: 'date', valor: hoy(), requerido: true }),
      campo({
        etiqueta: 'Tipo', nombre: 'tipo', tipo: 'select',
        opciones: TIPOS, valor: 'Anticipo', requerido: true,
      })
    ),
    filaCampos(
      campo({
        etiqueta: 'Método', nombre: 'metodo', tipo: 'select',
        opciones: METODOS, valor: 'Transferencia', requerido: true,
      }),
      campo({
        etiqueta: 'Valor', nombre: 'valor', tipo: 'number', requerido: true,
        atributos: { min: '0.01', step: '0.01' },
      }),
      campo({
        etiqueta: 'Moneda', nombre: 'moneda', tipo: 'select',
        opciones: MONEDAS, valor: 'EUR', requerido: true,
      })
    ),
    filaCampos(
      campo({ etiqueta: 'Referencia', nombre: 'referencia', placeholder: 'RF-2026-0001' }),
      campo({ etiqueta: 'Banco', nombre: 'banco', placeholder: 'Bancolombia' })
    ),
    campo({ etiqueta: 'Observaciones', nombre: 'observaciones', tipo: 'textarea' })
  );

  const { cerrar } = modal({
    titulo: 'Registrar pago',
    cuerpo,
    pie: [
      el('button.btn', { type: 'button', onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          type: 'button',
          onclick: async () => {
            if (!cuerpo.reportValidity()) return;
            const datos = leerFormulario(cuerpo);
            datos.id_exportacion = Number(datos.id_exportacion);
            datos.valor = Number(datos.valor);
            try {
              await api.financiero.crearPago(datos);
              cerrar();
              ok('Pago registrado');
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Guardar'
      ),
    ],
  });
}
