/**
 * Cliente de la API REST de RiTech SAS.
 *
 * Gestiona el token JWT de sesión, normaliza los errores del servidor y
 * expone los métodos agrupados por módulo (Sprints 2 a 4).
 */

const BASE = '/api';
const CLAVE_TOKEN = 'ritch_token';
const CLAVE_USUARIO = 'ritch_usuario';

export class ErrorApi extends Error {
  constructor(mensaje, estado, detalle) {
    super(mensaje);
    this.name = 'ErrorApi';
    this.estado = estado;
    this.detalle = detalle;
  }
}

export const sesion = {
  get token() {
    return localStorage.getItem(CLAVE_TOKEN);
  },
  get usuario() {
    const bruto = localStorage.getItem(CLAVE_USUARIO);
    return bruto ? JSON.parse(bruto) : null;
  },
  get activo() {
    return Boolean(this.token);
  },
  iniciar(token, usuario) {
    localStorage.setItem(CLAVE_TOKEN, token);
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(usuario));
  },
  cerrar() {
    localStorage.removeItem(CLAVE_TOKEN);
    localStorage.removeItem(CLAVE_USUARIO);
  },
  /** Roles con permiso sobre un módulo. */
  puede(...roles) {
    const u = this.usuario;
    if (!u) return false;
    return roles.length === 0 || roles.includes(u.rol);
  },
};

/** Extrae un mensaje legible de la respuesta de error de FastAPI. */
function mensajeDeError(cuerpo, estado) {
  const d = cuerpo?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && d.length) {
    return d
      .map((e) => {
        const campo = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : '';
        return campo ? `${campo}: ${e.msg}` : e.msg;
      })
      .join(' · ');
  }
  if (estado === 401) return 'Sesión expirada. Inicia sesión nuevamente.';
  if (estado === 403) return 'No tienes permisos para esta operación.';
  if (estado === 404) return 'El recurso solicitado no existe.';
  return `Error ${estado}`;
}

async function pedir(ruta, opciones = {}) {
  const cabeceras = { ...(opciones.headers || {}) };
  if (opciones.body !== undefined && !(opciones.body instanceof FormData)) {
    cabeceras['Content-Type'] = 'application/json';
  }
  if (sesion.token) cabeceras['Authorization'] = `Bearer ${sesion.token}`;

  const respuesta = await fetch(`${BASE}${ruta}`, {
    method: opciones.method || 'GET',
    headers: cabeceras,
    body:
      opciones.body === undefined
        ? undefined
        : opciones.body instanceof FormData
          ? opciones.body
          : JSON.stringify(opciones.body),
  });

  if (respuesta.status === 204) return null;

  let cuerpo = null;
  const tipo = respuesta.headers.get('content-type') || '';
  if (tipo.includes('application/json')) {
    cuerpo = await respuesta.json();
  }

  // Cualquier escritura deja obsoleto el panel general memoizado.
  if ((opciones.method || 'GET') !== 'GET') invalidarPanel();

  if (!respuesta.ok) {
    if (respuesta.status === 401 && !ruta.includes('/auth/login')) {
      sesion.cerrar();
      if (!location.hash.includes('login')) location.hash = '#/login';
    }
    throw new ErrorApi(mensajeDeError(cuerpo, respuesta.status), respuesta.status, cuerpo?.detail);
  }
  return cuerpo;
}

/**
 * El panel general lo piden la vista, la campana de alertas y el enlace
 * «Ver todos». Se memoriza unos segundos para no repetir la llamada en
 * cada renderizado; cualquier escritura lo invalida.
 */
const CACHE_PANEL_MS = 4000;
let cachePanel = null; // { promesa, sello }

function panelGeneral(forzar = false) {
  const ahora = Date.now();
  if (!forzar && cachePanel && ahora - cachePanel.sello < CACHE_PANEL_MS) {
    // Se guarda la promesa, no el resultado: así dos llamadas simultáneas
    // (la campana y la vista) comparten una sola petición.
    return cachePanel.promesa;
  }
  const promesa = pedir('/panel');
  cachePanel = { promesa, sello: ahora };
  promesa.catch(() => {
    if (cachePanel?.promesa === promesa) cachePanel = null;
  });
  return promesa;
}

export function invalidarPanel() {
  cachePanel = null;
}

const qs = (params = {}) => {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') p.append(k, v);
  }
  const s = p.toString();
  return s ? `?${s}` : '';
};

export const api = {
  salud: () => pedir('/salud'),

  auth: {
    entrar: (correo, contrasena) =>
      pedir('/auth/login', { method: 'POST', body: { correo, contrasena } }),
    salir: () => pedir('/auth/logout', { method: 'POST' }),
    yo: () => pedir('/auth/yo'),
    cambiarContrasena: (contrasena_actual, contrasena_nueva) =>
      pedir('/auth/cambiar-contrasena', {
        method: 'POST',
        body: { contrasena_actual, contrasena_nueva },
      }),
  },

  usuarios: {
    listar: (params) => pedir(`/usuarios${qs(params)}`),
    crear: (datos) => pedir('/usuarios', { method: 'POST', body: datos }),
    ver: (id) => pedir(`/usuarios/${id}`),
    actualizar: (id, datos) => pedir(`/usuarios/${id}`, { method: 'PATCH', body: datos }),
    cambiarEstado: (id, estado) =>
      pedir(`/usuarios/${id}${qs({ estado })}`, { method: 'DELETE' }),
  },

  catalogos: {
    /** Registro completo: la tabla necesita `activo`, `vat` y `contacto`. */
    clientes: (params) => pedir(`/clientes${qs(params)}`),
    crearCliente: (datos) => pedir('/clientes', { method: 'POST', body: datos }),
    verCliente: (id) => pedir(`/clientes/${id}`),
    actualizarCliente: (id, datos) => pedir(`/clientes/${id}`, { method: 'PATCH', body: datos }),
    productos: (params) => pedir(`/productos${qs(params)}`),
    crearProducto: (datos) => pedir('/productos', { method: 'POST', body: datos }),
    actualizarProducto: (id, datos) => pedir(`/productos/${id}`, { method: 'PATCH', body: datos }),
    fincas: (params) => pedir(`/fincas${qs(params)}`),
    crearFinca: (datos) => pedir('/fincas', { method: 'POST', body: datos }),
    verFinca: (id) => pedir(`/fincas/${id}`),
    actualizarFinca: (id, datos) => pedir(`/fincas/${id}`, { method: 'PATCH', body: datos }),
    listas: () => pedir('/catalogos'),
  },

  lotes: {
    listar: (params) => pedir(`/lotes${qs(params)}`),
    crear: (datos) => pedir('/lotes', { method: 'POST', body: datos }),
    ver: (id) => pedir(`/lotes/${id}`),
    actualizar: (id, datos) => pedir(`/lotes/${id}`, { method: 'PATCH', body: datos }),
    retirar: (id) => pedir(`/lotes/${id}`, { method: 'DELETE' }),
    inventario: () => pedir('/lotes/inventario'),
    calidad: (id) => pedir(`/lotes/${id}/calidad`),
    registrarCalidad: (id, datos) => pedir(`/lotes/${id}/calidad`, { method: 'PUT', body: datos }),
    trazabilidad: (id) => pedir(`/lotes/${id}/trazabilidad`),
    registrarEvento: (id, datos) =>
      pedir(`/lotes/${id}/trazabilidad`, { method: 'POST', body: datos }),
  },

  certificaciones: {
    listar: (params) => pedir(`/certificaciones${qs(params)}`),
    crear: (datos) => pedir('/certificaciones', { method: 'POST', body: datos }),
    anular: (id) => pedir(`/certificaciones/${id}`, { method: 'DELETE' }),
  },

  comercial: {
    solicitudesPedido: () => pedir('/solicitudes-pedido'),
    crearSolicitudPedido: (datos) => pedir('/solicitudes-pedido', { method: 'POST', body: datos }),
    cotizaciones: (params) => pedir(`/cotizaciones${qs(params)}`),
    crearCotizacion: (datos) => pedir('/cotizaciones', { method: 'POST', body: datos }),
    actualizarCotizacion: (id, datos) => pedir(`/cotizaciones/${id}`, { method: 'PATCH', body: datos }),
    aceptarCotizacion: (id, datos) =>
      pedir(`/cotizaciones/${id}/aceptar`, { method: 'POST', body: datos }),
    exportaciones: (params) => pedir(`/exportaciones${qs(params)}`),
    crearExportacion: (datos) => pedir('/exportaciones', { method: 'POST', body: datos }),
    verExportacion: (id) => pedir(`/exportaciones/${id}`),
    actualizarExportacion: (id, datos) =>
      pedir(`/exportaciones/${id}`, { method: 'PATCH', body: datos }),
    documentos: (idExp) => pedir(`/exportaciones/${idExp}/documentos`),
    crearDocumento: (idExp, datos) =>
      pedir(`/exportaciones/${idExp}/documentos`, { method: 'POST', body: datos }),
    actualizarDocumento: (id, datos) => pedir(`/documentos/${id}`, { method: 'PATCH', body: datos }),
    autorizarDocumento: (id) => pedir(`/documentos/${id}/autorizar`, { method: 'POST' }),
  },

  logistica: {
    contenedores: (params) => pedir(`/contenedores${qs(params)}`),
    crearContenedor: (datos) => pedir('/contenedores', { method: 'POST', body: datos }),
    actualizarContenedor: (id, datos) => pedir(`/contenedores/${id}`, { method: 'PATCH', body: datos }),
    envios: (params) => pedir(`/envios${qs(params)}`),
    crearEnvio: (datos) => pedir('/envios', { method: 'POST', body: datos }),
    verEnvio: (id) => pedir(`/envios/${id}`),
    actualizarEnvio: (id, datos) => pedir(`/envios/${id}`, { method: 'PATCH', body: datos }),
    anularEnvio: (id) => pedir(`/envios/${id}`, { method: 'DELETE' }),
    trazabilidadEnvio: (id) => pedir(`/envios/${id}/trazabilidad`),
  },

  financiero: {
    pagos: (params) => pedir(`/pagos${qs(params)}`),
    crearPago: (datos) => pedir('/pagos', { method: 'POST', body: datos }),
    actualizarPago: (id, datos) => pedir(`/pagos/${id}`, { method: 'PATCH', body: datos }),
    anularPago: (id) => pedir(`/pagos/${id}/anular`, { method: 'POST' }),
    eliminarPago: (id) => pedir(`/pagos/${id}`, { method: 'DELETE' }),
    resumen: () => pedir('/financiero/resumen'),
  },

  notificaciones: {
    listar: (params) => pedir(`/notificaciones${qs(params)}`),
    contador: () => pedir('/notificaciones/contador'),
    leer: (id) => pedir(`/notificaciones/${id}/leer`, { method: 'POST' }),
    leerTodas: () => pedir('/notificaciones/leer-todas', { method: 'POST' }),
    crear: (datos) => pedir('/notificaciones', { method: 'POST', body: datos }),
  },

  auditoria: {
    listar: (params) => pedir(`/auditoria${qs(params)}`),
    ver: (id) => pedir(`/auditoria/${id}`),
  },

  sistema: {
    integraciones: () => pedir('/integraciones'),
    probarCorreo: (datos) => pedir('/integraciones/correo', { method: 'POST', body: datos }),
    seguimiento: (numero) =>
      pedir(`/integraciones/seguimiento/${encodeURIComponent(numero)}`, { method: 'POST' }),
    bitacora: (params) => pedir(`/integraciones/bitacora${qs(params)}`),
    tiposCambio: () => pedir('/tipos-cambio'),
    crearTipoCambio: (datos) => pedir('/tipos-cambio', { method: 'POST', body: datos }),
    actualizarTiposCambio: () => pedir('/tipos-cambio/actualizar', { method: 'POST' }),
    convertir: (params) => pedir(`/monedas/convertir${qs(params)}`),
    respaldos: () => pedir('/respaldos'),
    crearRespaldo: () => pedir('/respaldos', { method: 'POST' }),
    verificarRespaldo: (id) => pedir(`/respaldos/${id}/verificar`, { method: 'POST' }),
    descargarRespaldo: (id) => `${BASE}/respaldos/${id}/descargar`,
  },

  panel: {
    datos: () => panelGeneral(),
    recargar: () => panelGeneral(true),
    kpis: () => pedir('/reportes/kpis'),
  },
};
