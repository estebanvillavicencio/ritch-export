/**
 * Módulo de Productores, Lotes y Trazabilidad + módulo de Calidad.
 *
 * Cubre HU-04 (fincas y asociaciones), HU-05 (inventario de lotes),
 * HU-06 (trazabilidad) y HU-17 (catación y laboratorio).
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, hoy, modal, confirmar, campo,
  filaCampos, leerFormulario, ok, error,
} from '../ui.js';

const ETAPAS = [
  'Finca', 'Beneficio', 'Puerto origen', 'Tránsito marítimo', 'Aduana UE', 'Cliente',
];
const TIPOS_CERT = [
  'EUDR', 'Orgánico', 'Fairtrade', 'Fitosanitario', 'Rainforest Alliance', 'Otro',
];

let cache = { fincas: [], productos: [], catalogos: null };

async function cargarCatalogos() {
  if (!cache.catalogos) cache.catalogos = await api.catalogos.listas();
  return cache.catalogos;
}

/* ========================================================================== */
/* Lotes                                                                       */
/* ========================================================================== */
export async function vistaLotes(raiz) {
  montar(raiz, cargando('Cargando lotes…'));

  // Inventario, catálogos y lista se piden una sola vez y en paralelo.
  const [inventario, fincas, productos, primeraPagina] = await Promise.all([
    api.lotes.inventario(),
    api.catalogos.fincas({ tamano: 100 }),
    api.catalogos.productos({ tamano: 100 }),
    api.lotes.listar({ pagina: 1, tamano: 100 }),
  ]);

  // `opcionesFinca` y `nombreFinca` se recalculan al crear o editar una
  // finca, para que el selector de lotes include la recién registrada.
  let opcionesFinca = opcionesDeFincas(fincas.items);
  let nombreFinca = indicePor(opcionesFinca);
  const opcionesProducto = productos.items.map((x) => ({
    valor: x.id_producto,
    texto: `${x.nombre} (${x.tipo})`,
  }));
  const nombreProducto = indicePor(opcionesProducto);

  const cuerpoTabla = el('div');
  const cuerpoFincas = el('div');

  async function refrescarFincas() {
    const datos = await api.catalogos.fincas({ tamano: 100 });
    fincas.items = datos.items;
    opcionesFinca = opcionesDeFincas(fincas.items);
    nombreFinca = indicePor(opcionesFinca);
    montar(
      cuerpoFincas,
      fincas.items.length
        ? tablaFincas(fincas.items, refrescarFincas, refrescar)
        : vacio('No hay fincas registradas. Crea la primera para asociar lotes.')
    );
  }

  async function refrescar() {
    const datos = await api.lotes.listar({ pagina: 1, tamano: 100 });
    montar(
      cuerpoTabla,
      datos.items.length
        ? tablaLotes(datos.items, refrescar, nombreFinca, nombreProducto, opcionesFinca, opcionesProducto)
        : vacio('No hay lotes registrados. Crea el primero con «+ Nuevo lote».')
    );
  }

  montar(
    raiz,
    panelInventario(inventario),
    el(
      'div.panel.mb-2',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Fincas y asociaciones'),
        sesion.puede('Administrador', 'Comercial', 'Calidad')
          ? el(
              'button.btn.btn-primary.btn-sm',
              { onclick: () => formFinca(refrescarFincas) },
              icono('mas'),
              'Nueva finca'
            )
          : null
      ),
      cuerpoFincas
    ),
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Lotes de café y cacao'),
        el(
          'div.flex',
          {},
          el('span.small.muted', {}, `${primeraPagina.total} lotes`),
          sesion.puede('Administrador', 'Comercial', 'Calidad', 'Logística')
            ? el(
                'button.btn.btn-primary.btn-sm',
                { onclick: () => formLote(refrescar, opcionesFinca, opcionesProducto) },
                icono('mas'),
                'Nuevo lote'
              )
            : null
        )
      ),
      cuerpoTabla
    )
  );

  refrescarFincas();
  await refrescar();
}

function panelInventario(inv) {
  const barras = (inv.por_tipo || []).map((t) => {
    const color = t.tipo === 'Cacao' ? 'var(--rust)' : '#7A5320';
    return el(
      'div.comp-item',
      {},
      el(
        'div.comp-top',
        {},
        el('span', {}, t.tipo),
        el('span.mono', {}, `${f.entero(t.kilos)} kg`)
      ),
      el(
        'div.bar-track',
        {},
        el('div.bar-fill', { style: { width: `${Math.min(t.porcentaje, 100)}%`, background: color } })
      )
    );
  });

  return el(
    'div.grid3.mb-2',
    {},
    el(
      'div.panel',
      {},
      el('div.panel-head', {}, el('h3', {}, 'Inventario disponible')),
      el(
        'dl',
        {},
        el('dt', {}, 'Total en finca'),
        el('dd', {}, f.kilos(inv.kilos_totales)),
        el('dt', {}, 'Disponible'),
        el('dd', { style: { color: 'var(--leaf)' } }, f.kilos(inv.kilos_disponibles)),
        el('dt', {}, 'Comprometido'),
        el('dd', {}, f.kilos(inv.kilos_comprometidos))
      )
    ),
    el(
      'div.panel',
      { style: { gridColumn: 'span 2' } },
      el('div.panel-head', {}, el('h3', {}, 'Disponible por tipo de producto')),
      ...(barras.length ? barras : [vacio('Sin datos de inventario.')])
    )
  );
}

function tablaLotes(lotes, refrescar, nombreFinca, nombreProducto, opcionesFinca, opcionesProducto) {
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
          el('th', {}, 'Finca'),
          el('th', {}, 'Producto'),
          el('th.tnum', {}, 'Cantidad'),
          el('th.tnum', {}, 'Disponible'),
          el('th', {}, 'Cosecha'),
          el('th', {}, 'Calidad'),
          el('th', {}, '')
        )
      ),
      el(
        'tbody',
        {},
        ...lotes.map((l) =>
          el(
            'tr',
            {},
            el('td', {}, el('div.mono.cell-main', {}, l.codigo_lote)),
            el(
              'td',
              {},
              el('div.cell-main', {}, nombreFinca[l.id_finca] || `Finca ${l.id_finca}`),
              el('div.cell-sub', {}, `${l.altura_msnm || '—'} msnm`)
            ),
            el(
              'td',
              {},
              el('div', {}, nombreProducto[l.id_producto] || `Producto ${l.id_producto}`),
              el('div.cell-sub', {}, l.variedad || '—')
            ),
            el('td.tnum', {}, f.kilos(l.cantidad_kg)),
            el(
              'td.tnum',
              { style: { fontWeight: 600 } },
              f.kilos(l.disponible_kg ?? l.cantidad_kg)
            ),
            el('td', {}, f.fechaCorta(l.fecha_cosecha)),
            el('td', {}, pill(l.estado_calidad)),
            el(
              'td',
              { class: 'right nowrap' },
              el(
                'div.flex',
                { style: { justifyContent: 'flex-end' } },
                el(
                  'button.btn.btn-sm',
                  { title: 'Trazabilidad', onclick: () => verTrazabilidad(l.id_lote) },
                  icono('hoja')
                ),
                el(
                  'button.btn.btn-sm',
                  { title: 'Calidad', onclick: () => formCalidad(l.id_lote, refrescar) },
                  icono('calidad')
                ),
                el(
                  'button.btn.btn-sm',
                  { title: 'Certificaciones', onclick: () => formCertificacion(l.id_lote) },
                  icono('etiqueta')
                ),
                el(
                  'button.btn.btn-sm',
                  { title: 'Ver ficha', onclick: () => verFichaLote(l.id_lote) },
                  icono('documento')
                ),
                sesion.puede('Administrador', 'Comercial', 'Calidad')
                  ? el(
                      'button.btn.btn-sm',
                      {
                        title: 'Editar lote',
                        onclick: () => formLote(refrescar, opcionesFinca, opcionesProducto, l),
                      },
                      icono('editar')
                    )
                  : null,
                l.estado_calidad !== 'Rechazado' && Number(l.consumo_kg || 0) === 0
                  ? el(
                      'button.btn.btn-sm.btn-danger',
                      {
                        title: 'Retirar del inventario exportable',
                        onclick: () => retirarLote(l, refrescar),
                      },
                      icono('alerta')
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

/* -------------------------------------------------------------------------- */
/* Formulario de lote                                                          */
/* -------------------------------------------------------------------------- */
/* Formulario de lote                                                          */
/* -------------------------------------------------------------------------- */
/**
 * HU-05 · Alta y edición de lotes. Si se pasa `lote`, el formulario edita ese
 * registro; en ese caso el código correlativo no se puede cambiar.
 */
function formLote(refrescar, opcionesFinca, opcionesProducto, lote = null) {
  const edicion = Boolean(lote);
  const num = (k) => (lote && lote[k] !== null && lote[k] !== undefined ? lote[k] : '');
  const fecha = (k) => (lote && lote[k] ? String(lote[k]).slice(0, 10) : hoy());

  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    el(
      'div.form-grid',
      {},
      campo({
        etiqueta: 'Finca', nombre: 'id_finca', tipo: 'select',
        opciones: opcionesFinca, valor: num('id_finca'), requerido: true,
      }),
      campo({
        etiqueta: 'Producto', nombre: 'id_producto', tipo: 'select',
        opciones: opcionesProducto, valor: num('id_producto'), requerido: true,
      }),
      filaCampos(
        campo({
          etiqueta: 'Cantidad (kg)', nombre: 'cantidad_kg', tipo: 'number',
          min: '1', step: '0.01', valor: num('cantidad_kg'), requerido: true,
        }),
        campo({
          etiqueta: 'Fecha de cosecha', nombre: 'fecha_cosecha', tipo: 'date',
          valor: fecha('fecha_cosecha'), max: hoy(), requerido: true,
        })
      ),
      filaCampos(
        campo({
          etiqueta: 'Variedad', nombre: 'variedad',
          placeholder: 'Caturra, Castillo…', valor: num('variedad'),
        }),
        campo({
          etiqueta: 'Altitud (msnm)', nombre: 'altura_msnm', tipo: 'number',
          min: '0', max: '4000', valor: num('altura_msnm'),
        })
      ),
      edicion
        ? campo({
            etiqueta: 'Estado de calidad', nombre: 'estado_calidad', tipo: 'select',
            opciones: ['Pendiente', 'En análisis', 'Aprobado', 'Aprobado con reserva', 'Rechazado'],
            valor: num('estado_calidad'),
          })
        : campo({
            etiqueta: 'Código de lote', nombre: 'codigo_lote', ancho: 'full',
            placeholder: 'Se genera automáticamente si lo dejas vacío',
            pista: 'Formato automático: CO-HUI-AAAA-NNNN',
          })
    )
  );

  const { cerrar } = modal({
    titulo: edicion ? `Editar lote ${lote.codigo_lote}` : 'Nuevo lote',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        { onclick: guardar },
        edicion ? 'Guardar cambios' : 'Registrar lote'
      ),
    ],
  });

  async function guardar() {
    const d = leerFormulario(form);
    if (!d.id_finca || !d.cantidad_kg || !d.fecha_cosecha) {
      return error('Finca, cantidad y fecha de cosecha son obligatorios');
    }
    const cuerpo = {
      id_finca: Number(d.id_finca),
      id_producto: Number(d.id_producto),
      cantidad_kg: d.cantidad_kg,
      fecha_cosecha: d.fecha_cosecha,
      variedad: d.variedad || null,
      altura_msnm: d.altura_msnm ? Number(d.altura_msnm) : null,
    };
    try {
      if (edicion) {
        if (d.estado_calidad) cuerpo.estado_calidad = d.estado_calidad;
        await api.lotes.actualizar(lote.id_lote, cuerpo);
        ok(`Lote ${lote.codigo_lote} actualizado`);
      } else {
        const creado = await api.lotes.crear({ ...cuerpo, codigo_lote: d.codigo_lote || null });
        ok(`Lote ${creado.codigo_lote} registrado`);
      }
      cerrar();
      refrescar();
    } catch (e) {
      error(e.message);
    }
  }
}

/** HU-05 · Retira un lote del inventario exportable sin borrarlo. */
async function retirarLote(lote, refrescar) {
  const confirmado = await confirmar({
    titulo: 'Retirar lote del inventario',
    mensaje:
      `El lote ${lote.codigo_lote} dejará de ofrecerse como exportable y se marcará ` +
      'como rechazado. No se borra: se conserva la trazabilidad.',
    textoOk: 'Retirar lote',
    peligro: true,
  });
  if (!confirmado) return;
  try {
    await api.lotes.retirar(lote.id_lote);
    ok(`Lote ${lote.codigo_lote} retirado`);
    refrescar();
  } catch (e) {
    error(e.message);
  }
}

/* -------------------------------------------------------------------------- */
/* Ficha y trazabilidad de un lote                                              */
/* -------------------------------------------------------------------------- */
async function verFichaLote(idLote) {
  const { cerrar } = modal({ titulo: 'Ficha de lote', cuerpo: cargando(), ancho: 'wide' });
  try {
    const lote = await api.lotes.ver(idLote);
    const cuerpo = el(
      'div',
      {},
      el(
        'div.ticket.mb-2',
        {},
        el(
          'div.ticket-row',
          {},
          el('div.ticket-code', {}, 'Lote', el('br'), el('b.mono', {}, lote.codigo_lote)),
          el('div.ticket-stamp', { class: lote.estado_calidad === 'Aprobado' ? '' : 'rust' }, lote.estado_calidad)
        ),
        el('div.ticket-farm', {}, lote.finca_nombre),
        el(
          'div.ticket-loc',
          {},
          `${lote.finca_ubicacion}, ${lote.finca_departamento}`
        ),
        el(
          'div.ticket-tags',
          {},
          el('span.tag', { class: lote.producto_tipo === 'Cacao' ? 'cacao' : 'cafe' }, lote.producto_tipo),
          ...(lote.certificaciones || []).map((c) => el('span.tag.eudr', {}, c.tipo))
        )
      ),
      el(
        'div.grid2',
        {},
        el(
          'div',
          {},
          el('h4', { style: { margin: '0 0 8px', fontSize: '13px' } }, 'Origen'),
          el(
            'dl',
            {},
            el('dt', {}, 'Propietario'), el('dd', {}, f.texto(lote.finca_propietario)),
            el('dt', {}, 'Productor'), el('dd', {}, f.texto(lote.finca_productor)),
            el('dt', {}, 'Asociación'), el('dd', {}, f.texto(lote.finca_asociacion)),
            el('dt', {}, 'Altitud'), el('dd', {}, lote.altura_msnm ? `${lote.altura_msnm} msnm` : '—')
          )
        ),
        el(
          'div',
          {},
          el('h4', { style: { margin: '0 0 8px', fontSize: '13px' } }, 'Lote'),
          el(
            'dl',
            {},
            el('dt', {}, 'Producto'), el('dd', {}, lote.producto_nombre),
            el('dt', {}, 'Variedad'), el('dd', {}, f.texto(lote.variedad)),
            el('dt', {}, 'Cantidad'), el('dd', {}, f.kilos(lote.cantidad_kg)),
            el('dt', {}, 'Disponible'), el('dd', {}, f.kilos(lote.disponible_kg)),
            el('dt', {}, 'Cosecha'), el('dd', {}, f.fecha(lote.fecha_cosecha))
          )
        )
      ),
      lote.calidad
        ? el(
            'div.mt-2',
            {},
            el('h4', { style: { margin: '0 0 8px', fontSize: '13px' } }, 'Calidad registrada'),
            el(
              'dl',
              {},
              el('dt', {}, 'Humedad'), el('dd', {}, f.decimal(lote.calidad.humedad) + ' %'),
              el('dt', {}, 'Puntaje de cata'), el('dd', {}, f.decimal(lote.calidad.puntaje_cata)),
              el('dt', {}, 'Clasificación'), el('dd', {}, f.texto(lote.calidad.clasificacion)),
              el('dt', {}, 'Laboratorio'), el('dd', {}, f.texto(lote.calidad.laboratorio))
            )
          )
        : el('div.alert.gold.mt-2', {}, icono('alerta'), el('div', {}, 'Este lote aún no tiene resultados de calidad.'))
    );
    const caja = document.querySelector('.modal-backdrop .modal-body');
    if (caja) montar(caja, cuerpo);
  } catch (e) {
    error(e.message);
    cerrar();
  }
}

async function verTrazabilidad(idLote) {
  const { cerrar } = modal({ titulo: 'Trazabilidad del lote', cuerpo: cargando(), ancho: 'wide' });
  try {
    const [traza, lote] = await Promise.all([
      api.lotes.trazabilidad(idLote),
      api.lotes.ver(idLote),
    ]);

    const cuerpo = el(
      'div',
      {},
      el('p.small.muted.mt-0', {}, `Recorrido del lote ${traza.codigo_lote} desde la finca hasta el destino (HU-06).`),
      el(
        'div.timeline.mt-2',
        {},
        ...traza.etapas.map((e) =>
          el(
            `div.t-step.${e.estado}`,
            {},
            el('div.t-dot', {}, e.estado === 'done' ? '✓' : e.estado === 'current' ? '●' : ''),
            el('div.t-step-label', {}, e.etapa),
            e.fecha ? el('div.small.muted', {}, f.fechaCorta(e.fecha)) : null
          )
        )
      ),
      el(
        'div.mt-2',
        {},
        ...traza.etapas
          .filter((e) => e.fecha)
          .map((e) =>
            el(
              'div.doc-item',
              {},
              el(
                'div',
                {},
                el('div.doc-main', {}, e.etapa),
                el('div.doc-sub', {}, [e.fecha ? f.fecha(e.fecha) : '', e.ubicacion, e.descripcion].filter(Boolean).join(' · '))
              ),
              pill(e.estado === 'done' ? 'Vigente' : 'Pendiente')
            )
          )
      ),
      el(
        'div.mt-2',
        {},
        el(
          'button.btn.btn-sm',
          {
            onclick: () => {
              cerrar();
              formEvento(idLote);
            },
          },
          icono('mas'),
          'Registrar hito'
        )
      )
    );

    const caja = document.querySelector('.modal-backdrop .modal-body');
    if (caja) montar(caja, cuerpo);
  } catch (e) {
    error(e.message);
    cerrar();
  }
}

function formEvento(idLote) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({ etiqueta: 'Etapa', nombre: 'etapa', tipo: 'select', opciones: ETAPAS, requerido: true }),
    filaCampos(
      campo({ etiqueta: 'Fecha', nombre: 'fecha', tipo: 'date', valor: hoy(), requerido: true }),
      campo({ etiqueta: 'Ubicación', nombre: 'ubicacion', placeholder: 'Beneficio La Esperanza' })
    ),
    campo({ etiqueta: 'Descripción', nombre: 'descripcion', tipo: 'textarea' })
  );

  const { cerrar } = modal({
    titulo: 'Registrar hito de trazabilidad',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.etapa || !d.fecha) return error('Indica etapa y fecha');
            try {
              await api.lotes.registrarEvento(idLote, d);
              ok('Hito registrado');
              cerrar();
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
/* Calidad (HU-17)                                                             */
/* -------------------------------------------------------------------------- */
function formCalidad(idLote, refrescar) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    el(
      'div.form-grid',
      {},
      filaCampos(
        campo({ etiqueta: 'Humedad (%)', nombre: 'humedad', tipo: 'number', step: '0.01', min: '8', max: '14', pista: 'Rango válido: 8 – 14 %' }),
        campo({ etiqueta: 'Puntaje de cata', nombre: 'puntaje_cata', tipo: 'number', step: '0.1', min: '0', max: '100' })
      ),
      filaCampos(
        campo({ etiqueta: 'Actividad de agua', nombre: 'actividad_agua', tipo: 'number', step: '0.01' }),
        campo({ etiqueta: 'Granulometría', nombre: 'granulometria', tipo: 'number', step: '0.1' })
      ),
      filaCampos(
        campo({ etiqueta: 'Impurezas (%)', nombre: 'impurezas', tipo: 'number', step: '0.01' }),
        campo({ etiqueta: 'Cafeína (%)', nombre: 'cafeina_pct', tipo: 'number', step: '0.01' })
      ),
      filaCampos(
        campo({ etiqueta: 'Clasificación', nombre: 'clasificacion', placeholder: 'Special, Excelente…' }),
        campo({ etiqueta: 'Método', nombre: 'prueba_metodos', placeholder: 'SCA, CAOBISCO…' })
      ),
      campo({ etiqueta: 'Laboratorio', nombre: 'laboratorio', ancho: 'full' }),
      filaCampos(
        campo({ etiqueta: 'Fecha de análisis', nombre: 'fecha_analisis', tipo: 'date', valor: hoy() }),
        campo({ etiqueta: 'Aprobado por', nombre: 'aprobado_por' })
      ),
      campo({ etiqueta: 'Observaciones', nombre: 'observaciones', tipo: 'textarea', ancho: 'full' })
    )
  );

  const { cerrar } = modal({
    titulo: 'Registrar calidad del lote',
    ancho: 'wide',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            for (const k of Object.keys(d)) {
              if (d[k] === '' && ['humedad', 'puntaje_cata', 'actividad_agua', 'granulometria', 'impurezas', 'cafeina_pct'].includes(k)) {
                delete d[k];
              }
            }
            try {
              await api.lotes.registrarCalidad(idLote, { id_lote: idLote, ...d });
              ok('Resultados de calidad registrados');
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        'Guardar resultados'
      ),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Certificaciones (Informe §6.4)                                               */
/* -------------------------------------------------------------------------- */
function formCertificacion(idLote) {
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({ etiqueta: 'Tipo de certificación', nombre: 'tipo', tipo: 'select', opciones: TIPOS_CERT, requerido: true }),
    filaCampos(
      campo({ etiqueta: 'Entidad emisora', nombre: 'entidad_emisora', placeholder: 'Rainforest Alliance, FLOCERT…' }),
      campo({ etiqueta: 'Número de certificado', nombre: 'numero_certificado' })
    ),
    filaCampos(
      campo({ etiqueta: 'Fecha de emisión', nombre: 'fecha_emision', tipo: 'date', valor: hoy(), requerido: true }),
      campo({ etiqueta: 'Fecha de vencimiento', nombre: 'fecha_vencimiento', tipo: 'date' })
    ),
    el(
      'div.field',
      {},
      el(
        'label',
        { style: { display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '400' } },
        el('input', { type: 'checkbox', name: 'lote_georreferenciado' }),
        'Lote georreferenciado (requisito del Reglamento EUDR)'
      )
    ),
    campo({ etiqueta: 'Notas', nombre: 'notas', tipo: 'textarea' })
  );

  const { cerrar } = modal({
    titulo: 'Registrar certificación',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.fecha_emision) return error('La fecha de emisión es obligatoria');
            try {
              await api.certificaciones.crear({
                id_lote: idLote,
                tipo: d.tipo,
                entidad_emisora: d.entidad_emisora || null,
                numero_certificado: d.numero_certificado || null,
                fecha_emision: d.fecha_emision,
                fecha_vencimiento: d.fecha_vencimiento || null,
                lote_georreferenciado: Boolean(d.lote_georreferenciado),
                notas: d.notas || null,
              });
              ok('Certificación registrada');
              cerrar();
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
/* Fincas y asociaciones · HU-04                                              */
/* -------------------------------------------------------------------------- */
function tablaFincas(fincas, refrescar, refrescarLotes) {
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
          el('th', {}, 'Finca'),
          el('th', {}, 'Ubicación'),
          el('th', {}, 'Propietario'),
          el('th', {}, 'Asociación'),
          el('th.tnum', {}, 'Capacidad'),
          el('th', {}, '')
        )
      ),
      el(
        'tbody',
        {},
        ...fincas.map((x) =>
          el(
            'tr',
            {},
            el(
              'td',
              {},
              el('div.cell-main', {}, x.nombre),
              el('div.cell-sub', {}, x.productor || '—')
            ),
            el('td.small', {}, x.ubicacion, el('div.cell-sub', {}, x.departamento)),
            el('td', {}, x.propietario),
            el('td.small', {}, f.texto(x.asociacion)),
            el('td.tnum', {}, f.kilos(x.capacidad_produccion_kg)),
            el(
              'td',
              { class: 'right' },
              el(
                'button.btn.btn-sm',
                { title: 'Editar', onclick: () => formFinca(refrescar, x, refrescarLotes) },
                icono('editar')
              )
            )
          )
        )
      )
    )
  );
}

/**
 * HU-04 · Registrar o editar una finca o asociación.
 * La geolocalización (latitud/longitud) es el dato que exige el Reglamento EUDR.
 */
function formFinca(refrescar, finca = null, refrescarLotes = null) {
  const edicion = Boolean(finca);
  const v = (k) => (finca ? (finca[k] ?? '') : '');
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    el(
      'div.form-grid',
      {},
      campo({ etiqueta: 'Nombre de la finca', nombre: 'nombre', valor: v('nombre'), requerido: true }),
      campo({ etiqueta: 'Propietario', nombre: 'propietario', valor: v('propietario'), requerido: true }),
      campo({
        etiqueta: 'Ubicación', nombre: 'ubicacion', valor: v('ubicacion'),
        placeholder: 'Vereda El Cedro, Pitalito', requerido: true,
      }),
      campo({
        etiqueta: 'Departamento', nombre: 'departamento', valor: v('departamento'),
        placeholder: 'Huila', requerido: true,
      }),
      campo({ etiqueta: 'Productor', nombre: 'productor', valor: v('productor') }),
      campo({ etiqueta: 'Asociación', nombre: 'asociacion', valor: v('asociacion') }),
      filaCampos(
        campo({
          etiqueta: 'Altitud (msnm)', nombre: 'altura_msnm', tipo: 'number',
          min: '0', max: '4000', valor: v('altura_msnm'),
        }),
        campo({
          etiqueta: 'Superficie (ha)', nombre: 'superficie_ha', tipo: 'number',
          min: '0', step: '0.01', valor: v('superficie_ha'),
        })
      ),
      campo({
        etiqueta: 'Capacidad de producción (kg/año)', nombre: 'capacidad_produccion_kg',
        tipo: 'number', min: '0', step: '0.01', valor: v('capacidad_produccion_kg'),
        ancho: 'full',
      }),
      filaCampos(
        campo({
          etiqueta: 'Latitud', nombre: 'latitud', tipo: 'number', step: '0.0000001',
          valor: v('latitud'), pista: 'Requisito del Reglamento EUDR',
        }),
        campo({
          etiqueta: 'Longitud', nombre: 'longitud', tipo: 'number', step: '0.0000001',
          valor: v('longitud'),
        })
      )
    )
  );

  const { cerrar } = modal({
    titulo: edicion ? `Editar ${finca.nombre}` : 'Nueva finca o asociación',
    ancho: 'wide',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.nombre || !d.ubicacion || !d.departamento || !d.propietario) {
              return error('Nombre, ubicación, departamento y propietario son obligatorios');
            }
            const cuerpo = {
              nombre: d.nombre,
              ubicacion: d.ubicacion,
              departamento: d.departamento,
              propietario: d.propietario,
              productor: d.productor || null,
              asociacion: d.asociacion || null,
              altura_msnm: d.altura_msnm ? Number(d.altura_msnm) : null,
              superficie_ha: d.superficie_ha || null,
              capacidad_produccion_kg: d.capacidad_produccion_kg || null,
              latitud: d.latitud || null,
              longitud: d.longitud || null,
            };
            try {
              if (edicion) {
                await api.catalogos.actualizarFinca(finca.id_finca, cuerpo);
                ok('Finca actualizada');
              } else {
                await api.catalogos.crearFinca(cuerpo);
                ok('Finca registrada');
              }
              cerrar();
              refrescar();
              if (refrescarLotes) refrescarLotes();
            } catch (e) {
              error(e.message);
            }
          },
        },
        edicion ? 'Guardar cambios' : 'Registrar finca'
      ),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Utilidades                                                                  */
/* -------------------------------------------------------------------------- */

/** Opciones del selector de fincas: «Nombre · Departamento». */
function opcionesDeFincas(fincas) {
  return fincas.map((x) => ({
    valor: x.id_finca,
    texto: `${x.nombre} · ${x.departamento}`,
  }));
}

/** Convierte una lista de {valor, texto} en un mapa id → nombre. */
function indicePor(opciones) {
  return Object.fromEntries(opciones.map((o) => [o.valor, o.texto]));
}
