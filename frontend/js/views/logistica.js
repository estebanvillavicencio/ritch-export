/**
 * Módulo de Logística: contenedores, envíos y seguimiento.
 *
 * Cubre HU-11 (gestión aduanera), HU-12 (transporte, contenedores y rutas)
 * y HU-13 (tracking).
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, modal, campo,
  filaCampos, leerFormulario, ok, error,
} from '../ui.js';

const TIPOS_CONTENEDOR = ['20GP', '40GP', '40HC', '20RF', '40RF', 'LCL'];
const TIPOS_TRANSPORTE = ['Marítimo', 'Aéreo', 'Terrestre'];
const ESTADOS_ENVIO = [
  'Programado', 'En tránsito', 'En aduana', 'En destino', 'Entregado',
  'Demorado', 'Incidencia',
];

const puedeEditar = () => sesion.puede('Administrador', 'Logística');

export async function vistaLogistica(raiz) {
  montar(raiz, cargando('Cargando el módulo de logística…'));

  let envios, contenedores, exportaciones;
  try {
    [envios, contenedores, exportaciones] = await Promise.all([
      api.logistica.envios({ tamano: 100 }),
      api.logistica.contenedores({ tamano: 100 }),
      api.comercial.exportaciones({ tamano: 100 }),
    ]);
  } catch (e) {
    montar(raiz, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    return;
  }

  // Se recalculan al crear un contenedor para que el selector de envíos
  // incluya el recién registrado.
  let opcionesContenedor = opcionesDeContenedores(contenedores.items);
  const opcionesExportacion = exportaciones.items.map((x) => ({
    valor: x.id_exportacion,
    texto: `${x.numero_contrato || `EXP-${x.id_exportacion}`} · ${x.cliente?.nombre_empresa || ''} · ${f.toneladas(x.total_kg)}`,
  }));

  const contEnvios = el('div');
  const contCont = el('div');

  async function refrescarEnvios() {
    const datos = await api.logistica.envios({ tamano: 100 });
    montar(
      contEnvios,
      datos.items.length
        ? tablaEnvios(datos.items, refrescarEnvios)
        : vacio('No hay envíos registrados.')
    );
  }

  async function refrescarContenedores() {
    const datos = await api.logistica.contenedores({ tamano: 100 });
    contenedores.items = datos.items;
    opcionesContenedor = opcionesDeContenedores(contenedores.items);
    montar(
      contCont,
      contenedores.items.length
        ? tablaContenedores(contenedores.items)
        : vacio('No hay contenedores registrados.')
    );
  }

  montar(
    raiz,
    el(
      'div.panel.mb-2',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Contenedores'),
        puedeEditar()
          ? el(
              'button.btn.btn-primary.btn-sm',
              { onclick: () => formContenedor() },
              icono('mas'),
              'Nuevo contenedor'
            )
          : null
      ),
      contCont
    ),
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Envíos y seguimiento'),
        el(
          'div.flex',
          {},
          el('span.small.muted', {}, `${envios.total} envíos`),
          puedeEditar()
            ? el(
                'button.btn.btn-primary.btn-sm',
                {
                  onclick: () => formEnvio(opcionesExportacion, opcionesContenedor, refrescarEnvios),
                },
                icono('mas'),
                'Nuevo envío'
              )
            : null
        )
      ),
      contEnvios
    )
  );

  refrescarContenedores();
  refrescarEnvios();
}

/* -------------------------------------------------------------------------- */
/* Utilidades                                                                  */
/* -------------------------------------------------------------------------- */

/** Opciones del selector de contenedores. */
function opcionesDeContenedores(contenedores) {
  return contenedores.map((c) => ({
    valor: c.id_contenedor,
    texto:
      `${c.codigo} · ${c.tipo} · ${f.entero(c.capacidad_kg)} kg` +
      (c.disponible ? '' : ' (ocupado)'),
  }));
}

/* -------------------------------------------------------------------------- */
/* Contenedores                                                                */
/* -------------------------------------------------------------------------- */
function tablaContenedores(contenedores) {
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
          el('th', {}, 'Código'),
          el('th', {}, 'Tipo'),
          el('th', {}, 'Naviera'),
          el('th.tnum', {}, 'Capacidad'),
          el('th', {}, 'Disponibilidad')
        )
      ),
      el(
        'tbody',
        {},
        ...contenedores.map((c) =>
          el(
            'tr',
            {},
            el('td.mono.cell-main', {}, c.codigo),
            el('td', {}, el('span.status.gris', {}, c.tipo)),
            el('td', {}, f.texto(c.naviera)),
            el('td.tnum', {}, f.kilos(c.capacidad_kg)),
            el('td', {}, c.disponible ? pill('Vigente') : pill('Ocupado'))
          )
        )
      )
    )
  );
}

function formContenedor() {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    filaCampos(
      campo({ etiqueta: 'Código', nombre: 'codigo', requerido: true, placeholder: 'CNT-2026-0422' }),
      campo({ etiqueta: 'Tipo', nombre: 'tipo', tipo: 'select', opciones: TIPOS_CONTENEDOR, valor: '40HC' })
    ),
    filaCampos(
      campo({ etiqueta: 'Capacidad (kg)', nombre: 'capacidad_kg', tipo: 'number', min: '1', step: '0.01', valor: '26400', requerido: true }),
      campo({ etiqueta: 'Naviera', nombre: 'naviera', placeholder: 'Maersk, Hapag-Lloyd…' })
    )
  );

  const { cerrar } = modal({
    titulo: 'Nuevo contenedor',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.codigo || !d.capacidad_kg) return error('Código y capacidad son obligatorios');
            try {
              await api.logistica.crearContenedor({
                codigo: d.codigo,
                tipo: d.tipo,
                capacidad_kg: d.capacidad_kg,
                naviera: d.naviera || null,
              });
              ok('Contenedor registrado');
              cerrar();
              location.reload();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Registrar'
      ),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Envíos                                                                      */
/* -------------------------------------------------------------------------- */
function tablaEnvios(envios, refrescar) {
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
          el('th', {}, 'Seguimiento'),
          el('th', {}, 'Cliente'),
          el('th', {}, 'Ruta'),
          el('th', {}, 'Salida'),
          el('th', {}, 'Llegada'),
          el('th', {}, 'Etapa'),
          el('th', {}, 'Estado'),
          el('th', {}, '')
        )
      ),
      el(
        'tbody',
        {},
        ...envios.map((e) =>
          el(
            'tr',
            {},
            el(
              'td',
              {},
              el('div.mono.cell-main', {}, e.numero_seguimiento),
              el('div.cell-sub', {}, `${e.transportadora} · ${e.tipo_transporte}`)
            ),
            el(
              'td',
              {},
              el('div.cell-main', {}, f.texto(e.cliente_nombre)),
              el('div.cell-sub', {}, f.texto(e.cliente_pais))
            ),
            el('td.small', {}, `${f.texto(e.puerto_origen)} → ${f.texto(e.puerto_destino)}`),
            el('td.small', {}, f.fecha(e.fecha_salida)),
            el(
              'td.small',
              {},
              f.fecha(e.fecha_llegada),
              e.dias_restantes !== null && e.dias_restantes !== undefined
                ? el('div.cell-sub', {}, `${e.dias_restantes} días`)
                : null
            ),
            el('td.small', {}, f.texto(e.etapa_actual)),
            el('td', {}, pill(e.estado)),
            el(
              'td',
              { class: 'right nowrap' },
              el(
                'div.flex',
                { style: { justifyContent: 'flex-end' } },
                el(
                  'button.btn.btn-sm',
                  { title: 'Línea de tiempo', onclick: () => verLineaTiempo(e.id_envio) },
                  icono('logistica')
                ),
                puedeEditar() && e.estado !== 'Entregado'
                  ? el(
                      'button.btn.btn-sm',
                      { title: 'Actualizar envío', onclick: () => formEnvioEstado(e, refrescar) },
                      icono('editar')
                    )
                  : null
              )
            )
          )
        )
      )
    )
  );
}

function formEnvio(opcionesExportacion, opcionesContenedor, refrescar) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({
      etiqueta: 'Exportación', nombre: 'id_exportacion', tipo: 'select',
      opciones: opcionesExportacion, requerido: true,
    }),
    filaCampos(
      campo({ etiqueta: 'Transportadora', nombre: 'transportadora', requerido: true, placeholder: 'Maersk' }),
      campo({ etiqueta: 'Número de seguimiento', nombre: 'numero_seguimiento', requerido: true, placeholder: 'MAEU-4471288' })
    ),
    filaCampos(
      campo({ etiqueta: 'Tipo de transporte', nombre: 'tipo_transporte', tipo: 'select', opciones: TIPOS_TRANSPORTE, valor: 'Marítimo' }),
      campo({ etiqueta: 'Estado', nombre: 'estado', tipo: 'select', opciones: ESTADOS_ENVIO, valor: 'Programado' })
    ),
    filaCampos(
      campo({ etiqueta: 'Puerto de origen', nombre: 'puerto_origen', placeholder: 'Cartagena' }),
      campo({ etiqueta: 'Puerto de destino', nombre: 'puerto_destino', placeholder: 'Rotterdam' })
    ),
    filaCampos(
      campo({ etiqueta: 'Fecha de salida', nombre: 'fecha_salida', tipo: 'date' }),
      campo({ etiqueta: 'Fecha estimada de llegada', nombre: 'fecha_llegada', tipo: 'date' })
    ),
    campo({
      etiqueta: 'Contenedor', nombre: 'id_contenedor', tipo: 'select',
      opciones: [{ valor: '', texto: 'Sin asignar' }, ...opcionesContenedor],
    }),
    campo({ etiqueta: 'Costo del flete', nombre: 'costo_flete', tipo: 'number', min: '0', step: '0.01' })
  );

  const { cerrar } = modal({
    titulo: 'Nuevo envío',
    ancho: 'wide',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.id_exportacion || !d.transportadora || !d.numero_seguimiento) {
              return error('Exportación, transportadora y seguimiento son obligatorios');
            }
            try {
              await api.logistica.crearEnvio({
                id_exportacion: Number(d.id_exportacion),
                transportadora: d.transportadora,
                numero_seguimiento: d.numero_seguimiento,
                tipo_transporte: d.tipo_transporte,
                estado: d.estado,
                puerto_origen: d.puerto_origen || null,
                puerto_destino: d.puerto_destino || null,
                fecha_salida: d.fecha_salida || null,
                fecha_llegada: d.fecha_llegada || null,
                id_contenedor: d.id_contenedor ? Number(d.id_contenedor) : null,
                costo_flete: d.costo_flete || null,
              });
              ok('Envío registrado');
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Registrar envío'
      ),
    ],
  });
}

function formEnvioEstado(envio, refrescar) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    el('p.small.muted.mt-0', {}, `Envío ${envio.numero_seguimiento} · estado actual: ${envio.estado}`),
    campo({ etiqueta: 'Nuevo estado', nombre: 'estado', tipo: 'select', opciones: ESTADOS_ENVIO, valor: envio.estado, requerido: true }),
    filaCampos(
      campo({ etiqueta: 'Fecha de salida', nombre: 'fecha_salida', tipo: 'date', valor: (envio.fecha_salida || '').slice(0, 10) }),
      campo({ etiqueta: 'Fecha de llegada', nombre: 'fecha_llegada', tipo: 'date', valor: (envio.fecha_llegada || '').slice(0, 10) })
    ),
    campo({ etiqueta: 'Observación de incidencia', nombre: '_nota' })
  );

  const { cerrar } = modal({
    titulo: 'Actualizar envío',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            const cuerpo = { estado: d.estado };
            if (d.fecha_salida) cuerpo.fecha_salida = d.fecha_salida;
            if (d.fecha_llegada) cuerpo.fecha_llegada = d.fecha_llegada;
            try {
              await api.logistica.actualizarEnvio(envio.id_envio, cuerpo);
              ok('Envío actualizado');
              cerrar();
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

async function verLineaTiempo(idEnvio) {
  const { cerrar } = modal({ titulo: 'Línea de tiempo del envío', cuerpo: cargando(), ancho: 'wide' });
  try {
    const [envio, etapas] = await Promise.all([
      api.logistica.verEnvio(idEnvio),
      api.logistica.trazabilidadEnvio(idEnvio),
    ]);

    const cuerpo = el(
      'div',
      {},
      el(
        'div.timeline',
        {},
        ...etapas.map((e) =>
          el(
            `div.t-step.${e.estado}`,
            { title: e.ubicacion || '' },
            el('div.t-dot', {}, e.estado === 'done' ? '✓' : e.estado === 'current' ? '●' : ''),
            el('div.t-step-label', {}, e.etapa),
            e.fecha ? el('div.small.muted', {}, f.fechaCorta(e.fecha)) : null
          )
        )
      ),
      el(
        'dl.mt-2',
        {},
        el('dt', {}, 'Transportadora'), el('dd', {}, envio.transportadora),
        el('dt', {}, 'Seguimiento'), el('dd.mono', {}, envio.numero_seguimiento),
        el('dt', {}, 'Ruta'), el('dd', {}, `${envio.puerto_origen || '—'} → ${envio.puerto_destino || '—'}`),
        el('dt', {}, 'Salida'), el('dd', {}, f.fecha(envio.fecha_salida)),
        el('dt', {}, 'Llegada'), el('dd', {}, f.fecha(envio.fecha_llegada)),
        el('dt', {}, 'Días de tránsito'), el('dd', {}, envio.dias_transito ?? '—'),
        el('dt', {}, 'Estado'), el('dd', {}, pill(envio.estado))
      )
    );
    const caja = document.querySelector('.modal-backdrop .modal-body');
    if (caja) montar(caja, cuerpo);
  } catch (e) {
    error(e.message);
    cerrar();
  }
}
