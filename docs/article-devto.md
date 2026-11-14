---
title: "Ingeniería de datos con dbt y DuckDB: de CSV crudos a un producto de datos público"
published: true
tags: dataengineering, dbt, python, devops
---

**Autora: Marymar Danytza Calloticona Chambilla**

En este proyecto construí **Data Foundry**, una solución de ingeniería de datos por lotes que convierte eventos de ventas en tablas confiables y resultados públicos. Utilicé dbt para organizar las transformaciones y las pruebas, DuckDB como almacén local y GitHub Actions para ejecutar el proceso y desplegar sus resultados en GitHub Pages. No configuré servicios ni una cuenta AWS.

Mi objetivo fue demostrar algo más que una consulta sobre un CSV: ingestión reproducible, reglas de calidad explícitas, deduplicación, trazabilidad, pruebas y entrega automatizada de un producto de datos.

## 1. El problema: los datos llegan con defectos

El generador produce **1.006 eventos sintéticos**, junto con dimensiones de clientes y productos. Hay 1.000 órdenes únicas válidas, una versión repetida de una orden y cinco eventos con problemas intencionales: una fecha imposible de interpretar, una cantidad negativa, un precio vacío, un cliente inexistente y un producto inexistente.

Los datos no representan personas ni ventas reales. Introducir defectos conocidos permite demostrar qué hace el pipeline con ellos. No basta con borrar las filas problemáticas: quiero saber cuántas llegaron, cuántas se aceptaron y por qué se retuvo cada una.

## 2. Arquitectura: bronze, silver y gold

```text
CSV sintéticos + dimensiones
        ↓ dbt seed
BRONZE: raw_orders, customers, products
        ↓ tipado + validación + ranking de versiones
STAGING: stg_order_events
        ├── SILVER: fct_orders
        └── AUDITORÍA: quarantine
                  ↓
GOLD: daily_sales, market_sales
        ↓ pruebas dbt + conciliación Python
JSON / CSV / documentación dbt
        ↓ GitHub Actions
GitHub Pages: producto de datos público
```

DuckDB se ejecuta durante la construcción del pipeline. El sitio publicado sirve un snapshot de los resultados: no ofrece una base compartida ni ejecuta dbt en el navegador.

## 3. Ingesta reproducible con seeds

El script `scripts/generate_data.py` genera los mismos archivos en cada ejecución. `dbt seed` carga esos CSV como tablas. Las dimensiones pequeñas funcionan bien como seeds en un laboratorio; en producción utilizaría un proceso de ingesta y fuentes apropiadas para el origen real de los datos.

La [documentación de dbt seed](https://docs.getdbt.com/reference/commands/seed) explica este mecanismo de carga. En el proyecto fijo los campos originales de la orden como texto para que el staging pueda identificar los errores de conversión de manera controlada.

## 4. Transformar sin ocultar los errores

El modelo `stg_order_events` elimina espacios y usa `try_cast` para interpretar fechas, cantidades y precios. Una conversión inválida devuelve un valor nulo, que la regla de calidad clasifica con un motivo.

```sql
select
  trim(order_id) as order_id,
  try_cast(order_date as date) as order_date,
  try_cast(quantity as integer) as quantity,
  try_cast(unit_price as decimal(12,2)) as unit_price
from {{ ref('raw_orders') }}
```

También verifica las claves contra las dimensiones. Los registros reciben estados como `invalid_date`, `invalid_quantity`, `invalid_price`, `unknown_customer` o `unknown_product`.

Para las versiones de una orden, la política es que el mayor `event_id` gana:

```sql
row_number() over (
  partition by order_id
  order by event_id desc
) as event_rank
```

Si la última versión es inválida, se retiene en cuarentena y no se recupera silenciosamente una versión anterior. En este ejemplo los identificadores de evento son únicos; en un origen real también necesitaría definir cómo resolver empates y eventos fuera de orden.

## 5. Conservar una salida auditable

`fct_orders` contiene solo la última versión aceptada de cada orden. Calcula ingresos con decimales y agrega el mercado y la categoría desde las dimensiones.

`quarantine` conserva los eventos inválidos y las versiones anteriores. Una versión reemplazada se identifica como `superseded_event`, que se distingue de un error de calidad. Así puedo reconciliar el volumen:

```text
1.006 eventos = 1.000 órdenes aceptadas + 6 eventos retenidos
6 retenidos = 5 inválidos + 1 versión reemplazada
```

Las tablas gold `daily_sales` y `market_sales` resumen órdenes, unidades e ingresos. USD es una unidad común para el ejemplo; no realizo conversiones monetarias.

## 6. Las pruebas forman parte de la construcción

Las pruebas de dbt verifican claves únicas y no nulas, referencias a dimensiones, estados permitidos y medidas válidas. Dos pruebas SQL adicionales comprueban que ningún evento desaparezca y que los ingresos de las tablas gold concilien con la tabla silver.

Una prueba singular de dbt devuelve las filas que violan la regla. Si devuelve una fila, falla:

```sql
select 'unaccounted_events' as failure
where (select count(*) from {{ ref('raw_orders') }}) !=
      (select count(*) from {{ ref('fct_orders') }}) +
      (select count(*) from {{ ref('quarantine') }})
```

Además, Python vuelve a leer los CSV, aplica la política documentada y calcula el ingreso esperado de forma independiente en centavos. Lo compara con la suma decimal de DuckDB. Esto ayuda a evitar que dos tablas concilien entre sí aunque ambas compartan un mismo error de transformación.

`scripts/export_site.py` solo exporta cuando todas las pruebas registradas en `run_results.json` pasan y la conciliación independiente coincide. La evidencia queda en `evidence/pipeline-validation.json`.

En la ejecución local pasaron las **26 pruebas de datos** y los 34 recursos procesados por `dbt build`. Las 1.000 órdenes aceptadas sumaron **USD 154.075,00**, iguales a los **15.407.500 centavos** calculados de forma independiente. Los seis eventos retenidos quedaron disponibles para auditoría. Estos importes pertenecen al conjunto sintético del laboratorio.

## 7. Linaje y documentación como resultados del pipeline

Cada `ref()` declara una dependencia entre modelos. dbt usa esas referencias para construir el grafo y ejecutar los recursos en el orden correcto. Después, `dbt docs generate` crea la documentación de las tablas, sus columnas y dependencias.

Publico esa documentación junto con un pequeño dashboard y archivos CSV/JSON. El dashboard permite revisar volúmenes, ingresos por mercado, motivos de cuarentena y resultados por mes. Los datos mostrados provienen de una ejecución real del pipeline, no de indicadores escritos a mano en el HTML.

## 8. Automatizar ejecución y publicación

El workflow se activa con un push a `main` o una ejecución manual. Sus pasos son:

1. Instalar el entorno Python con versiones registradas.
2. Generar los datos e ingresar los seeds.
3. Ejecutar `dbt build`, que procesa recursos y pruebas según el grafo.
4. Conciliar los ingresos y exportar las salidas públicas.
5. Generar y empaquetar la documentación de dbt.
6. Guardar artefactos de evidencia y desplegar el sitio en GitHub Pages.

El job de despliegue depende de que termine correctamente el pipeline. Una prueba fallida impide publicar la nueva versión. GitHub Pages se configura con la fuente **GitHub Actions**; el workflow utiliza un token temporal y no necesita una clave de otro proveedor de nube.

El repositorio incluye el código y la configuración para reproducir el proceso. La [referencia de dbt build](https://docs.getdbt.com/reference/commands/build) y la [guía de workflows de Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) describen los mecanismos utilizados.

## 9. Límites y siguientes pasos

Esta solución muestra ingeniería de datos por lotes a pequeña escala. No implementa streaming, CDC, cargas incrementales ni un almacén persistente en la nube. El archivo DuckDB se reconstruye en el runner y el sitio sirve sus resultados exportados.

Para evolucionarla, incorporaría una fuente externa, reglas de calidad vinculadas con el negocio y una estrategia de persistencia. Mantendría las comprobaciones de conservación de eventos y conciliación de ingresos para detectar regresiones.

**Autora: Marymar Danytza Calloticona Chambilla.**

- [Repositorio público con modelos, pruebas y automatización](https://github.com/mary010-sky/data-engineering-dbt)
- [Producto de datos público](https://mary010-sky.github.io/data-engineering-dbt/)
- [Documentación de dbt y linaje](https://mary010-sky.github.io/data-engineering-dbt/dbt/)
- [Ejecución automatizada exitosa](https://github.com/mary010-sky/data-engineering-dbt/actions/runs/43623819473)

La ejecución en GitHub Actions terminó correctamente: el pipeline y el despliegue pasaron. La aplicación pública mostró las 26 pruebas correctas, 1.000 órdenes aceptadas y USD 154.075,00 de ingreso validado. El filtro de febrero mostró 28 fechas del snapshot publicado.

Este artículo y el código se prepararon con asistencia de IA y comprobaciones de ejecución.
