/**
 * Portal del cliente europeo (Informe §8).
 *
 * El cliente entra con su propio usuario y solo ve la información de sus
 * operaciones: catálogo, certificaciones, pedidos, seguimiento, contratos,
 * pagos y descarga de documentos autorizados.
 *
 * HU-19 · el portal está disponible en siete idiomas y muestra los importes
 * en EUR, USD o COP. Las tasas llegan de `/api/tipos-cambio`; no hay ninguna
 * tasa escrita en el código del frontend.
 */

import { api, sesion } from '../api.js';
import {
  el, montar, icono, pill, vacio, cargando, f, campo, leerFormulario, modal,
  ok, error,
} from '../ui.js';

const IDIOMAS = [
  { valor: 'es', texto: 'Español' },
  { valor: 'en', texto: 'English' },
  { valor: 'de', texto: 'Deutsch' },
  { valor: 'fr', texto: 'Français' },
  { valor: 'it', texto: 'Italiano' },
  { valor: 'nl', texto: 'Nederlands' },
  { valor: 'sv', texto: 'Svenska' },
];
const MONEDAS = ['EUR', 'USD', 'COP'];

/** Locale de `Intl` para cada idioma del portal. */
const LOCALES = {
  es: 'es-ES', en: 'en-GB', de: 'de-DE', fr: 'fr-FR',
  it: 'it-IT', nl: 'nl-NL', sv: 'sv-SE',
};

/**
 * HU-19 · textos del portal en los siete idiomas de la Unión que atiende
 * RiTech. Las tasas de cambio ya no están escritas aquí: llegan de
 * `/api/tipos-cambio` y se actualizan desde el módulo de sistema.
 */
const TEXTOS = {
  es: {
    portal: 'Portal de', operaciones: 'operación', operacionesPlural: 'operaciones',
    envios: 'envío', enviosPlural: 'envíos', documentos: 'documentos autorizados',
    catalogo: 'Catálogo de productos', consultar: 'Precio a consultar',
    pedidos: 'Mis pedidos', misEnvios: 'Mis envíos', docs: 'Documentos autorizados',
    contrato: 'Contrato', fecha: 'Fecha', destino: 'Destino', peso: 'Peso',
    valor: 'Valor', estado: 'Estado', documentosCol: 'Documentos',
    seguimiento: 'N.º de seguimiento', naviera: 'Naviera', ruta: 'Ruta',
    salida: 'Salida', llegada: 'Llegada', sinPedidos: 'Todavía no tienes pedidos registrados.',
    sinEnvios: 'Todavía no tienes envíos registrados.',
    sinDocs: 'Todavía no hay documentos autorizados para descargar.',
    catalogoVacio: 'El catálogo está siendo actualizado.',
    idioma: 'Idioma', moneda: 'Moneda', pendiente: 'Pendiente',
    ver: 'Ver', numero: 'Número', emitido: 'Emitido', contratoMin: 'contrato',
  },
  en: {
    portal: 'Portal of', operaciones: 'operation', operacionesPlural: 'operations',
    envios: 'shipment', enviosPlural: 'shipments', documentos: 'authorised documents',
    catalogo: 'Product catalogue', consultar: 'Price on request',
    pedidos: 'My orders', misEnvios: 'My shipments', docs: 'Authorised documents',
    contrato: 'Contract', fecha: 'Date', destino: 'Destination', peso: 'Weight',
    valor: 'Value', estado: 'Status', documentosCol: 'Documents',
    seguimiento: 'Tracking number', naviera: 'Carrier', ruta: 'Route',
    salida: 'Departure', llegada: 'Arrival', sinPedidos: 'You have no orders yet.',
    sinEnvios: 'You have no shipments yet.',
    sinDocs: 'No authorised documents to download yet.',
    catalogoVacio: 'The catalogue is being updated.',
    idioma: 'Language', moneda: 'Currency', pendiente: 'Pending',
    ver: 'View', numero: 'Number', emitido: 'Issued', contratoMin: 'contract',
  },
  de: {
    portal: 'Portal von', operaciones: 'Vorgang', operacionesPlural: 'Vorgänge',
    envios: 'Sendung', enviosPlural: 'Sendungen', documentos: 'autorisierte Dokumente',
    catalogo: 'Produktkatalog', consultar: 'Preis auf Anfrage',
    pedidos: 'Meine Bestellungen', misEnvios: 'Meine Sendungen', docs: 'Autorisierte Dokumente',
    contrato: 'Vertrag', fecha: 'Datum', destino: 'Ziel', peso: 'Gewicht',
    valor: 'Wert', estado: 'Status', documentosCol: 'Dokumente',
    seguimiento: 'Sendungsnummer', naviera: 'Reederei', ruta: 'Route',
    salida: 'Abfahrt', llegada: 'Ankunft', sinPedidos: 'Noch keine Bestellungen.',
    sinEnvios: 'Noch keine Sendungen.', sinDocs: 'Noch keine autorisierten Dokumente.',
    catalogoVacio: 'Der Katalog wird aktualisiert.',
    idioma: 'Sprache', moneda: 'Währung', pendiente: 'Ausstehend',
    ver: 'Ansehen', numero: 'Nummer', emitido: 'Ausgestellt', contratoMin: 'Vertrag',
  },
  fr: {
    portal: 'Portail de', operaciones: 'opération', operacionesPlural: 'opérations',
    envios: 'expédition', enviosPlural: 'expéditions', documentos: 'documents autorisés',
    catalogo: 'Catalogue de produits', consultar: 'Prix sur demande',
    pedidos: 'Mes commandes', misEnvios: 'Mes expéditions', docs: 'Documents autorisés',
    contrato: 'Contrat', fecha: 'Date', destino: 'Destination', peso: 'Poids',
    valor: 'Valeur', estado: 'Statut', documentosCol: 'Documents',
    seguimiento: 'N.º de suivi', naviera: 'Transporteur', ruta: 'Itinéraire',
    salida: 'Départ', llegada: 'Arrivée', sinPedidos: 'Aucune commande enregistrée.',
    sinEnvios: 'Aucune expédition enregistrée.', sinDocs: 'Aucun document autorisé à télécharger.',
    catalogoVacio: 'Le catalogue est en cours de mise à jour.',
    idioma: 'Langue', moneda: 'Devise', pendiente: 'En attente',
    ver: 'Voir', numero: 'Numéro', emitido: 'Émis', contratoMin: 'contrat',
  },
  it: {
    portal: 'Portale di', operaciones: 'operazione', operacionesPlural: 'operazioni',
    envios: 'spedizione', enviosPlural: 'spedizioni', documentos: 'documenti autorizzati',
    catalogo: 'Catalogo prodotti', consultar: 'Prezzo su richiesta',
    pedidos: 'I miei ordini', misEnvios: 'Le mie spedizioni', docs: 'Documenti autorizzati',
    contrato: 'Contratto', fecha: 'Data', destino: 'Destinazione', peso: 'Peso',
    valor: 'Valore', estado: 'Stato', documentosCol: 'Documenti',
    seguimiento: 'N.º di tracciamento', naviera: 'Compagnia', ruta: 'Percorso',
    salida: 'Partenza', llegada: 'Arrivo', sinPedidos: 'Nessun ordine registrato.',
    sinEnvios: 'Nessuna spedizione registrata.', sinDocs: 'Nessun documento autorizzato da scaricare.',
    catalogoVacio: 'Il catalogo è in aggiornamento.',
    idioma: 'Lingua', moneda: 'Valuta', pendiente: 'In attesa',
    ver: 'Vedi', numero: 'Numero', emitido: 'Emesso', contratoMin: 'contratto',
  },
  nl: {
    portal: 'Portaal van', operaciones: 'transactie', operacionesPlural: 'transacties',
    envios: 'zending', enviosPlural: 'zendingen', documentos: 'geautoriseerde documenten',
    catalogo: 'Productcatalogus', consultar: 'Prijs op aanvraag',
    pedidos: 'Mijn bestellingen', misEnvios: 'Mijn zendingen', docs: 'Geautoriseerde documenten',
    contrato: 'Contract', fecha: 'Datum', destino: 'Bestemming', peso: 'Gewicht',
    valor: 'Waarde', estado: 'Status', documentosCol: 'Documenten',
    seguimiento: 'Trackingnummer', naviera: 'Rederij', ruta: 'Route',
    salida: 'Vertrek', llegada: 'Aankomst', sinPedidos: 'Nog geen bestellingen.',
    sinEnvios: 'Nog geen zendingen.', sinDocs: 'Nog geen geautoriseerde documenten.',
    catalogoVacio: 'De catalogus wordt bijgewerkt.',
    idioma: 'Taal', moneda: 'Valuta', pendiente: 'In afwachting',
    ver: 'Bekijken', numero: 'Nummer', emitido: 'Uitgegeven', contratoMin: 'contract',
  },
  sv: {
    portal: 'Portal för', operaciones: 'transaktion', operacionesPlural: 'transaktioner',
    envios: 'sändning', enviosPlural: 'sändningar', documentos: 'auktoriserade dokument',
    catalogo: 'Produktkatalog', consultar: 'Pris på begäran',
    pedidos: 'Mina beställningar', misEnvios: 'Mina sändningar', docs: 'Auktoriserade dokument',
    contrato: 'Kontrakt', fecha: 'Datum', destino: 'Destination', peso: 'Vikt',
    valor: 'Värde', estado: 'Status', documentosCol: 'Dokument',
    seguimiento: 'Spårningsnummer', naviera: 'Rederi', ruta: 'Rutt',
    salida: 'Avgång', llegada: 'Ankomst', sinPedidos: 'Inga beställningar ännu.',
    sinEnvios: 'Inga sändningar ännu.', sinDocs: 'Inga auktoriserade dokument att ladda ner.',
    catalogoVacio: 'Katalogen uppdateras.',
    idioma: 'Språk', moneda: 'Valuta', pendiente: 'Väntande',
    ver: 'Visa', numero: 'Nummer', emitido: 'Utfärdat', contratoMin: 'kontrakt',
  },
};

export async function vistaPortal(raiz) {
  montar(raiz, cargando('Cargando su portal…'));

  const usuario = sesion.usuario;
  if (!usuario) {
    montar(raiz, el('div.alert.rust', {}, icono('candado'), el('div', {}, 'Inicia sesión para acceder al portal.')));
    return;
  }

  let exportaciones, productos, envios, solicitudes;
  try {
    [exportaciones, envios, productos, solicitudes] = await Promise.all([
      api.comercial.exportaciones({ tamano: 100 }),
      api.logistica.envios({ tamano: 100 }),
      api.catalogos.productos({ tamano: 100 }),
      api.comercial.solicitudesPedido(),
    ]);
  } catch (e) {
    montar(raiz, el('div.alert.rust', {}, icono('alerta'), el('div', {}, e.message)));
    return;
  }

  // HU-19 · las tasas vienen de la API. Si el servicio no responde, el portal
  // sigue funcionando en EUR: nunca se inventan conversiones.
  const tasas = { EUR: 1 };
  try {
    const tipos = await api.sistema.tiposCambio();
    for (const t of tipos) tasas[t.moneda] = Number(t.tasa);
  } catch { /* se conserva solo EUR */ }
  const monedasDisponibles = MONEDAS.filter((m) => Number(tasas[m]) > 0);
  const monedas = monedasDisponibles.length ? monedasDisponibles : ['EUR'];

  // La API ya devuelve solo las operaciones de la empresa del cliente: aquí no
  // se vuelve a filtrar, porque el filtro que manda es el del servidor.
  const propias = exportaciones.items;
  const propiosEnvios = envios.items;
  const iniciales = { idioma: 'es', moneda: 'EUR' };
  try {
    Object.assign(iniciales, JSON.parse(localStorage.getItem('ritch_portal_prefs') || '{}'));
  } catch { /* preferencias corruptas: se usan las de fábrica */ }
  if (!monedas.includes(iniciales.moneda)) iniciales.moneda = 'EUR';

  const cont = el('div');

  /** Traduce una clave al idioma elegido, con español como respaldo. */
  const t = (clave) => TEXTOS[iniciales.idioma]?.[clave] ?? TEXTOS.es[clave] ?? clave;

  function convertir(valor, monedaBase) {
    const origen = Number(tasas[monedaBase] ?? 1);
    const destino = Number(tasas[iniciales.moneda] ?? 1);
    return (valor / origen) * destino;
  }

  function formatear(valor, monedaBase = 'EUR') {
    if (valor === null || valor === undefined) return '—';
    return new Intl.NumberFormat(LOCALES[iniciales.idioma] || 'es-ES', {
      style: 'currency',
      currency: iniciales.moneda,
      maximumFractionDigits: 0,
    }).format(convertir(valor, monedaBase));
  }

  function pintar() {
    montar(
      cont,
      el(
        'div.portal-banner',
        {},
        el(
          'div',
          {},
          el('h2', {}, `${t('portal')} ${usuario.nombre}`),
          el(
            'p',
            {},
            [
              usuario.nombre_cliente && `${usuario.nombre_cliente} · `,
              `${propias.length} ${propias.length === 1 ? t('operaciones') : t('operacionesPlural')}`,
              ` · ${propiosEnvios.length} ${propiosEnvios.length === 1 ? t('envios') : t('enviosPlural')}`,
              ` · ${t('documentos')}`,
            ]
              .filter(Boolean)
              .join('')
          )
        ),
        el(
          'div.portal-controls',
          {},
          el(
            'label',
            { style: { fontSize: '11.5px', color: '#B7A891' } },
            `${t('idioma')} `,
            el(
              'select',
              {
                onchange: (e) => {
                  iniciales.idioma = e.target.value;
                  guardarPrefs();
                },
              },
              ...IDIOMAS.map((i) => el('option', { value: i.valor, selected: i.valor === iniciales.idioma }, i.texto))
            )
          ),
          el(
            'label',
            { style: { fontSize: '11.5px', color: '#B7A891' } },
            `${t('moneda')} `,
            el(
              'select',
              {
                onchange: (e) => {
                  iniciales.moneda = e.target.value;
                  guardarPrefs();
                },
              },
              ...monedas.map((m) => el('option', { value: m, selected: m === iniciales.moneda }, m))
            )
          )
        )
      ),

      catalogoProductos(productos.items, formatear, t, enviarPedido),

      el(
        'div.panel.mt-2',
        {},
        el('div.panel-head', {}, el('h3', {}, 'Solicitudes de pedido')),
        solicitudes.length ? tablaSolicitudes(solicitudes) : vacio('Aún no has enviado solicitudes de pedido.')
      ),

      el(
        'div.panel.mt-2',
        {},
        el('div.panel-head', {}, el('h3', {}, t('pedidos'))),
        propias.length ? tablaOperaciones(propias, formatear, t) : vacio(t('sinPedidos'))
      ),

      el(
        'div.panel.mt-2',
        {},
        el('div.panel-head', {}, el('h3', {}, t('misEnvios'))),
        propiosEnvios.length ? tablaEnvios(propiosEnvios, t) : vacio(t('sinEnvios'))
      ),

      el(
        'div.panel.mt-2',
        {},
        el('div.panel-head', {}, el('h3', {}, t('docs'))),
        documentos(propias, t)
      )
    );
  }

  function guardarPrefs() {
    localStorage.setItem('ritch_portal_prefs', JSON.stringify(iniciales));
    pintar();
  }

  async function enviarPedido(producto, formulario, boton) {
    boton.disabled = true;
    try {
      const datos = leerFormulario(formulario);
      await api.comercial.crearSolicitudPedido({
        id_producto: producto.id_producto,
        cantidad_kg: Number(datos.cantidad_kg),
        incoterm: datos.incoterm,
        puerto_destino: datos.puerto_destino || null,
        observaciones: datos.observaciones || null,
      });
      solicitudes = await api.comercial.solicitudesPedido();
      ok('Solicitud enviada. El equipo comercial revisará tu pedido.');
      pintar();
    } catch (e) {
      error(e.message);
      boton.disabled = false;
    }
  }

  pintar();
  montar(raiz, cont);
}

function catalogoProductos(productos, formatear, t, solicitarPedido) {
  return el(
    'div.panel',
    {},
    el('div.panel-head', {}, el('h3', {}, t('catalogo'))),
    productos.length
      ? el(
          'div.grid3',
          {},
          ...productos.map((p) =>
            el(
              'div',
              {
                style: {
                  border: '1px solid var(--line)',
                  borderRadius: '8px',
                  padding: '13px 15px',
                },
              },
              el(
                'div.flex',
                { style: { justifyContent: 'space-between', alignItems: 'flex-start' } },
                el('div', {}, el('div.cell-main', {}, p.nombre), el('div.cell-sub', {}, p.variedad || p.tipo)),
                el('span.tag', { class: p.tipo === 'Cacao' ? 'cacao' : 'cafe' }, p.tipo)
              ),
              el('p.small.muted.mt-1', {}, p.descripcion || ''),
              el(
                'div.mt-1',
                { style: { fontFamily: 'Fraunces, serif', fontSize: '18px' } },
                p.precio_referencia_eur
                  ? `${formatear(p.precio_referencia_eur)} / kg`
                  : t('consultar')
              ),
              formularioPedido(p, solicitarPedido)
            )
          )
        )
      : vacio(t('catalogoVacio'))
  );
}

function formularioPedido(producto, enviarPedido) {
  let formulario;
  const boton = el('button.btn.btn-primary.btn-sm', { type: 'submit' }, 'Enviar solicitud');
  formulario = el(
    'form.pedido-inline-form',
    { onsubmit: (e) => { e.preventDefault(); enviarPedido(producto, formulario, boton); } },
    campo({ etiqueta: 'Cantidad solicitada (kg)', nombre: 'cantidad_kg', tipo: 'number', requerido: true, min: '1', step: '0.01', placeholder: 'Por ejemplo, 5000' }),
    campo({ etiqueta: 'Incoterm', nombre: 'incoterm', tipo: 'select', opciones: ['EXW','FCA','CPT','CIP','DAP','DPU','DDP','FAS','FOB','CFR','CIF'], valor: 'FOB' }),
    campo({ etiqueta: 'Puerto de destino', nombre: 'puerto_destino', placeholder: 'Por ejemplo, Rotterdam' }),
    campo({ etiqueta: 'Detalles adicionales', nombre: 'observaciones', tipo: 'textarea', placeholder: 'Calidad, certificaciones u otros requisitos', ancho: 'full' }),
    el('div.flex', { style: { justifyContent: 'flex-end' } }, boton)
  );
  return el('details.pedido-inline', {},
    el('summary.btn.btn-primary.btn-sm.mt-1', {}, 'Solicitar pedido'),
    formulario
  );
}

function tablaSolicitudes(solicitudes) {
  return el('div.table-wrap', {}, el('table', {},
    el('thead', {}, el('tr', {},
      el('th', {}, 'Solicitud'), el('th', {}, 'Fecha'), el('th', {}, 'Producto'),
      el('th.tnum', {}, 'Cantidad'), el('th', {}, 'Destino'), el('th', {}, 'Estado')
    )),
    el('tbody', {}, ...solicitudes.map((s) => el('tr', {},
      el('td.mono.cell-main', {}, `SOL-${String(s.id_solicitud).padStart(5, '0')}`),
      el('td.small', {}, f.fecha(s.created_at)),
      el('td.small', {}, s.producto_nombre),
      el('td.tnum', {}, f.kilos2(Number(s.cantidad_kg))),
      el('td.small', {}, f.texto(s.puerto_destino)),
      el('td', {}, pill(s.estado))
    )))
  ));
}

function tablaOperaciones(operaciones, formatear, t) {
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
          el('th', {}, t('contrato')),
          el('th', {}, t('fecha')),
          el('th', {}, t('destino')),
          el('th.tnum', {}, t('peso')),
          el('th.tnum', {}, t('valor')),
          el('th', {}, t('estado')),
          el('th', {}, t('documentosCol'))
        )
      ),
      el(
        'tbody',
        {},
        ...operaciones.map((x) => {
          const autorizados = (x.documentos || []).filter((d) => d.autorizado_cliente);
          return el(
            'tr',
            {},
            el('td.mono.cell-main', {}, f.texto(x.numero_contrato)),
            el('td.small', {}, f.fecha(x.fecha)),
            el('td.small', {}, `${f.texto(x.puerto_origen)} → ${f.texto(x.puerto_destino)}`),
            el('td.tnum', {}, f.toneladas(x.total_kg)),
            el('td.tnum', {}, formatear(x.valor_total, x.moneda)),
            el('td', {}, pill(x.estado)),
            el(
              'td',
              {},
              autorizados.length
                ? el(
                    'div.flex',
                    { style: { flexWrap: 'wrap' } },
                    ...autorizados.map((d) =>
                      el('span.status.verde', { title: d.numero_documento }, d.tipo_documento)
                    )
                  )
                : el('span.status.gris', {}, t('pendiente'))
            )
          );
        })
      )
    )
  );
}

/** Tabla de los envíos del cliente, con la etapa en que va cada uno. */
function tablaEnvios(envios, t) {
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
          el('th', {}, t('seguimiento')),
          el('th', {}, t('naviera')),
          el('th', {}, t('ruta')),
          el('th', {}, t('salida')),
          el('th', {}, t('llegada')),
          el('th', {}, t('estado'))
        )
      ),
      el(
        'tbody',
        {},
        ...envios.map((e) =>
          el(
            'tr',
            {},
            el('td.mono.cell-main', {}, f.texto(e.numero_seguimiento)),
            el('td.small', {}, f.texto(e.transportadora)),
            el(
              'td.small',
              {},
              e.puerto_origen || e.puerto_destino
                ? `${f.texto(e.puerto_origen)} → ${f.texto(e.puerto_destino)}`
                : '—'
            ),
            el('td.small', {}, e.fecha_salida ? f.fecha(e.fecha_salida) : '—'),
            el('td.small', {}, e.fecha_llegada ? f.fecha(e.fecha_llegada) : '—'),
            el('td', {}, pill(e.estado))
          )
        )
      )
    )
  );
}

function documentos(operaciones, t) {
  const autorizados = operaciones.flatMap((x) =>
    (x.documentos || []).filter((d) => d.autorizado_cliente).map((d) => ({ ...d, contrato: x.numero_contrato }))
  );

  if (!autorizados.length) {
    return vacio(t('sinDocs'));
  }

  return el(
    'div',
    {},
    ...autorizados.map((d) =>
      el(
        'div.doc-item',
        {},
        el(
          'div',
          {},
          el('div.doc-main', {}, d.tipo_documento),
          el('div.doc-sub', {}, `${d.numero_documento} · ${t('contratoMin')} ${f.texto(d.contrato)} · ${f.fecha(d.fecha_emision)}`)
        ),
        el(
          'div.flex',
          {},
          pill(d.estado),
          el(
            'button.btn.btn-sm',
            {
              onclick: () =>
                modal({
                  titulo: d.tipo_documento,
                  cuerpo: el(
                    'div',
                    {},
                    el(
                      'dl',
                      {},
                      el('dt', {}, t('numero')), el('dd.mono', {}, d.numero_documento),
                      el('dt', {}, t('emitido')), el('dd', {}, f.fecha(d.fecha_emision)),
                      el('dt', {}, t('contrato')), el('dd.mono', {}, f.texto(d.contrato)),
                      el('dt', {}, t('estado')), el('dd', {}, pill(d.estado))
                    ),
                    el(
                      'p.small.muted.mt-2',
                      {},
                      'La descarga del archivo firmado se habilita cuando RiTech SAS ' +
                        'habilite el almacenamiento documental (S3 / Azure Blob).'
                    )
                  ),
                  pie: [el('button.btn.btn-primary', { onclick: () => document.querySelector('.modal-backdrop')?.remove() }, 'Entendido')],
                }),
            },
            icono('descargar'),
            t('ver')
          )
        )
      )
    )
  );
}
