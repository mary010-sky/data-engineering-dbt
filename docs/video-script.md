# Guion para grabación — 4 minutos 30 segundos

Presentadora: Marymar Danytza Calloticona Chambilla.

| Tiempo | Demostración |
| --- | --- |
| 0:00–0:25 | Presentarse con nombre completo. Objetivo: ingeniería de datos con dbt + DuckDB; publicación automatizada sin configurar AWS. |
| 0:25–1:00 | Abrir repositorio público. Mostrar arquitectura y CSV de entrada con 1.006 eventos y defectos intencionales. |
| 1:00–1:50 | Mostrar stg_order_events.sql: try_cast, validación de dimensiones, row_number y política de última versión. Abrir fct_orders y quarantine. |
| 1:50–2:30 | Mostrar tests/reconcile_events.sql y reconcile_revenue.sql. Explicar el cálculo independiente en centavos y el bloqueo de publicación si falla una prueba. |
| 2:30–3:10 | Abrir aplicación pública. Mostrar 1.000 órdenes aceptadas, 6 retenidos, motivos de cuarentena, ingresos por mercado y filtro mensual. Descargar un CSV. |
| 3:10–3:55 | Abrir ejecución exitosa de GitHub Actions: dbt build, exportación, documentación y deploy. Abrir documentación dbt y linaje. |
| 3:55–4:30 | Mostrar artículo en DEV.to. Explicar límites: datos sintéticos, batch, snapshot publicado y warehouse temporal en CI. Cerrar con enlaces en la descripción. |

Duración máxima requerida: cinco minutos. Marymar grabará, publicará el video y enviará los enlaces al grupo de Telegram. Verificar que el video sea público antes de añadir su URL al ZIP. No mostrar contraseñas ni notificaciones privadas.
