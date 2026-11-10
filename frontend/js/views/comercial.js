/**
 * Módulo Comercial: clientes europeos, cotizaciones, exportaciones y documentos.
 *
 * Cubre HU-03 (clientes UE), HU-08 (cotizaciones y contratos),
 * HU-09 (pedidos), HU-10 (documentación) y HU-11 (gestión aduanera).
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, hoy, modal, campo,
  filaCampos, leerFormulario, ok, error,
} from '../ui.js';

const INCOTERMS = ['EXW', 'FCA', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP', 'FAS', 'FOB', 'CFR', 'CIF'];
const MONEDAS = ['EUR', 'USD', 'COP'];
const TIPOS_DOC = [
  'Factura comercial', 'Packing list', 'Certificado de origen', 'BL', 'AWB',
  'Certificado', 'Documento aduanero',
];
const ESTADOS_DOC = ['Borrador', 'Emitido', 'Validado', 'Anulado'];

const puedeEditar = () => sesion.puede('Administrador', 'Comercial');

export async function vistaComercial(raiz) {
  montar(raiz, cargando('Cargando el módulo comercial…'));

  let cotizaciones, exportaciones, clientes;
  try {
    [cotizaciones, exportaciones, clientes] = await Promise.all([
      api.comercial.cotizaciones({ tamano: 100 }),
      api.comercial.exportaciones({ tamano: 100 }),
      api.catalogos.clientes({ tamano: 100 }),
    ]);
  } catch (e) {
    montar(raiz, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    return;
  }

  // Se recalculan al crear un cliente para que los selectores de
  // cotización y exportación incluyan al recién registrado.
  let opcionesCliente = opcionesDeClientes(clientes.items);

  const contCot = el('div');
  const contExp = el('div');
  const contCli = el('div');
  const contSolicitudes = el('div');

  async function refrescarSolicitudes() {
    if (!puedeEditar()) return;
    const datos = await api.comercial.solicitudesPedido();
    montar(contSolicitudes, datos.length ? tablaSolicitudesPedido(datos) : vacio('No hay solicitudes de pedido de clientes.'));
  }

  async function refrescarCotizaciones() {
    const datos = await api.comercial.cotizaciones({ tamano: 100 });
    montar(
      contCot,
      datos.items.length
        ? tablaCotizaciones(datos.items, refrescarCotizaciones, opcionesCliente)
        : vacio('No hay cotizaciones registradas.')
    );
  }

  async function refrescarExportaciones() {
    const datos = await api.comercial.exportaciones({ tamano: 100 });
    montar(
      contExp,
      datos.items.length
        ? tablaExportaciones(datos.items, refrescarExportaciones)
        : vacio('No hay exportaciones registradas.')
    );
  }

  async function refrescarClientes() {
    const datos = await api.catalogos.clientes({ tamano: 100 });
    clientes.items = datos.items;
    opcionesCliente = opcionesDeClientes(clientes.items);
    montar(
      contCli,
      clientes.items.length
        ? tablaClientes(clientes.items, refrescarClientes)
        : vacio('No hay clientes registrados.')
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
        el('h3', {}, 'Clientes de la Unión Europea'),
        puedeEditar()
          ? el(
              'button.btn.btn-primary.btn-sm',
              { onclick: () => formCliente(refrescarClientes) },
              icono('mas'),
              'Nuevo cliente'
            )
          : null
      ),
      contCli
    ),
    el(
      'div.panel.mb-2',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Cotizaciones'),
        el(
          'div.flex',
          {},
          el('span.small.muted', {}, `${cotizaciones.total} cotizaciones`),
          puedeEditar()
            ? el(
                'button.btn.btn-primary.btn-sm',
                { onclick: () => formCotizacion(refrescarCotizaciones, opcionesCliente) },
                icono('mas'),
                'Nueva cotización'
              )
            : null
        )
      ),
      contCot
    ),
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Exportaciones y pedidos'),
        el(
          'div.flex',
          {},
          el('span.small.muted', {}, `${exportaciones.total} exportaciones`),
          puedeEditar()
            ? el(
                'button.btn.btn-primary.btn-sm',
                { onclick: () => formExportacion(refrescarExportaciones, opcionesCliente) },
                icono('mas'),
                'Nueva exportación'
              )
            : null
        )
      ),
      contExp
    ),
    puedeEditar()
      ? el('div.panel.mt-2', {},
          el('div.panel-head', {}, el('h3', {}, 'Solicitudes recibidas del portal')),
          contSolicitudes
        )
      : null
  );

  await refrescarClientes();
  refrescarCotizaciones();
  refrescarExportaciones();
  refrescarSolicitudes();
}

function tablaSolicitudesPedido(solicitudes) {
  return el('div.table-wrap', {}, el('table', {},
    el('thead', {}, el('tr', {}, el('th', {}, 'Solicitud'), el('th', {}, 'Cliente'),
      el('th', {}, 'Fecha'), el('th', {}, 'Producto'), el('th.tnum', {}, 'Cantidad'),
      el('th', {}, 'Incoterm'), el('th', {}, 'Destino'), el('th', {}, 'Estado'))),
    el('tbody', {}, ...solicitudes.map((s) => el('tr', {},
      el('td.mono.cell-main', {}, `SOL-${String(s.id_solicitud).padStart(5, '0')}`),
      el('td.small', {}, s.empresa), el('td.small', {}, f.fecha(s.created_at)),
      el('td.small', {}, s.producto_nombre), el('td.tnum', {}, f.kilos2(Number(s.cantidad_kg))),
      el('td', {}, s.incoterm), el('td.small', {}, f.texto(s.puerto_destino)), el('td', {}, pill(s.estado))
    )))
  ));
}

/* -------------------------------------------------------------------------- */
/* Utilidades                                                                  */
/* -------------------------------------------------------------------------- */

/** Opciones del selector de clientes: «Empresa · País». */
function opcionesDeClientes(clientes) {
  return clientes.map((c) => ({
    valor: c.id_cliente,
    texto: `${c.nombre_empresa} · ${c.pais}`,
  }));
}

/* -------------------------------------------------------------------------- */
/* Clientes                                                                    */
/* -------------------------------------------------------------------------- */
function tablaClientes(clientes, refrescar) {
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
          el('th', {}, 'Empresa'),
          el('th', {}, 'País'),
          el('th', {}, 'Puerto de destino'),
          el('th', {}, 'Contacto'),
          el('th', {}, 'Moneda'),
          el('th', {}, 'Estado')
        )
      ),
      el(
        'tbody',
        {},
        ...clientes.map((c) =>
          el(
            'tr',
            {},
            el(
              'td',
              {},
              el('div.cell-main', {}, c.nombre_empresa),
              el('div.cell-sub', {}, c.vat || c.correo || '—')
            ),
            el('td', {}, c.pais),
            el('td', {}, f.texto(c.puerto_destino)),
            el('td', {}, f.texto(c.contacto)),
            el('td.mono', {}, c.moneda_preferida),
            el('td', {}, c.activo ? pill('Vigente') : pill('Anulado'))
          )
        )
      )
    )
  );
}

function formCliente(refrescar) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({ etiqueta: 'Nombre de la empresa', nombre: 'nombre_empresa', requerido: true }),
    filaCampos(
      campo({ etiqueta: 'País', nombre: 'pais', requerido: true, placeholder: 'Alemania, Países Bajos…' }),
      campo({ etiqueta: 'VAT', nombre: 'vat', placeholder: 'DE8145092' })
    ),
    campo({ etiqueta: 'Dirección', nombre: 'direccion' }),
    filaCampos(
      campo({ etiqueta: 'Correo', nombre: 'correo', tipo: 'email' }),
      campo({ etiqueta: 'Teléfono', nombre: 'telefono' })
    ),
    filaCampos(
      campo({ etiqueta: 'Persona de contacto', nombre: 'contacto' }),
      campo({ etiqueta: 'Puerto de destino', nombre: 'puerto_destino' })
    ),
    campo({
      etiqueta: 'Moneda preferida', nombre: 'moneda_preferida', tipo: 'select',
      opciones: MONEDAS, valor: 'EUR',
    })
  );

  const { cerrar } = modal({
    titulo: 'Nuevo cliente importador',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.nombre_empresa || !d.pais) return error('Nombre y país son obligatorios');
            try {
              await api.catalogos.crearCliente({
                nombre_empresa: d.nombre_empresa,
                pais: d.pais,
                vat: d.vat || null,
                direccion: d.direccion || null,
                correo: d.correo || null,
                telefono: d.telefono || null,
                contacto: d.contacto || null,
                puerto_destino: d.puerto_destino || null,
                moneda_preferida: d.moneda_preferida || 'EUR',
              });
              ok('Cliente registrado');
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Registrar cliente'
      ),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Cotizaciones                                                                */
/* -------------------------------------------------------------------------- */
function tablaCotizaciones(cotizaciones, refrescar, opcionesCliente) {
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
          el('th', {}, 'Número'),
          el('th', {}, 'Cliente'),
          el('th', {}, 'Producto'),
          el('th.tnum', {}, 'Cantidad'),
          el('th', {}, 'Incoterm'),
          el('th.tnum', {}, 'Valor'),
          el('th', {}, 'Estado'),
          el('th', {}, '')
        )
      ),
      el(
        'tbody',
        {},
        ...cotizaciones.map((c) =>
          el(
            'tr',
            {},
            el('td.mono.cell-main', {}, c.numero),
            el(
              'td',
              {},
              el('div.cell-main', {}, c.cliente?.nombre_empresa || '—'),
              el('div.cell-sub', {}, c.cliente?.pais || '')
            ),
            el('td.mono', {}, `${f.moneda(c.precio_kg, c.moneda)}/kg`),
            el('td.tnum', {}, f.kilos(c.cantidad_kg)),
            el('td', {}, el('span.status.gris', {}, c.incoterm)),
            el('td.tnum', {}, f.moneda(c.valor_total, c.moneda)),
            el('td', {}, pill(c.estado)),
            el(
              'td',
              { class: 'right nowrap' },
              el(
                'div.flex',
                { style: { justifyContent: 'flex-end' } },
                puedeEditar() && c.estado !== 'Aceptada' && c.estado !== 'Rechazada'
                  ? el(
                      'button.btn.btn-sm',
                      {
                        title: 'Marcar como enviada',
                        onclick: async () => {
                          try {
                            await api.comercial.actualizarCotizacion(c.id_cotizacion, { estado: 'Enviada' });
                            ok('Cotización enviada');
                            refrescar();
                          } catch (e) {
                            error(e.message);
                          }
                        },
                      },
                      'Enviar'
                    )
                  : null,
                puedeEditar() && ['Enviada', 'Aceptada'].includes(c.estado)
                  ? el(
                      'button.btn.btn-gold.btn-sm',
                      { onclick: () => aceptarCotizacion(c, refrescar) },
                      'Aceptar'
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

function formCotizacion(refrescar, opcionesCliente) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({ etiqueta: 'Cliente', nombre: 'id_cliente', tipo: 'select', opciones: opcionesCliente, requerido: true }),
    filaCampos(
      campo({ etiqueta: 'Cantidad (kg)', nombre: 'cantidad_kg', tipo: 'number', min: '1', step: '0.01', requerido: true }),
      campo({ etiqueta: 'Precio por kg', nombre: 'precio_kg', tipo: 'number', min: '0.01', step: '0.01', requerido: true })
    ),
    filaCampos(
      campo({ etiqueta: 'Moneda', nombre: 'moneda', tipo: 'select', opciones: MONEDAS, valor: 'EUR' }),
      campo({ etiqueta: 'Incoterm', nombre: 'incoterm', tipo: 'select', opciones: INCOTERMS, valor: 'FOB' })
    ),
    filaCampos(
      campo({ etiqueta: 'Puerto de origen', nombre: 'puerto_origen', placeholder: 'Cartagena' }),
      campo({ etiqueta: 'Puerto de destino', nombre: 'puerto_destino', placeholder: 'Rotterdam' })
    ),
    filaCampos(
      campo({ etiqueta: 'Fecha', nombre: 'fecha', tipo: 'date', valor: hoy(), requerido: true }),
      campo({ etiqueta: 'Validez (días)', nombre: 'validez_dias', tipo: 'number', valor: '15', min: '1', max: '365' })
    ),
    campo({ etiqueta: 'Observaciones', nombre: 'observaciones', tipo: 'textarea' })
  );

  const { cerrar } = modal({
    titulo: 'Nueva cotización',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.id_cliente || !d.cantidad_kg || !d.precio_kg) {
              return error('Cliente, cantidad y precio son obligatorios');
            }
            try {
              await api.comercial.crearCotizacion({
                id_cliente: Number(d.id_cliente),
                cantidad_kg: d.cantidad_kg,
                precio_kg: d.precio_kg,
                moneda: d.moneda,
                incoterm: d.incoterm,
                fecha: d.fecha,
                validez_dias: Number(d.validez_dias) || 15,
                puerto_origen: d.puerto_origen || null,
                puerto_destino: d.puerto_destino || null,
                observaciones: d.observaciones || null,
              });
              ok('Cotización creada');
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Crear cotización'
      ),
    ],
  });
}

async function aceptarCotizacion(cotizacion, refrescar) {
  const loteDatos = await api.lotes.listar({ solo_disponibles: true, tamano: 100 });
  if (!loteDatos.items.length) {
    return error('No hay lotes con saldo disponible para comprometer');
  }

  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    el(
      'p.small.muted.mt-0',
      {},
      `Convierte la cotización ${cotizacion.numero} en un contrato de exportación. `,
      'Selecciona los lotes y los kilos a asignar.'
    ),
    campo({
      etiqueta: 'Lotes a comprometer',
      nombre: 'lotes',
      tipo: 'select',
      opciones: loteDatos.items.map((l) => ({
        valor: l.codigo_lote,
        texto: `${l.codigo_lote} · ${f.kilos(l.disponible_kg)} disponibles`,
      })),
      requerido: true,
      pista: 'Por ahora se asigna un único lote; repite la operación para varios.',
    }),
    campo({
      etiqueta: 'Cantidad a asignar (kg)', nombre: 'cantidad_default', tipo: 'number',
      min: '0.01', step: '0.01', valor: String(cotizacion.cantidad_kg), requerido: true,
    })
  );

  const { cerrar } = modal({
    titulo: `Aceptar cotización ${cotizacion.numero}`,
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-gold',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.lotes || !d.cantidad_default) return error('Indica lote y cantidad');
            try {
              const exp = await api.comercial.aceptarCotizacion(cotizacion.id_cotizacion, {
                lotes: [d.lotes],
                cantidad_default: d.cantidad_default,
              });
              ok(`Exportación ${exp.numero_contrato} creada`);
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Crear exportación'
      ),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Exportaciones                                                                */
/* -------------------------------------------------------------------------- */
const CADENA_ESTADOS = [
  'Pedido recibido', 'En preparación', 'En producción', 'En puerto',
  'En tránsito', 'En destino', 'Entregado',
];

function tablaExportaciones(exportaciones, refrescar) {
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
          el('th', {}, 'Destino'),
          el('th.tnum', {}, 'Peso'),
          el('th.tnum', {}, 'Valor'),
          el('th', {}, 'Estado'),
          el('th', {}, '')
        )
      ),
      el(
        'tbody',
        {},
        ...exportaciones.map((x) => {
          const avance = Math.round(
            (CADENA_ESTADOS.indexOf(x.estado) / (CADENA_ESTADOS.length - 1)) * 100
          );
          return el(
            'tr',
            {},
            el(
              'td',
              {},
              el('div.mono.cell-main', {}, x.numero_contrato || `EXP-${x.id_exportacion}`),
              el('div.cell-sub', {}, f.fecha(x.fecha))
            ),
            el(
              'td',
              {},
              el('div.cell-main', {}, x.cliente?.nombre_empresa || '—'),
              el('div.cell-sub', {}, x.cliente?.pais || '')
            ),
            el('td', {}, `${f.texto(x.puerto_origen)} → ${f.texto(x.puerto_destino)}`),
            el('td.tnum', {}, f.toneladas(x.total_kg)),
            el('td.tnum', {}, f.moneda(x.valor_total, x.moneda)),
            el(
              'td',
              {},
              pill(x.estado),
              el(
                'div.bar-track',
                { style: { marginTop: '5px', width: '80px' } },
                el('div.bar-fill', {
                  style: { width: `${Math.max(avance, 4)}%`, background: 'var(--gold)' },
                })
              )
            ),
            el(
              'td',
              { class: 'right nowrap' },
              el(
                'div.flex',
                { style: { justifyContent: 'flex-end' } },
                el(
                  'button.btn.btn-sm',
                  { title: 'Detalle', onclick: () => verExportacion(x.id_exportacion) },
                  icono('documento')
                ),
                el(
                  'button.btn.btn-sm',
                  { title: 'Documentos', onclick: () => gestionDocumentos(x.id_exportacion) },
                  icono('hoja')
                ),
                el(
                  'button.btn.btn-sm',
                  { title: 'Cambiar estado', onclick: () => cambiarEstado(x, refrescar) },
                  icono('refrescar')
                )
              )
            )
          );
        })
      )
    )
  );
}

function formExportacion(refrescar, opcionesCliente) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({ etiqueta: 'Cliente', nombre: 'id_cliente', tipo: 'select', opciones: opcionesCliente, requerido: true }),
    filaCampos(
      campo({ etiqueta: 'Fecha', nombre: 'fecha', tipo: 'date', valor: hoy(), requerido: true }),
      campo({ etiqueta: 'Incoterm', nombre: 'incoterm', tipo: 'select', opciones: INCOTERMS, valor: 'FOB' })
    ),
    filaCampos(
      campo({ etiqueta: 'Puerto de origen', nombre: 'puerto_origen', placeholder: 'Cartagena' }),
      campo({ etiqueta: 'Puerto de destino', nombre: 'puerto_destino', placeholder: 'Rotterdam' })
    ),
    el('h4', { style: { fontSize: '13px', margin: '18px 0 8px' } }, 'Detalle de la exportación'),
    el('div#detalles-exp'),
    el(
      'button.btn.btn-sm.mt-1',
      { type: 'button', onclick: () => agregarLineaDetalle(document.getElementById('detalles-exp')) },
      icono('mas'),
      'Añadir lote'
    ),
    campo({ etiqueta: 'Observaciones', nombre: 'observaciones', tipo: 'textarea' })
  );

  agregarLineaDetalle(document.getElementById('detalles-exp'));

  const { cerrar } = modal({
    titulo: 'Nueva exportación / pedido',
    ancho: 'wide',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            const detalles = leerLineasDetalle();
            if (!d.id_cliente || !d.fecha) return error('Cliente y fecha son obligatorios');
            if (!detalles.length) return error('Añade al menos un lote al detalle');
            try {
              const exp = await api.comercial.crearExportacion({
                id_cliente: Number(d.id_cliente),
                fecha: d.fecha,
                incoterm: d.incoterm,
                puerto_origen: d.puerto_origen || null,
                puerto_destino: d.puerto_destino || null,
                observaciones: d.observaciones || null,
                detalles,
              });
              ok(`Exportación ${exp.numero_contrato} creada`);
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Crear exportación'
      ),
    ],
  });
}

function agregarLineaDetalle(contenedor) {
  if (!contenedor) return;
  const fila = el(
    'div.field-row.mb-1',
    {},
    el(
      'div.field',
      {},
      el('label', {}, 'Lote'),
      el(
        'select',
        { name: 'det_lote', class: 'det-lote' },
        el('option', { value: '' }, 'Cargando lotes…')
      )
    ),
    el(
      'div.field',
      {},
      el('label', {}, 'Cantidad (kg)'),
      el('input', { type: 'number', name: 'det_cantidad', min: '0.01', step: '0.01', class: 'det-cantidad' })
    ),
    el(
      'div.field',
      {},
      el('label', {}, 'Precio por kg'),
      el('input', { type: 'number', name: 'det_precio', min: '0.01', step: '0.01', class: 'det-precio' })
    ),
    el(
      'div.field',
      { style: { display: 'flex', alignItems: 'flex-end' } },
      el(
        'button.btn.btn-sm.btn-danger',
        {
          type: 'button',
          onclick: () => {
            fila.remove();
            if (!contenedor.querySelector('.det-lote')) agregarLineaDetalle(contenedor);
          },
        },
        '×'
      )
    )
  );
  contenedor.appendChild(fila);

  api.lotes.listar({ solo_disponibles: true, tamano: 100 })
    .then(({ items }) => {
      const select = fila.querySelector('.det-lote');
      montar(
        select,
        el('option', { value: '' }, 'Selecciona un lote'),
        ...items.map((l) =>
          el(
            'option',
            { value: l.id_lote, 'data-disponible': l.disponible_kg, 'data-producto': l.id_producto || '' },
            `${l.codigo_lote} · ${f.kilos(l.disponible_kg)} disp.`
          )
        )
      );
    })
    .catch(() => montar(fila.querySelector('.det-lote'), el('option', { value: '' }, 'No se pudieron cargar')));
}

function leerLineasDetalle() {
  return [...document.querySelectorAll('.det-lote')]
    .map((select) => {
      const fila = select.closest('.field-row');
      const idLote = select.value;
      const cantidad = fila.querySelector('.det-cantidad').value;
      const precio = fila.querySelector('.det-precio').value;
      if (!idLote || !cantidad || !precio) return null;
      return {
        id_lote: Number(idLote),
        cantidad_kg: cantidad,
        precio_kg: precio,
      };
    })
    .filter(Boolean);
}

async function verExportacion(idExp) {
  const { cerrar } = modal({ titulo: 'Detalle de la exportación', cuerpo: cargando(), ancho: 'wide' });
  try {
    const x = await api.comercial.verExportacion(idExp);
    const cuerpo = el(
      'div',
      {},
      el(
        'dl.mb-2',
        {},
        el('dt', {}, 'Contrato'), el('dd.mono', {}, f.texto(x.numero_contrato)),
        el('dt', {}, 'Cliente'), el('dd', {}, x.cliente?.nombre_empresa || '—'),
        el('dt', {}, 'Fecha'), el('dd', {}, f.fecha(x.fecha)),
        el('dt', {}, 'Estado'), el('dd', {}, pill(x.estado)),
        el('dt', {}, 'Incoterm'), el('dd', {}, f.texto(x.incoterm)),
        el('dt', {}, 'Ruta'), el('dd', {}, `${f.texto(x.puerto_origen)} → ${f.texto(x.puerto_destino)}`),
        el('dt', {}, 'Peso total'), el('dd', {}, f.kilos(x.total_kg)),
        el('dt', {}, 'Valor'), el('dd', {}, f.moneda(x.valor_total, x.moneda))
      ),
      el('h4', { style: { fontSize: '13px', margin: '0 0 8px' } }, 'Lotes'),
      el(
        'table',
        {},
        el('thead', {}, el('tr', {}, el('th', {}, 'Cantidad'), el('th.tnum', {}, 'Kg'), el('th.tnum', {}, 'Precio/kg'), el('th.tnum', {}, 'Subtotal'))),
        el(
          'tbody',
          {},
          ...x.detalles.map((d) =>
            el(
              'tr',
              {},
              el('td', {}, `Lote ${d.id_lote}`),
              el('td.tnum', {}, f.kilos2(d.cantidad_kg)),
              el('td.tnum', {}, f.moneda(d.precio_kg, x.moneda)),
              el('td.tnum', {}, f.moneda(d.subtotal, x.moneda))
            )
          )
        )
      ),
      el('h4', { style: { fontSize: '13px', margin: '18px 0 8px' } }, 'Documentos'),
      x.documentos.length
        ? el(
            'div',
            {},
            ...x.documentos.map((d) =>
              el(
                'div.doc-item',
                {},
                el(
                  'div',
                  {},
                  el('div.doc-main', {}, d.tipo_documento),
                  el('div.doc-sub', {}, `${d.numero_documento} · ${f.fecha(d.fecha_emision)}`)
                ),
                el('div.flex', {}, pill(d.estado), d.autorizado_cliente ? pill('Vigente') : null)
              )
            )
          )
        : vacio('Sin documentos registrados.'),
      el('h4', { style: { fontSize: '13px', margin: '18px 0 8px' } }, 'Envíos'),
      x.envios.length
        ? el(
            'div',
            {},
            ...x.envios.map((e) =>
              el(
                'div.doc-item',
                {},
                el(
                  'div',
                  {},
                  el('div.doc-main', {}, `${e.transportadora} · ${e.numero_seguimiento}`),
                  el('div.doc-sub', {}, `${f.texto(e.puerto_origen)} → ${f.texto(e.puerto_destino)} · salida ${f.fecha(e.fecha_salida)}`)
                ),
                pill(e.estado)
              )
            )
          )
        : vacio('Sin envíos registrados.')
    );
    const caja = document.querySelector('.modal-backdrop .modal-body');
    if (caja) montar(caja, cuerpo);
  } catch (e) {
    error(e.message);
    cerrar();
  }
}

function cambiarEstado(exportacion, refrescar) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    el('p.small.muted.mt-0', {}, `Estado actual: ${exportacion.estado}`),
    campo({
      etiqueta: 'Nuevo estado', nombre: 'estado', tipo: 'select', requerido: true,
      opciones: [...CADENA_ESTADOS, 'Anulado'], valor: exportacion.estado,
      pista: 'Solo se permite avanzar o retroceder un paso en la cadena de estados.',
    })
  );

  const { cerrar } = modal({
    titulo: `Cambiar estado · ${exportacion.numero_contrato || ''}`,
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            try {
              await api.comercial.actualizarExportacion(exportacion.id_exportacion, { estado: d.estado });
              ok('Estado actualizado');
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Actualizar'
      ),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Documentos                                                                  */
/* -------------------------------------------------------------------------- */
async function gestionDocumentos(idExp) {
  const { cerrar } = modal({
    titulo: 'Documentos de exportación',
    cuerpo: cargando(),
    ancho: 'wide',
    pie: [el('button.btn', { onclick: () => cerrar() }, 'Cerrar')],
  });

  async function refrescar() {
    try {
      const docs = await api.comercial.documentos(idExp);
      const cuerpo = el(
        'div',
        {},
        el(
          'div.flex-between.mb-2',
          {},
          el('span.small.muted', {}, `${docs.length} documentos registrados`),
          el(
            'button.btn.btn-primary.btn-sm',
            { onclick: () => formDocumento(idExp, refrescar) },
            icono('mas'),
            'Nuevo documento'
          )
        ),
        docs.length
          ? el(
              'div',
              {},
              ...docs.map((d) =>
                el(
                  'div.doc-item',
                  {},
                  el(
                    'div',
                    {},
                    el('div.doc-main', {}, d.tipo_documento),
                    el('div.doc-sub', {}, `${d.numero_documento} · emitido ${f.fecha(d.fecha_emision)}`)
                  ),
                  el(
                    'div.flex',
                    {},
                    pill(d.estado),
                    d.autorizado_cliente ? el('span.status.verde', {}, 'En portal') : el('span.status.gris', {}, 'No publicado'),
                    d.estado !== 'Borrador'
                      ? el(
                          'button.btn.btn-sm',
                          {
                            onclick: async () => {
                              try {
                                await api.comercial.autorizarDocumento(d.id_documento);
                                refrescar();
                              } catch (e) {
                                error(e.message);
                              }
                            },
                          },
                          d.autorizado_cliente ? 'Retirar' : 'Autorizar'
                        )
                      : null
                  )
                )
              )
            )
          : vacio('Esta exportación aún no tiene documentos.')
      );
      const caja = document.querySelector('.modal-backdrop .modal-body');
      if (caja) montar(caja, cuerpo);
    } catch (e) {
      error(e.message);
    }
  }

  refrescar();
}

function formDocumento(idExp, refrescar) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({ etiqueta: 'Tipo de documento', nombre: 'tipo_documento', tipo: 'select', opciones: TIPOS_DOC, requerido: true }),
    campo({ etiqueta: 'Número de documento', nombre: 'numero_documento', requerido: true, placeholder: 'FC-2026-0001' }),
    filaCampos(
      campo({ etiqueta: 'Fecha de emisión', nombre: 'fecha_emision', tipo: 'date', valor: hoy(), requerido: true }),
      campo({ etiqueta: 'Estado', nombre: 'estado', tipo: 'select', opciones: ESTADOS_DOC, valor: 'Borrador' })
    )
  );

  const { cerrar } = modal({
    titulo: 'Registrar documento',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.numero_documento) return error('El número de documento es obligatorio');
            try {
              await api.comercial.crearDocumento(idExp, {
                tipo_documento: d.tipo_documento,
                numero_documento: d.numero_documento,
                fecha_emision: d.fecha_emision,
                estado: d.estado,
              });
              ok('Documento registrado');
              cerrar();
              refrescar();
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
