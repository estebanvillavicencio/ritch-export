/**
 * Pantalla de inicio de sesión (HU-02).
 */

import { api, sesion } from './api.js';
import { el, montar, icono } from './ui.js';
import { reiniciarApp } from './app.js';

export function vistaLogin(contenedor) {
  if (sesion.activo) {
    // Igual que después de entrar: el cliente europeo va a su portal.
    location.hash = sesion.usuario?.rol === 'Cliente europeo' ? '#/portal' : '#/panel';
    return;
  }

  const cajaError = el('div');
  const correo = el('input', {
    type: 'email', name: 'correo', id: 'c-correo', required: true,
    placeholder: 'tucorreo@ritch.com', autocomplete: 'username', value: '',
  });
  const contrasena = el('input', {
    type: 'password', name: 'contrasena', id: 'c-contrasena', required: true,
    placeholder: '••••••••', autocomplete: 'current-password',
  });
  const boton = el('button.btn.btn-primary', { type: 'submit', style: { width: '100%', justifyContent: 'center', padding: '11px' } }, 'Entrar');

  const form = el(
    'form',
    {
      onsubmit: async (e) => {
        e.preventDefault();
        montar(cajaError);
        boton.disabled = true;
        boton.textContent = 'Verificando…';
        try {
          const datos = await api.auth.entrar(correo.value.trim(), contrasena.value);
          sesion.iniciar(datos.access_token, datos.usuario);
          // La barra lateral depende del rol: se reconstruye desde cero.
          reiniciarApp();
          // No todo el mundo entra por el panel: el cliente europeo no tiene
          // acceso a él, así que si lo mandáramos ahí vería un «acceso
          // restringido» apenas entra. La misma regla de `app.js`.
          location.hash = datos.usuario.rol === 'Cliente europeo' ? '#/portal' : '#/panel';
        } catch (err) {
          montar(cajaError, el('div.login-error', {}, err.message));
          contrasena.value = '';
          contrasena.focus();
        } finally {
          boton.disabled = false;
          boton.textContent = 'Entrar';
        }
      },
    },
    cajaError,
    el('div.field', {}, el('label', { for: 'c-correo' }, 'Correo electrónico'), correo),
    el('div.field', {}, el('label', { for: 'c-contrasena' }, 'Contraseña'), contrasena),
    boton
  );

  montar(
    contenedor,
    el(
      'div.login-page',
      {},
      el(
        'div.login-aside',
        {},
        el(
          'div',
          {},
          el(
            'div.brand',
            { style: { padding: 0, marginBottom: '38px' } },
            el('div.brand-mark', {}, 'R'),
            el('div', {}, el('div.brand-name', {}, 'RiTech'), el('div.brand-sub', {}, 'Café · Cacao · UE'))
          ),
          el('h2', {}, 'Sistema de Gestión de Exportación de Café y Cacao'),
          el(
            'p',
            {},
            'Centraliza el origen, la calidad, el cumplimiento del Reglamento europeo ' +
              'de deforestación y la logística de cada envío a la Unión Europea.'
          ),
          el(
            'div.login-mods',
            {},
            ...[
              'Productores, fincas y lotes con trazabilidad completa',
              'Resultados de catación y laboratorio',
              'Certificaciones EUDR, orgánico y Fairtrade',
              'Clientes, cotizaciones, contratos y documentos',
              'Contenedores, navieras, puertos y seguimiento',
            ].map((t) => el('div.login-mod', {}, icono('check'), t))
          )
        ),
        el('div.login-foot', {}, 'RiTech SAS · Sprint 2 · Metodología Scrum')
      ),
      el(
        'div.login-form-wrap',
        {},
        el(
          'div.login-form',
          {},
          el('h1', {}, 'Iniciar sesión'),
          el('p', {}, 'Accede con las credenciales asignadas por el administrador.'),
          form,
          el('p.small.muted.mt-1', {}, 'Si necesitas acceso, solicita tus credenciales al administrador del sistema.')
        )
      )
    )
  );

  correo.focus();
}
