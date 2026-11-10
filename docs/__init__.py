"""Generadores de los entregables escritos del Sprint 2 de RiTech SAS.

Todo el contenido vive en `datos.py`: requisitos, UML, backlog, historias de
usuario, modelo de datos y el guion de la exposición. Los demás módulos leen de
ahí, así que cambiar una cifra o una frase y volver a correr

    python -m docs.generar_todo

actualiza el documento en PDF, el documento en Word, la presentación, el guion
en Word y el guion en PowerPoint, sin que se puedan desincronizar entre sí.

Módulos:

    datos.py                  todo el contenido; no se edita a mano mientras
                              `generar_guion_detallado` esté en uso
    generar_todo.py           corre todo en el orden correcto
    generar_guion_detallado.py rehace el guion detallado desde `datos.EXPOSICION`
    diagrama_er.py            diagrama entidad-relación
    diagramas.py              diagrama de casos de uso
    documento.py              documento en PDF (reportlab)
    word.py                   documento en Word (python-docx)
    presentacion.py           presentación (python-pptx)
    guion.py                  guion de exposición en Word
    guion_pptx.py             guion de exposición en PowerPoint

Comprobaciones:

    resumen_guion.py          reparto de tiempo y tamaño del guion
    verificar_entregables.py   busca en los archivos generados frases que ya no
                              aplican, como «58 endpoints» o «trece elementos»
    revisar_texto.py          busca fragmentos corruptos en la prosa de datos.py
    arreglar_escapes.py       convierte los `\\u00e1` literales que se cuelan al
                              editar el texto a su carácter real
"""
