/**
 * Sistema — HU-19, HU-20 y HU-22.
 *
 * Integraciones externas, tipos de cambio y copias de seguridad. El módulo
 * funciona sin internet: las integraciones caen a un modo simulado que deja
 * el mismo rastro en la bitácora.
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, hoy, modal, campo,
  filaCampos, leerFormulario, ok, error, confirmar, aviso,
} from '../ui.js';

const esAdmin = () => sesion.puede('Administrador');
const puedeVer = () => sesion.puede('Administrador', 'Financiero');

export async function vistaSistema(raiz) {
  montar(raiz, cargando('Cargando el módulo de sistema…'));

  if (!puedeVer()) {
    montar(raiz, el('div.alert.rust', {}, icono('candado'),
      el('div', {}, 'Tu rol no tiene acceso a integraciones ni respaldos.')));
    return;
  }

  let integraciones, tipos;
  try {
    [integraciones, tipos] = await Promise.all([
      api.sistema.integraciones(),
      api.sistema.tiposCambio(),
    ]);
  } catch (e) {
    montar(raiz, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    return;
  }

  const contIntegraciones = el('div', {}, tablaIntegraciones(integraciones, cargarIntegraciones));
  const contTipos = el('div', {}, tablaTipos(tipos, cargarTipos));
  const contRespaldos = el('div', {});

  async function cargarIntegraciones() {
    try {
      integraciones = await api.sistema.integraciones();
      montar(contIntegraciones, tablaIntegraciones(integraciones, cargarIntegraciones));
    } catch (e) {
      error(e.message);
    }
  }

  async function cargarTipos() {
    try {
      tipos = await api.sistema.tiposCambio();
      montar(contTipos, tablaTipos(tipos, cargarTipos));
    } catch (e) {
      error(e.message);
    }
  }

  async function cargarRespaldos() {
    if (!esAdmin()) return;
    montar(contRespaldos, cargando('Consultando respaldos…'));
    try {
      const datos = await api.sistema.respaldos();
      montar(contRespaldos, datos.length ? tablaRespaldos(datos, cargarRespaldos) : vacio('Todavía no hay copias de seguridad.'));
    } catch (e) {
      montar(contRespaldos, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    }
  }

  montar(
    raiz,
    el(
      'div.panel.mb-2',
      {},
      el(
        'div.panel-head',
        {},
        el('div', {}, el('h3', {}, 'Integraciones externas'),
          el('p.muted.small', { style: { margin: '4px 0 0' } },
            'Servicios de correo, seguimiento, tipos de cambio y almacenamiento.')),
        esAdmin()
          ? el('div.flex', {},
              el('button.btn.btn-sm', { onclick: () => formularioCorreo(cargarIntegraciones) },
                icono('comercial'), 'Probar correo'),
              el('button.btn.btn-sm', { onclick: () => formularioSeguimiento(cargarIntegraciones) },
                icono('buscar'), 'Consultar seguimiento'))
          : null
      ),
      contIntegraciones
    ),
    el(
      'div.panel.mb-2',
      {},
      el(
        'div.panel-head',
        {},
        el('div', {}, el('h3', {}, 'Tipos de cambio'),
          el('p.muted.small', { style: { margin: '4px 0 0' } },
            'Unidades de cada moneda por 1 EUR. El portal las usa para mostrar precios.')),
        el('div.flex', {},
          el('button.btn.btn-sm', { onclick: () => formularioConversion() }, icono('euro'), 'Convertir'),
          esAdmin()
            ? el('button.btn.btn-sm.btn-primary', { onclick: actualizarTipos }, icono('refrescar'), 'Actualizar tasas')
            : null,
          esAdmin()
            ? el('button.btn.btn-sm', { onclick: () => formularioTipo(cargarTipos) }, icono('mas'), 'Tasa manual')
            : null)
      ),
      contTipos
    ),
    esAdmin()
      ? el(
          'div.panel',
          {},
          el(
            'div.panel-head',
            {},
            el('div', {}, el('h3', {}, 'Copias de seguridad'),
              el('p.muted.small', { style: { margin: '4px 0 0' } },
                'Instantánea JSON de todas las tablas, con tamaño y SHA-256 verificable.')),
            el('button.btn.btn-sm.btn-primary', { onclick: crearRespaldo }, icono('descargar'), 'Crear respaldo')
          ),
          contRespaldos
        )
      : null
  );

  cargarRespaldos();
  if (esAdmin()) cargarBitacora();

  async function cargarBitacora() {
    try {
      const filas = await api.sistema.bitacora({ limite: 12 });
      if (!filas.length) return;
      contIntegraciones.appendChild(
        el(
          'div',
          { style: { padding: '0 20px 16px' } },
          el('div.nav-label', {}, 'Últimas ejecuciones'),
          el(
            'div.table-wrap',
            {},
            el(
              'table',
              {},
              el('thead', {}, el('tr', {}, ...['Fecha', 'Servicio', 'Acción', 'Estado', 'Mensaje']
                .map((t) => el('th', {}, t)))),
              el('tbody', {}, ...filas.map((r) =>
                el('tr', {},
                  el('td', {}, f.fechaHora(r.created_at)),
                  el('td', {}, r.servicio),
                  el('td', {}, r.accion),
                  el('td', {}, pill(r.estado === 'ok' ? 'Aprobado' : r.estado === 'error' ? 'Rechazado' : 'Pendiente')),
                  el('td.small', {}, r.mensaje || '—'))))
            )
          )
        )
      );
    } catch { /* la bitácora es informativa */ }
  }

  async function actualizarTipos() {
    try {
      const r = await api.sistema.actualizarTiposCambio();
      aviso(`${r.actualizados} moneda(s) actualizadas desde ${r.fuente} (${r.modo}).`, 'ok');
      cargarTipos();
    } catch (e) {
      error(e.message);
    }
  }

  async function crearRespaldo() {
    const seguro = await confirmar({
      titulo: 'Crear copia de seguridad',
      mensaje: 'Se escribirá un archivo JSON con todas las tablas en el directorio de respaldos.',
      textoOk: 'Crear',
    });
    if (!seguro) return;
    try {
      const r = await api.sistema.crearRespaldo();
      aviso(`Respaldo ${r.nombre} creado (${r.registros} registros).`, 'ok');
      cargarRespaldos();
    } catch (e) {
      error(e.message);
    }
  }
}

/* -------------------------------------------------------------------------- */
/* Integraciones                                                               */
/* -------------------------------------------------------------------------- */
function tablaIntegraciones(integraciones, recargar) {
  return el(
    'div.table-wrap',
    {},
    el(
      'table',
      {},
      el('thead', {}, el('tr', {}, ...['Servicio', 'Descripción', 'Estado', 'Configuración', 'Última ejecución']
        .map((t) => el('th', {}, t)))),
      el('tbody', {}, ...integraciones.map((i) =>
        el('tr', {},
          el('td.cell-main', {}, i.servicio),
          el('td.small', {}, i.descripcion),
          el('td', {}, pill(i.estado === 'operativo' ? 'Aprobado' : i.estado === 'simulado' ? 'Pendiente' : 'Rechazado')),
          el('td.small', {}, i.detalle || '—'),
          el('td.small', {}, i.ultima_ejecucion ? f.fechaHora(i.ultima_ejecucion) : '—'))))
    )
  );
}

function formularioCorreo(recargar) {
  const form = el(
    'form',
    {},
    campo({ etiqueta: 'Destinatario', nombre: 'destinatario', tipo: 'email', requerido: true, valor: 'compras@ritch.com' }),
    campo({ etiqueta: 'Asunto', nombre: 'asunto', valor: 'Prueba de integración RiTech' }),
    campo({ etiqueta: 'Mensaje', nombre: 'mensaje', tipo: 'textarea', valor: 'Mensaje de prueba del sistema RiTech.' })
  );
  const { cerrar } = modal({
    titulo: 'Probar la integración de correo',
    cuerpo: form,
    pie: [
      el('button.btn', { type: 'button', onclick: () => cerrar() }, 'Cancelar'),
      el('button.btn.btn-primary', {
        type: 'button',
        onclick: async () => {
          if (!form.reportValidity()) return;
          try {
            const r = await api.sistema.probarCorreo(leerFormulario(form));
            cerrar();
            aviso(r.mensaje, r.estado === 'error' ? 'err' : 'ok');
            recargar();
          } catch (e) {
            error(e.message);
          }
        },
      }, 'Enviar'),
    ],
  });
}

function formularioSeguimiento(recargar) {
  const form = el(
    'form',
    {},
    campo({ etiqueta: 'Número de seguimiento', nombre: 'numero', requerido: true, placeholder: 'MAEU-4471288' })
  );
  const { cerrar } = modal({
    titulo: 'Consultar seguimiento',
    cuerpo: form,
    pie: [
      el('button.btn', { type: 'button', onclick: () => cerrar() }, 'Cerrar'),
      el('button.btn.btn-primary', {
        type: 'button',
        onclick: async () => {
          if (!form.reportValidity()) return;
          try {
            const r = await api.sistema.seguimiento(leerFormulario(form).numero);
            cerrar();
            aviso(r.mensaje, r.estado === 'error' ? 'err' : 'ok');
            recargar();
          } catch (e) {
            error(e.message);
          }
        },
      }, 'Consultar'),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Monedas                                                                     */
/* -------------------------------------------------------------------------- */
function tablaTipos(tipos, recargar) {
  if (!tipos.length) return vacio('No hay tipos de cambio cargados.');
  return el(
    'div.table-wrap',
    {},
    el(
      'table',
      {},
      el('thead', {}, el('tr', {}, ...['Moneda', 'Tasa (por 1 EUR)', 'Fecha', 'Fuente', 'Equivalencia']
        .map((t, i) => el('th', { class: i === 1 ? 'tnum' : '' }, t)))),
      el('tbody', {}, ...tipos.map((t) =>
        el('tr', {},
          el('td', {}, el('span.status.azul', {}, t.moneda)),
          el('td.tnum', {}, f.decimal(t.tasa)),
          el('td', {}, f.fecha(t.fecha)),
          el('td.small', {}, t.fuente || '—'),
          el('td.small', {}, `1 EUR = ${f.decimal(t.tasa)} ${t.moneda}`))))
    )
  );
}

function formularioTipo(recargar) {
  const form = el(
    'form',
    {},
    filaCampos(
      campo({ etiqueta: 'Moneda', nombre: 'moneda', requerido: true, placeholder: 'USD' }),
      campo({ etiqueta: 'Tasa por 1 EUR', nombre: 'tasa', tipo: 'number', requerido: true, atributos: { min: '0.000001', step: '0.000001' } }),
      campo({ etiqueta: 'Fecha', nombre: 'fecha', tipo: 'date', valor: hoy(), requerido: true })
    ),
    campo({ etiqueta: 'Fuente', nombre: 'fuente', valor: 'Carga manual' })
  );
  const { cerrar } = modal({
    titulo: 'Registrar tipo de cambio',
    cuerpo: form,
    pie: [
      el('button.btn', { type: 'button', onclick: () => cerrar() }, 'Cancelar'),
      el('button.btn.btn-primary', {
        type: 'button',
        onclick: async () => {
          if (!form.reportValidity()) return;
          const d = leerFormulario(form);
          d.moneda = d.moneda.toUpperCase();
          d.tasa = Number(d.tasa);
          try {
            await api.sistema.crearTipoCambio(d);
            cerrar();
            ok('Tipo de cambio guardado');
            recargar();
          } catch (e) {
            error(e.message);
          }
        },
      }, 'Guardar'),
    ],
  });
}

function formularioConversion() {
  const form = el(
    'form',
    {},
    filaCampos(
      campo({ etiqueta: 'Valor', nombre: 'valor', tipo: 'number', requerido: true, valor: 1000, atributos: { min: '0.01', step: '0.01' } }),
      campo({ etiqueta: 'Desde', nombre: 'desde', tipo: 'select', opciones: ['EUR', 'USD', 'COP'], valor: 'EUR' }),
      campo({ etiqueta: 'Hasta', nombre: 'hasta', tipo: 'select', opciones: ['EUR', 'USD', 'COP'], valor: 'USD' })
    )
  );
  const resultado = el('div.alert.leaf', { style: { display: 'none', marginTop: '10px' } });
  const { cerrar } = modal({
    titulo: 'Convertir moneda',
    cuerpo: el('div', {}, form, resultado),
    pie: [
      el('button.btn', { type: 'button', onclick: () => cerrar() }, 'Cerrar'),
      el('button.btn.btn-primary', {
        type: 'button',
        onclick: async () => {
          if (!form.reportValidity()) return;
          try {
            const r = await api.sistema.convertir(leerFormulario(form));
            resultado.style.display = '';
            montar(resultado, el('strong', {}, `${f.moneda(r.valor, r.desde)} = ${f.moneda(r.resultado, r.hasta)}`),
              el('div.small', {}, `Tasa: 1 ${r.desde} = ${f.decimal(r.tasa)} ${r.hasta} · ${f.fecha(r.fecha)}`));
          } catch (e) {
            error(e.message);
          }
        },
      }, 'Convertir'),
    ],
  });
}

/* -------------------------------------------------------------------------- */
/* Respaldos                                                                   */
/* -------------------------------------------------------------------------- */
function tablaRespaldos(respaldos, recargar) {
  return el(
    'div.table-wrap',
    {},
    el(
      'table',
      {},
      el('thead', {}, el('tr', {}, ...['Archivo', 'Fecha', 'Tipo', 'Tamaño', 'Registros', 'Integridad', 'Acciones']
        .map((t) => el('th', {}, t)))),
      el('tbody', {}, ...respaldos.map((r) =>
        el('tr', {},
          el('td.mono.cell-main', {}, r.nombre),
          el('td', {}, f.fechaHora(r.created_at)),
          el('td', {}, el('span.status.gris', {}, r.tipo)),
          el('td.tnum', {}, `${Math.max(1, Math.round(r.tamano_bytes / 1024))} KB`),
          el('td.tnum', {}, f.entero(r.registros)),
          el('td', {}, pill(r.estado)),
          el('td', {}, el('div.flex', {},
            el('button.btn.btn-sm', {
              onclick: async () => {
                try {
                  const v = await api.sistema.verificarRespaldo(r.id_respaldo);
                  aviso(v.mensaje, v.integro ? 'ok' : 'err');
                } catch (e) {
                  error(e.message);
                }
              },
            }, icono('check'), 'Verificar'),
            el('button.btn.btn-sm', {
              onclick: () => {
                window.open(api.sistema.descargarRespaldo(r.id_respaldo), '_blank');
              },
            }, icono('descargar'), 'Descargar'))))))
    )
  );
}
