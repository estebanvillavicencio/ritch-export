from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = Path(__file__).parent / "salida"
OUT.mkdir(exist_ok=True)
COFFEE = "3B2A20"
GREEN = "496B4A"
GOLD = "B78A42"
CREAM = "F5F1E8"

def shade(cell, color):
    pr = cell._tc.get_or_add_tcPr()
    el = OxmlElement("w:shd")
    el.set(qn("w:fill"), color)
    pr.append(el)

def setup(doc, sprint, subtitle):
    sec = doc.sections[0]
    sec.top_margin = Inches(.7); sec.bottom_margin = Inches(.65)
    sec.left_margin = Inches(.8); sec.right_margin = Inches(.8)
    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)
    styles["Normal"].font.color.rgb = RGBColor.from_string("302820")
    for name, size, color in [("Heading 1", 17, COFFEE), ("Heading 2", 12, GREEN)]:
        styles[name].font.name = "Georgia" if name == "Heading 1" else "Calibri"
        styles[name].font.size = Pt(size); styles[name].font.bold = True
        styles[name].font.color.rgb = RGBColor.from_string(color)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("RITECH SAS  |  GESTIÓN DE EXPORTACIONES")
    r.bold = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string(GREEN)
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Sprint {sprint}\n{subtitle}")
    r.font.name = "Georgia"; r.font.size = Pt(25); r.font.bold = True
    r.font.color.rgb = RGBColor.from_string(COFFEE)
    p = doc.add_paragraph("Sistema de Gestión de Exportación de Café y Cacao a la Unión Europea")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:
        r.italic = True; r.font.color.rgb = RGBColor.from_string("71665A")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Metodología Scrum  •  Duración planificada: 2 semanas  •  Equipo RiTech SAS")
    r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string("71665A")
    doc.add_paragraph()

def para(doc, text):
    p=doc.add_paragraph(text); p.paragraph_format.space_after=Pt(6); return p

def bullets(doc, items):
    for item in items:
        p=doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after=Pt(3); p.add_run(item)

def table(doc, headers, rows):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.style="Table Grid"
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=h; shade(c,COFFEE)
        for r in c.paragraphs[0].runs:
            r.bold=True; r.font.color.rgb=RGBColor(255,255,255); r.font.size=Pt(9)
    for idx,row in enumerate(rows):
        cells=t.add_row().cells
        for i,val in enumerate(row):
            cells[i].text=val; cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if idx%2==1: shade(cells[i],CREAM)
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after=Pt(2)
                for r in p.runs: r.font.size=Pt(9)
    doc.add_paragraph()

def footer(doc, sprint):
    f=doc.sections[0].footer.paragraphs[0]
    f.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=f.add_run(f"RiTech SAS  •  Documento de seguimiento Scrum  •  Sprint {sprint}")
    r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string("71665A")

def sprint3():
    d=Document(); setup(d,3,"Finanzas y control de la operación")
    d.add_heading("Resumen del sprint",1)
    para(d,"En este sprint se amplió la plataforma operativa con herramientas para controlar pagos y cartera, comunicar eventos relevantes y consultar el historial de acciones. El resultado conecta la operación comercial y logística con controles financieros y de seguridad.")
    d.add_heading("Objetivo",1)
    para(d,"Dar seguimiento a los compromisos de pago de las exportaciones y mantener informados a los usuarios responsables, dejando evidencia de las acciones críticas realizadas en el sistema.")
    d.add_heading("Alcance y trabajo realizado",1)
    table(d,["Historia","Funcionalidad entregada","Resultado para el usuario"],[
        ["HU-14 · Financiero y cartera","Registro de anticipos, pagos parciales y pagos; cálculo de saldo pendiente; seguimiento de cartas de crédito y resumen financiero.","El equipo consulta lo facturado, lo pagado y lo que falta por cobrar por exportación."],
        ["HU-16 · Notificaciones","Bandeja de avisos para vencimientos y cambios relevantes, incluidos estados de pedidos y pagos. Los avisos evitan duplicados mediante una clave única.","Cada responsable puede revisar alertas recientes y marcar su seguimiento."],
        ["HU-21 · Auditoría","Registro de acciones críticas con usuario, acción, entidad afectada, ruta y dirección IP; consulta restringida a administración.","La empresa puede rastrear cambios relevantes y revisar quién los realizó."],
    ])
    d.add_heading("Criterios de aceptación",1)
    bullets(d,["Los pagos parciales actualizan el saldo pendiente y un pago anulado deja de contar en el cálculo.","Los usuarios autorizados pueden consultar y registrar movimientos financieros; las acciones quedan auditadas.","Las notificaciones derivadas de un mismo evento no se duplican.","El administrador puede filtrar el historial de auditoría y revisar el detalle de cada evento."])
    d.add_heading("Revisión del sprint",1)
    para(d,"La demostración recorre el resumen de cartera, el registro de un pago parcial, la aparición de una notificación y la consulta del evento correspondiente en auditoría. El alcance se considera entregado cuando esos flujos están disponibles desde la aplicación y respetan los permisos por rol.")
    d.add_heading("Resultado y continuidad",1)
    para(d,"El Sprint 3 deja una base de seguimiento financiero y trazabilidad de acciones. El siguiente sprint completa capacidades transversales: conversión entre monedas, conexión con servicios externos, respaldo de información y experiencia de consulta para clientes europeos.")
    d.add_heading("Equipo y responsabilidades",1)
    para(d,"El equipo RiTech SAS trabaja de forma colaborativa. Las responsabilidades individuales se asignan según los roles del proyecto (administración, comercial, logística y calidad) y pueden ajustarse al tablero del curso.")
    footer(d,3); d.save(OUT/"Documento_Sprint3_RiTech.docx")

def sprint4():
    d=Document(); setup(d,4,"Integración y cierre del producto")
    d.add_heading("Resumen del sprint",1)
    para(d,"El Sprint 4 completa el sistema de gestión de exportaciones con soporte multimoneda, registro de integraciones y copias de seguridad verificables. También consolida el portal de consulta del cliente europeo y la integración de los módulos desarrollados en los sprints anteriores.")
    d.add_heading("Objetivo",1)
    para(d,"Entregar una solución integrada para administrar el recorrido de café y cacao desde lotes y calidad hasta pedidos, pagos y seguimiento del envío, con consulta segura para clientes y herramientas básicas de continuidad operativa.")
    d.add_heading("Alcance y trabajo realizado",1)
    table(d,["Historia","Funcionalidad entregada","Resultado para el usuario"],[
        ["HU-19 · Multimoneda","Registro y consulta de tasas de cambio, conversión de valores y presentación de ingresos por moneda. Si el proveedor externo no responde, se utiliza una tasa local de respaldo.","El equipo puede revisar valores en distintas monedas y mantener la operación disponible sin conexión al proveedor."],
        ["HU-20 · Integraciones","Registro del estado e historial de intentos de servicios de correo, seguimiento de envíos y actualización de tasas; los fallos quedan identificados.","Administración puede conocer cuándo se intentó una integración y si se completó o recurrió al modo local."],
        ["HU-22 · Copias de seguridad","Creación manual y automática de instantáneas JSON, metadatos, tamaño y huella SHA-256; verificación y descarga restringidas al administrador.","La empresa puede comprobar la integridad de una copia y conservar un archivo portable de los datos."],
        ["HU-10 · Portal del cliente","Consulta de pedidos y envíos propios, con aislamiento de datos por empresa aplicado en el servidor.","El comprador europeo revisa el estado de sus exportaciones sin acceder a información de otros clientes."],
    ])
    d.add_heading("Criterios de aceptación",1)
    bullets(d,["La conversión informa la moneda, tasa, fuente y fecha; ante una falla del proveedor, queda registrado el uso de tasas locales.","Los intentos de integración y sus resultados se consultan en la bitácora.","El administrador puede crear, listar, descargar y verificar respaldos; una modificación del archivo se detecta mediante su huella.","El cliente solo consulta pedidos y envíos asociados a su empresa, incluso si modifica parámetros de la solicitud.","Los módulos operativos, financieros y de consulta funcionan como una aplicación integrada con permisos por rol."])
    d.add_heading("Revisión final del producto",1)
    para(d,"La revisión final muestra el inicio de sesión y los permisos por perfil; el registro de productores, fincas y lotes; los controles de calidad y certificación; la creación de pedidos y el seguimiento logístico; la cartera y notificaciones; auditoría, multimoneda, integraciones, respaldos y el portal del comprador. La documentación del proyecto describe 90 pruebas automatizadas para los flujos de los sprints y los controles de acceso.")
    d.add_heading("Resultado del Sprint 4",1)
    para(d,"Al cierre de este sprint queda construido el sistema RiTech para gestionar exportaciones de café y cacao a la Unión Europea, desde la trazabilidad del lote hasta el seguimiento del pedido y su estado financiero. El producto incluye interfaz web, API, persistencia de datos, roles, portal externo, alertas, auditoría y herramientas de continuidad.")
    d.add_heading("Cierre y entregables",1)
    bullets(d,["Aplicación web con módulos comerciales, logísticos, de calidad, financieros y administrativos.","API y base de datos con esquemas para SQLite, PostgreSQL y MySQL.","Portal del cliente con separación de información por empresa.","Documentación de instalación, operación y publicación, junto con el código fuente y los entregables del proyecto."])
    para(d,"El producto queda listo para demostración académica. La publicación en un entorno productivo requiere configurar las credenciales y servicios del entorno donde se despliegue.")
    d.add_heading("Equipo y responsabilidades",1)
    para(d,"El equipo RiTech SAS realiza la integración final, revisa los flujos de usuario y presenta el producto completo. Los responsables concretos se pueden completar conforme a la asignación del tablero del curso.")
    footer(d,4); d.save(OUT/"Documento_Sprint4_RiTech.docx")

if __name__=="__main__":
    sprint3(); sprint4()
