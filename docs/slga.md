# Sistema Local de Gestión Ambiental (SLGA)

Este proyecto no solo monitorea datos técnicos (aire, residuos, agua, ruido,
áreas verdes, incendios): también modela el **Sistema Local de Gestión
Ambiental** que toda municipalidad peruana debe operar, para que el mismo
repositorio sirva como base de gestión institucional y no solo como dashboard de
sensores.

Lima Metropolitana tiene **44 gobiernos locales independientes** (1 municipalidad
provincial + 43 distritales), cada uno con su propia CAM y sus propios
instrumentos de gestión — por eso cada fila de las tablas de este módulo lleva un
`distrito_id`. Ver [`docs/distritos.md`](distritos.md) para el detalle de cómo se
modela y se resuelve el distrito de cada dato.

## Marco legal

- **Ley N° 28245**, Ley Marco del Sistema Nacional de Gestión Ambiental (crea las
  Comisiones Ambientales Municipales — Art. 25).
- **D.S. N° 008-2005-PCM**, Reglamento de la Ley N° 28245 —
  https://sinia.minam.gob.pe/normas/reglamento-ley-ndeg-28245-ley-marco-sistema-nacional-gestion-ambiental
- **Ley N° 27972**, Ley Orgánica de Municipalidades (funciones ambientales de
  gobiernos locales).
- **RM N° 101-2021-MINAM**, "Guía para el funcionamiento de los Sistemas Locales de
  Gestión Ambiental (SLGA)" —
  https://cdn.www.gob.pe/uploads/document/file/1957133/Anexo%20RM%20101-2021-MINAM%20-%20Guia%20SLGA%20version%2003.06.2021.pdf.pdf
- **Reconocimiento GALS** (Gestión Ambiental Local Sostenible) —
  https://www.minam.gob.pe/gals/

## Componentes del SLGA y cómo este proyecto los modela

| Componente oficial | Qué es | Tabla / módulo en este repo |
|---|---|---|
| Política Ambiental Local (PAL) | Lineamientos generales de gestión ambiental del municipio | `instrumentos_gestion_ambiental` (`tipo='politica_ambiental_local'`) |
| Diagnóstico Ambiental Local (DAL) | Línea base de la situación ambiental del territorio | `instrumentos_gestion_ambiental` (`tipo='diagnostico_ambiental_local'`) |
| Plan de Acción Ambiental Local (PAAL) | Plan de mediano plazo derivado del DAL | `instrumentos_gestion_ambiental` (`tipo='plan_accion_ambiental_local'`) |
| Agenda Ambiental Local (AAL) | Plan operativo de corto plazo (bianual) | `instrumentos_gestion_ambiental` (`tipo='agenda_ambiental_local'`) |
| PIGARS / plan de residuos sólidos | Plan de gestión de residuos sólidos municipales | `instrumentos_gestion_ambiental` (`tipo='pigars'`) + datos de `residuos_distrito` |
| Comisión Ambiental Municipal (CAM) | Instancia de concertación público-privada-sociedad civil (Art. 25, Ley 28245) | `cam_integrantes`, `cam_sesiones` |
| PLANEFA | Plan Anual de Evaluación y Fiscalización Ambiental | `planefa_acciones` |
| Sistema de Información Ambiental Local (SIAL) | Red de información ambiental local, parte del SINIA | Este proyecto en su conjunto — pensado como un SIAL ligero y open source, con énfasis en monitoreo casi en tiempo real que los portales SIAL oficiales normalmente no cubren |
| Certificación GALS | Reconocimiento MINAM en 2 niveles (GALS I inicial, GALS II intermedio) sobre 3 dimensiones: calidad ambiental, institucionalidad y ciudadanía, aprovechamiento sostenible de RRNN en cambio climático | `indicadores_gals` |

## Por qué esta parte del sistema es de carga manual

A diferencia de aire (OpenAQ) o residuos (PNDA), no existe una API pública para la
composición de una CAM, el estado de sus instrumentos de gestión o sus acciones
PLANEFA — son decisiones y actas administrativas propias de cada gobierno local.
Por eso `src/slga/cli.py` es una CLI de carga manual en vez de un ingestor
automático, y por eso conviene mantenerla simple: el valor no está en automatizar
algo que no tiene fuente automatizable, sino en tener un lugar único, versionado y
con dashboard, donde esa información viva junto a los datos técnicos.

## Cargar datos de tu distrito

1. Corre `python -m src.slga.cli distritos` para ver los 44 nombres válidos
   (43 distritos + "Lima Metropolitana" para el ámbito provincial).
2. (Opcional, para probar el dashboard antes de tener datos reales) carga el set
   de ejemplo: `python -m src.slga.cli seed-ejemplo` — cubre 3 gobiernos locales
   a modo de muestra (Lima Metropolitana, San Isidro, San Juan de Lurigancho).
3. Reemplaza los datos de ejemplo por los reales de cada distrito con los
   comandos `*-add` de `src/slga/cli.py`, pasando siempre `--distrito "Nombre"`
   (ver el docstring del archivo para el uso completo de cada subcomando).
4. Abre el dashboard **"Gestión Ambiental Municipal - SLGA"** en Grafana — tiene
   un filtro de distrito arriba para ver uno, varios, o los 44 a la vez.

## Adaptar esto a otra ciudad (fuera de Lima)

Este proyecto pasó de modelar una sola municipalidad genérica a modelar
específicamente los 44 gobiernos locales de Lima Metropolitana (tabla
`distritos`, sembrada en `sql/schema.sql`). Para otra ciudad/provincia, reemplaza
el seed de `distritos` por la lista de gobiernos locales de esa provincia — el
resto del modelo (instrumentos, CAM, PLANEFA, GALS, indicadores por distrito)
funciona igual, siempre que exista una tabla `distritos` con al menos `id`,
`nombre` y `nivel`.
