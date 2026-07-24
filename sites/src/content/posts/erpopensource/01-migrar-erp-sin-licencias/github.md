---
title: "Por qué el modelo de licencia por usuario encarece cada año que pasa"
date: "2026-07-24"
project: "erpopensource"
---

Un ERP con licencia por usuario parece barato el primer año, casi siempre
más barato que la alternativa de código abierto con implantación a
medida. El problema aparece en el año tres o cuatro, cuando la plantilla
ha crecido, el proveedor ha subido precios de renovación y cada usuario
nuevo cuesta lo mismo que el primero, sin descuento por volumen real.

La causa técnica de fondo es sencilla: el software propietario cobra por
"asiento", una licencia atada a una persona o a un puesto concreto.
Cuantas más personas necesiten tocar el ERP —comercial, almacén,
administración, gerencia—, más asientos hacen falta, y el coste crece de
forma lineal con la plantilla, no con el uso real del sistema. Un
almacenero que consulta stock cinco minutos al día paga la misma
licencia que un contable que vive dentro del ERP ocho horas.

**Tres cosas pasan cuando el coste crece así, año tras año:**

- Las empresas empiezan a **compartir usuarios** entre varios empleados
  para ahorrar licencias, lo que rompe la trazabilidad de quién hizo cada
  cambio en el sistema.
- Se **retrasa dar acceso** a gente que lo necesitaría —un comercial
  nuevo, un becario de almacén— porque cada alta cuesta dinero de forma
  inmediata.
- El departamento de IT empieza a **evitar** activar módulos adicionales
  del mismo proveedor, no porque no sirvan, sino por miedo a que suban el
  precio del contrato entero al renovar.

![Persona trabajando frente a un ordenador portátil con código en pantalla](https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1200&q=80)

Tryton, como proyecto de código abierto bajo licencia GPL-3.0, rompe esa
ecuación porque no cobra por asiento: el software en sí no tiene coste de
licencia, sea cual sea el número de usuarios que lo usen a diario. Lo que
se paga es implantación, adaptación a tu sector y soporte, un gasto que
sí escala con el trabajo real hecho, no con cuántas personas abren la
aplicación.

Eso no significa que sea gratis migrar. Adaptar el ERP a tu contabilidad,
tu normativa de facturación electrónica o tu operativa de logística
requiere trabajo de implantación, igual que con cualquier sistema
propietario. La diferencia está en qué pagas: en un modelo por asiento,
pagas cada persona que toca el sistema, para siempre. En un modelo de
software libre con implantación a medida, pagas el trabajo de adaptación
una vez, y añadir usuarios después no dispara la factura.

Repositorio y documentación técnica del proyecto en
[opensourceerp.org](https://opensourceerp.org).
