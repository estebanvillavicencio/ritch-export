/**
 * Módulo de Usuarios y Roles (HU-01 · Informe §6.1).
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, modal, confirmar, campo,
  filaCampos, leerFormulario, ok, error, debounce,
} from '../ui.js';

const ROLES = [
  'Administrador', 'Comercial', 'Logística', 'Calidad', 'Financiero', 'Cliente europeo',
];
const ESTADOS = ['activo', 'inactivo', 'bloqueado'];

/**
 * Empresas compradoras para el selector del rol «Cliente europeo». Se llena al
 * cargar la vista: la lista de clientes la rechaza el rol de cliente, pero quien
 * administra usuarios es administrador y sí la puede pedir.
 */
let EMPRESAS = [{ valor: '', texto: '— Sin empresa —' }];

export async function vistaUsuarios(raiz) {
  montar(raiz, cargando('Cargando usuarios…'));

  if (!sesion.puede('Administrador')) {
    montar(
      raiz,
      el(
        'div.panel',
        {},
        el('div.alert.rust', {}, icono('candado'), el('div', {}, 'Solo un administrador puede gestionar usuarios y roles.'))
      )
    );
    return;
  }

  const cont = el('div');
  let busqueda = '';

  // El selector de empresa del formulario necesita el catálogo de clientes.
  // Si la petición falla, se deja el valor en blanco: la API igual lo va a
  // pedir al crear la cuenta de cliente.
  try {
    const lista = await api.catalogos.clientes({ tamano: 100 });
    if (lista.items?.length) {
      EMPRESAS = [
        { valor: '', texto: '— Sin empresa —' },
        ...lista.items.map((c) => ({ valor: String(c.id_cliente), texto: c.nombre_empresa })),
      ];
    }
  } catch { /* sin catálogo: el campo queda solo con «Sin empresa» */ }

  async function refrescar() {
    const datos = await api.usuarios.listar({ q: busqueda, tamano: 100 });
    montar(
      cont,
      datos.items.length ? tabla(datos.items, refrescar) : vacio('No hay usuarios que coincidan con la búsqueda.')
    );
  }

  const buscador = el('input', {
    type: 'search',
    placeholder: 'Buscar por nombre o correo…',
    oninput: debounce((e) => {
      busqueda = e.target.value;
      refrescar();
    }, 300),
  });

  montar(
    raiz,
    el(
      'div.panel',
      {},
      el(
        'div.panel-head',
        {},
        el('h3', {}, 'Usuarios y roles'),
        el(
          'div.flex',
          {},
          el(
            'div.search',
            { style: { width: '260px' } },
            icono('buscar'),
            buscador
          ),
          el(
            'button.btn.btn-primary.btn-sm',
            { onclick: () => formUsuario(refrescar) },
            icono('mas'),
            'Nuevo usuario'
          )
        )
      ),
      el(
        'p.small.muted',
        {},
        'Los usuarios no se eliminan: se cambia su estado para conservar la trazabilidad ' +
          'de las exportaciones que registraron.'
      ),
      cont
    )
  );

  await refrescar();
}

function tabla(usuarios, refrescar) {
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
          el('th', {}, 'Usuario'),
          el('th', {}, 'Rol'),
          el('th', {}, 'Empresa'),
          el('th', {}, 'Estado'),
          el('th', {}, 'Creado'),
          el('th', {}, 'Último acceso'),
          el('th', {}, '')
        )
      ),
      el(
        'tbody',
        {},
        ...usuarios.map((u) => {
          const esYo = sesion.usuario?.id_usuario === u.id_usuario;
          return el(
            'tr',
            {},
            el(
              'td',
              {},
              el(
                'div.flex',
                {},
                el('div.avatar', { style: { background: 'var(--paper-2)', color: 'var(--ink)' } }, f.iniciales(u.nombre)),
                el(
                  'div',
                  {},
                  el('div.cell-main', {}, u.nombre, esYo ? el('span.status.azul', { style: { marginLeft: '6px' } }, 'tú') : null),
                  el('div.cell-sub', {}, u.correo)
                )
              )
            ),
            el('td', {}, el('span.status.gris', {}, u.rol)),
            // La empresa solo aparece para los contactos de clientes europeos.
            el('td.small', {}, u.nombre_cliente || '—'),
            el(
              'td',
              {},
              u.estado === 'activo' ? pill('Vigente') : u.estado === 'inactivo' ? pill('Pendiente') : pill('Rechazado')
            ),
            el('td.small.muted', {}, f.fechaHora(u.creado_en)),
            el('td.small.muted', {}, f.fechaHora(u.ultimo_acceso)),
            el(
              'td',
              { class: 'right nowrap' },
              el(
                'div.flex',
                { style: { justifyContent: 'flex-end' } },
                el(
                  'button.btn.btn-sm',
                  { title: 'Editar', onclick: () => formUsuario(refrescar, u) },
                  icono('editar')
                ),
                !esYo
                  ? el(
                      'button.btn.btn-sm.btn-danger',
                      {
                        title: u.estado === 'activo' ? 'Desactivar' : 'Activar',
                        onclick: async () => {
                          const nuevo = u.estado === 'activo' ? 'inactivo' : 'activo';
                          const confirmado = await confirmar({
                            titulo: u.estado === 'activo' ? 'Desactivar usuario' : 'Activar usuario',
                            mensaje: `¿${u.estado === 'activo' ? 'Desactivar' : 'Activar'} el acceso de ${u.nombre}?`,
                            textoOk: u.estado === 'activo' ? 'Desactivar' : 'Activar',
                            peligro: u.estado === 'activo',
                          });
                          if (!confirmado) return;
                          try {
                            await api.usuarios.cambiarEstado(u.id_usuario, nuevo);
                            ok('Estado actualizado');
                            refrescar();
                          } catch (e) {
                            error(e.message);
                          }
                        },
                      },
                      u.estado === 'activo' ? 'Desactivar' : 'Activar'
                    )
                  : null
              )
            )
          );
        })
      )
    )
  );
}

function formUsuario(refrescar, usuario = null) {
  const edicion = Boolean(usuario);
  const form = el(
    'form',
    { onsubmit: (e) => e.preventDefault() },
    campo({
      etiqueta: 'Nombre completo', nombre: 'nombre', requerido: true,
      valor: usuario?.nombre || '',
    }),
    campo({
      etiqueta: 'Correo electrónico', nombre: 'correo', tipo: 'email', requerido: true,
      valor: usuario?.correo || '',
    }),
    filaCampos(
      campo({
        etiqueta: 'Rol', nombre: 'rol', tipo: 'select', opciones: ROLES,
        valor: usuario?.rol || 'Comercial', requerido: true,
        pista: 'Determina a qué módulos tiene acceso (RR-004).',
      }),
      // La empresa solo importa para el rol «Cliente europeo»: es lo que hace que
      // su portal muestre únicamente sus pedidos y no los de los demás. Se
      // escribe siempre; la API descarta el valor si el rol no es de cliente.
      campo({
        etiqueta: 'Empresa (si es cliente europeo)', nombre: 'id_cliente',
        tipo: 'select', opciones: EMPRESAS,
        valor: usuario?.id_cliente ? String(usuario.id_cliente) : '',
        pista: 'Obligatoria para «Cliente europeo». Con ella, el portal muestra solo lo de esa empresa.',
      }),
      edicion
        ? campo({
            etiqueta: 'Estado', nombre: 'estado', tipo: 'select', opciones: ESTADOS,
            valor: usuario.estado,
          })
        : campo({
            etiqueta: 'Contraseña', nombre: 'contrasena', tipo: 'password',
            requerido: true, atributos: { minlength: '8', autocomplete: 'new-password' },
            pista: 'Mínimo 8 caracteres.',
          })
    ),
    edicion
      ? campo({
          etiqueta: 'Nueva contraseña', nombre: 'contrasena', tipo: 'password',
          atributos: { minlength: '8', autocomplete: 'new-password' },
          pista: 'Déjalo vacío para mantener la contraseña actual.',
        })
      : null
  );

  const { cerrar } = modal({
    titulo: edicion ? `Editar ${usuario.nombre}` : 'Nuevo usuario',
    cuerpo: form,
    pie: [
      el('button.btn', { onclick: () => cerrar() }, 'Cancelar'),
      el(
        'button.btn.btn-primary',
        {
          onclick: async () => {
            const d = leerFormulario(form);
            if (!d.nombre || !d.correo) return error('Nombre y correo son obligatorios');
            if (!edicion && (!d.contrasena || d.contrasena.length < 8)) {
              return error('La contraseña debe tener al menos 8 caracteres');
            }
            // Sin empresa no hay portal: la API lo rechaza, pero es más claro
            // avisarlo aquí, donde se está eligiendo el rol.
            if (d.rol === 'Cliente europeo' && !d.id_cliente) {
              return error('Un cliente europeo necesita su empresa: el portal muestra solo sus pedidos');
            }
            const idCliente = d.id_cliente ? Number(d.id_cliente) : null;
            try {
              if (edicion) {
                const cambios = { nombre: d.nombre, correo: d.correo, rol: d.rol };
                if (d.estado) cambios.estado = d.estado;
                if (d.contrasena) cambios.contrasena = d.contrasena;
                cambios.id_cliente = idCliente;
                await api.usuarios.actualizar(usuario.id_usuario, cambios);
                ok('Usuario actualizado');
              } else {
                await api.usuarios.crear({
                  nombre: d.nombre,
                  correo: d.correo,
                  rol: d.rol,
                  contrasena: d.contrasena,
                  id_cliente: idCliente,
                });
                ok('Usuario creado');
              }
              cerrar();
              refrescar();
            } catch (e) {
              error(e.message);
            }
          },
        },
        edicion ? 'Guardar cambios' : 'Crear usuario'
      ),
    ],
  });
}
