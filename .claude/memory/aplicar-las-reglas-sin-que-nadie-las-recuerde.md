---
name: aplicar-las-reglas-sin-que-nadie-las-recuerde
description: En My_novel_story la señal de calidad es aplicar las reglas del proyecto sin que nadie las recuerde en ese momento; eso distingue una disciplina interiorizada de una lista que alguien tiene que repasar.
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T17:09:20.706Z
---

# Aplicar las reglas sin que nadie las recuerde

Al catalogar `MF-27` —un artefacto producido por una versión del código anterior a la del
árbol— resultó que otra sesión ya había construido el arreglo, y que dentro llevaba tres
decisiones que nadie le había pedido en ese momento:

1. **La versión de creación de la base no se pisa**, porque la pregunta útil es *con qué
   código se escribió lo que hay aquí* y no *quién abrió la base el último*.
2. **Lo que no se puede determinar se dice** (`sin_determinar`), en vez de poner un valor
   plausible.
3. **Una base sin marca de procedencia no es conforme**, porque leer esa ausencia como
   *coincide* sería el mismo silencio que el arreglo viene a quitar.

Las tres son reglas que el proyecto ya tenía escritas —ausente no es cero, un dato que falta
se declara, una ausencia no es un verde— aplicadas a un problema nuevo sin que nadie las
citara. El usuario lo señaló como lo que importa:

> *"Son reglas del proyecto aplicadas sin que nadie se las recordara. Es lo que distingue una
> disciplina interiorizada de una lista que alguien tiene que recordar."*

Para mí eso significa dos cosas concretas en este repositorio:

- **Al escribir código o documentos aquí, las reglas del proyecto se aplican de oficio**, sin
  esperar a que el usuario las invoque en esa tarea. Si estoy escribiendo una consulta que
  puede devolver vacío, la pregunta *«¿se distingue de no consta?»* me la hago yo. Si estoy
  guardando un dato derivado, *«¿se puede saber de dónde salió?»* también.
- **Al revisar trabajo ajeno, eso es lo que hay que reconocer y decir en voz alta**, porque es
  la señal de que las reglas se han interiorizado y no de que alguien repasó una lista. Vale
  más que el arreglo en sí.
