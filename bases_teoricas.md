# Bases Teoricas del Generador de Melodias

Este documento define las reglas de teoria musical clasica que el sistema debe implementar. Sirve como referencia para validar que el algoritmo responde correctamente a la teoria.

---

## Tabla de Contenidos

1. [Jerarquia Estructural](#1-jerarquia-estructural)
2. [Sistema de Grados de la Escala](#2-sistema-de-grados-de-la-escala)
3. [Notas Estructurales vs Ornamentales](#3-notas-estructurales-vs-ornamentales)
4. [Intervalos Melodicos](#4-intervalos-melodicos)
5. [Conduccion de Voces](#5-conduccion-de-voces)
6. [Sistema de Cadencias](#6-sistema-de-cadencias)
7. [Progresiones Armonicas](#7-progresiones-armonicas)
8. [Metrica y Ritmo](#8-metrica-y-ritmo)
9. [Variaciones Motivicas](#9-variaciones-motivicas)
10. [Contrapunto](#10-contrapunto)
11. [Modos y Escalas](#11-modos-y-escalas)

---

## 1. Jerarquia Estructural

La melodia clasica se construye mediante una jerarquia de unidades formales, de menor a mayor:

### 1.1 El Motivo

Es la unidad minima con sentido musical. Caracteristicas:
- **Longitud**: 2-5 notas tipicamente
- **Componentes**: Perfil ritmico + intervalo caracteristico
- **Funcion**: Actua como "semilla" generadora de toda la pieza

El motivo es como una palabra en una oracion: tiene significado propio pero adquiere mayor sentido en contexto.

### 1.2 La Frase

Agrupacion de motivos que forma una idea musical completa pero que necesita respuesta.
- **Longitud tipica**: 4 compases
- **Estructura**: Motivo + desarrollo/respuesta del motivo
- **Analogia**: Como una oracion que termina en coma

### 1.3 El Periodo

Unidad completa formada por dos frases en relacion pregunta-respuesta:

| Componente | Nombre | Cadencia | Funcion |
|------------|--------|----------|---------|
| Primera frase | **Antecedente** | Semicadencia (V) | Pregunta, tension |
| Segunda frase | **Consecuente** | Cadencia autentica (V-I) | Respuesta, resolucion |

**Longitud tipica**: 8 compases (4 + 4)

### 1.4 Tipos de Periodo

- **Periodo paralelo**: Ambas frases comienzan con material melodico similar
- **Periodo contrastante**: Las frases comienzan con material diferente
- **Periodo doble**: 16 compases (dos periodos de 8)
- **Periodo compuesto**: Periodo formado por oraciones en lugar de frases simples

### 1.5 La Oracion (Sentence)

Estructura alternativa al periodo, de 8 compases:
- **Presentacion** (4 compases): Motivo basico + repeticion
- **Continuacion** (4 compases): Fragmentacion + aceleracion armonica + cadencia

---

## 2. Sistema de Grados de la Escala

No todos los grados de la escala tienen el mismo peso funcional.

### 2.1 Grados de Estabilidad (Triada Tonica)

| Grado | Nombre | Funcion |
|-------|--------|---------|
| **I** | Tonica | Maxima estabilidad, reposo absoluto |
| **III** | Mediante | Estabilidad, define modo (mayor/menor) |
| **V** | Dominante | Estabilidad relativa, soporte armonico |

**Regla**: Estos grados pueden ocupar tiempos fuertes y ser destino de saltos melodicos.

### 2.2 Grados de Tension (Notas de Tendencia)

| Grado | Nombre | Tendencia | Resolucion |
|-------|--------|-----------|------------|
| **VII** | Sensible | Atraccion magnetica hacia I | Resuelve **ascendiendo** a I |
| **IV** | Subdominante | Tension hacia III | Resuelve **descendiendo** a III |
| **II** | Supertonica | Tension hacia I o III | Resuelve por grado conjunto |
| **VI** | Superdominante | Tension leve | Resuelve a V o I |

**Regla critica**: La sensible (VII) DEBE resolver a la tonica (I) por semitono ascendente. Esta es la regla de conduccion de voces mas importante.

### 2.3 Funciones Armonicas

Los grados se agrupan en tres funciones:

| Funcion | Grados | Caracter |
|---------|--------|----------|
| **Tonica** | I, III, VI | Estabilidad, reposo |
| **Subdominante** | II, IV | Preparacion, movimiento |
| **Dominante** | V, VII | Tension, necesidad de resolucion |

---

## 3. Notas Estructurales vs Ornamentales

### 3.1 Notas del Acorde (Chord Tones)

Son las notas que pertenecen al acorde vigente:
- Ocupan **tiempos fuertes**
- Son destino de **saltos melodicos**
- Definen la **armonia implicita**

**Regla de oro**: Si la melodia salta (intervalo > 3a), ambas notas deben ser notas del acorde.

### 3.2 Notas de Paso (Passing Tones)

Conectan dos notas del acorde por grado conjunto:
- Movimiento **por grados conjuntos** (2as)
- Ubicacion en **tiempos debiles** (no acentuadas)
- Direccion: misma direccion de entrada y salida
- Pueden ser diatonicas o cromaticas

### 3.3 Bordaduras (Neighbor Tones)

Adornan una nota del acorde y regresan a ella:
- **Bordadura superior**: nota + paso arriba + regreso
- **Bordadura inferior**: nota + paso abajo + regreso
- Ubicacion tipica: tiempos debiles

### 3.4 Apoyaturas (Appoggiaturas)

Nota acentuada que no pertenece al acorde:
- Ubicacion: **tiempo fuerte** (acentuada)
- Aproximacion: por **salto**
- Resolucion: por **grado conjunto descendente**
- Efecto: tension expresiva ("suspiro" clasico)

### 3.5 Suspensiones (Suspensions)

Tres fases obligatorias:
1. **Preparacion**: nota del acorde en tiempo debil
2. **Suspension**: misma nota sostenida sobre nuevo acorde (tiempo fuerte)
3. **Resolucion**: descenso por grado conjunto a nota del nuevo acorde

Tipos comunes: 4-3, 7-6, 9-8, 2-1

### 3.6 Anticipaciones (Anticipations)

- Nota del siguiente acorde que aparece antes de tiempo
- Siempre **no acentuada**
- Valor ritmico **corto**

### 3.7 Escapadas (Escape Tones)

- Aproximacion por **grado conjunto**
- Resolucion por **salto en direccion opuesta**
- No acentuadas

### 3.8 Notas Pedal

- Nota sostenida (usualmente tonica o dominante)
- Mantiene mientras la armonia cambia encima
- Tipicamente en el bajo

---

## 4. Intervalos Melodicos

### 4.1 Clasificacion por Consonancia

**Consonancias perfectas**:
- Unisono (1:1)
- Octava (2:1)
- Quinta justa (3:2)
- Cuarta justa (4:3)

**Consonancias imperfectas**:
- Tercera mayor (5:4) y menor (6:5)
- Sexta mayor (5:3) y menor (8:5)

**Disonancias**:
- Segunda mayor y menor
- Septima mayor y menor
- Tritono (cuarta aumentada / quinta disminuida)

### 4.2 Reglas de Saltos Melodicos

| Regla | Descripcion |
|-------|-------------|
| **Limite de salto** | Maximo sexta en contexto normal |
| **Octava** | Solo permitida en climax o momentos especiales |
| **Recuperacion** | Salto > 3a debe compensarse con movimiento contrario |
| **Saltos consecutivos** | Evitar; si ocurren, deben sumar < octava y cambiar direccion |
| **Tritono** | Evitar como intervalo melodico directo |

### 4.3 Movimiento Melodico Ideal

- Predominio de **grados conjuntos** (movimiento por 2as)
- Saltos espaciados y compensados
- Linea melodica en forma de **arco** o **onda**
- Evitar monotonia (repeticion excesiva de notas)
- Evitar saltos repetidos en misma direccion

---

## 5. Conduccion de Voces

### 5.1 Principios Fundamentales

1. **Movimiento minimo**: Cada voz se mueve la menor distancia posible
2. **Notas comunes**: Mantener notas compartidas entre acordes
3. **Independencia**: Cada voz debe tener interes melodico propio

### 5.2 Movimientos Prohibidos

| Prohibicion | Descripcion |
|-------------|-------------|
| **Quintas paralelas** | Dos voces moviendose en 5as justas consecutivas |
| **Octavas paralelas** | Dos voces moviendose en 8as consecutivas |
| **Quintas directas** | Llegar a 5a justa por movimiento directo (ambas voces misma direccion) |
| **Octavas directas** | Llegar a 8a por movimiento directo |
| **Cruce de voces** | Una voz cruzando el registro de otra |

### 5.3 Resoluciones Obligatorias

| Nota | Resolucion |
|------|------------|
| Sensible (VII) | Asciende a tonica (I) |
| Septima del acorde | Desciende por grado conjunto |
| Cuarta del acorde (IV) | Desciende a tercera (III) |

---

## 6. Sistema de Cadencias

Las cadencias son puntuaciones musicales que articulan la forma.

### 6.1 Cadencia Autentica (V - I)

La mas conclusiva. Dos tipos:

**Cadencia Autentica Perfecta (PAC)**:
- Bajo: grado 5 a grado 1
- Soprano: termina en grado 1
- Ambos acordes en estado fundamental
- Maxima sensacion de cierre

**Cadencia Autentica Imperfecta (IAC)**:
- Cualquier variacion de la perfecta
- Soprano no en grado 1, o acordes invertidos
- Menos conclusiva

### 6.2 Semicadencia (Half Cadence)

- Termina en acorde de **dominante (V)**
- Sensacion de **pregunta** o pausa
- Usada al final del antecedente

### 6.3 Cadencia Plagal (IV - I)

- Subdominante a tonica
- Caracter **himnico** ("Amen")
- Menos tension que la autentica

### 6.4 Cadencia Rota/Enganyosa (V - vi)

- Dominante resuelve a **submediante** en lugar de tonica
- Efecto de **sorpresa**
- Prolonga la tension

### 6.5 Cadencia Frigia

- Tipo especial de semicadencia en modo menor
- Bajo desciende por semitono al V (iv6 - V)
- Caracter arcaico

---

## 7. Progresiones Armonicas

### 7.1 Circulo de Quintas Funcional

Movimiento natural de la armonia:
```
I -> IV -> vii -> iii -> vi -> ii -> V -> I
```

### 7.2 Progresiones Comunes

| Contexto | Progresion |
|----------|------------|
| Basica | I - IV - V - I |
| Extendida | I - vi - IV - V - I |
| Con ii | I - ii - V - I |
| Periodo 8 compases | I - I - IV - V - I - I - IV - I |

### 7.3 Reglas de Movimiento Armonico

1. **V resuelve a I** (movimiento mas fuerte)
2. **IV puede ir a V o I**
3. **ii prepara V** (pre-dominante)
4. **vi puede sustituir I** (tonica debil)
5. **Evitar V a IV** (retroceso funcional)

### 7.4 Acordes en Modo Menor

| Grado | Calidad | Nota |
|-------|---------|------|
| i | menor | tonica |
| ii° | disminuido | |
| III | mayor | relativo mayor |
| iv | menor | |
| V | **MAYOR** | practica comun: usar sensible |
| VI | mayor | |
| vii° | **disminuido** | sobre sensible elevada |

**Regla importante**: En modo menor, el V debe ser MAYOR (con sensible) para crear cadencia autentica efectiva.

---

## 8. Metrica y Ritmo

### 8.1 Jerarquia Metrica

| Nivel | Descripcion |
|-------|-------------|
| **Tiempo fuerte** | Primer pulso del compas, maxima importancia |
| **Tiempo semi-fuerte** | Pulso 3 en 4/4, importancia secundaria |
| **Tiempos debiles** | Pulsos intermedios |
| **Subdivisiones** | Partes del pulso, menor jerarquia |

### 8.2 Tipos de Inicio

| Tipo | Descripcion | Caracter |
|------|-------------|----------|
| **Tetico** | Comienza en tiempo fuerte | Estabilidad, afirmacion |
| **Anacrusico** | Comienza antes del tiempo fuerte | Impulso, direccion |
| **Acefalo** | Silencio en tiempo fuerte | Incertidumbre, sincopa |

### 8.3 Ritmo Armonico

Velocidad de cambio de acordes:
- **Lento** (1 acorde por compas): melodia mas activa ritmicamente
- **Rapido** (varios acordes por compas): melodia mas calmada

### 8.4 Metricas Compuestas

| Compas | Subdivision | Caracter |
|--------|-------------|----------|
| 6/8 | 2 grupos de 3 | Binario con pulso ternario |
| 9/8 | 3 grupos de 3 | Ternario con pulso ternario |
| 12/8 | 4 grupos de 3 | Cuaternario con pulso ternario |

**Regla**: En compases compuestos, el pulso es la negra con puntillo (3 corcheas), no la corchea.

### 8.5 Metricas Amalgama

Compases irregulares con subdivisiones asimetricas:

| Compas | Subdivisiones posibles |
|--------|------------------------|
| 5/8 | 2+3 o 3+2 |
| 7/8 | 2+2+3, 2+3+2, 3+2+2 |
| 11/8 | 3+3+3+2, 2+3+3+3, etc. |

---

## 9. Variaciones Motivicas

Tecnicas clasicas para desarrollar un motivo manteniendo su identidad.

### 9.1 Tipos de Variacion

| Variacion | Descripcion |
|-----------|-------------|
| **Repeticion** | Motivo identico |
| **Transposicion** | Motivo en otro grado de la escala |
| **Inversion** | Intervalos invertidos (sube->baja, baja->sube) |
| **Retrogradacion** | Motivo al reves (ultima nota primero) |
| **Aumentacion** | Duraciones duplicadas |
| **Disminucion** | Duraciones reducidas a mitad |
| **Secuencia** | Repeticion a diferentes alturas |

### 9.2 Principio de Economia de Materiales

La coherencia se logra mediante:
- Reutilizacion del motivo inicial
- Variaciones reconocibles
- Balance entre repeticion (familiaridad) y variacion (interes)

**Regla**: Evitar introducir material completamente nuevo. Desarrollar lo existente.

---

## 10. Contrapunto

Reglas para melodias que se combinan polifonicamente.

### 10.1 Especies de Contrapunto (Fux)

| Especie | Descripcion |
|---------|-------------|
| **Primera** | Nota contra nota |
| **Segunda** | Dos notas contra una |
| **Tercera** | Cuatro notas contra una |
| **Cuarta** | Ligaduras y sincopas |
| **Quinta** | Contrapunto florido (combinacion) |

### 10.2 Reglas Fundamentales

1. Comenzar y terminar en consonancia perfecta (unisono, 5a, 8a)
2. Predominio de movimiento contrario u oblicuo
3. Evitar mas de 3 terceras o sextas paralelas
4. La nota final debe aproximarse por grado conjunto
5. En modo menor, elevar la sensible en la cadencia

---

## 11. Modos y Escalas

### 11.1 Modos Diatonicos (de escala mayor)

| Modo | Grados alterados | Caracter |
|------|------------------|----------|
| Jonico (Mayor) | ninguno | Brillante, alegre |
| Dorico | b3, b7 | Modal, jazzy |
| Frigio | b2, b3, b6, b7 | Espanol, oscuro |
| Lidio | #4 | Etereo, sonador |
| Mixolidio | b7 | Blues, rock |
| Eolico (Menor) | b3, b6, b7 | Triste, melancolico |
| Locrio | b2, b3, b5, b6, b7 | Inestable, disonante |

### 11.2 Escalas Menores

| Escala | Caracteristica |
|--------|----------------|
| **Menor natural** | = Eolico |
| **Menor armonica** | 7mo grado elevado (sensible) |
| **Menor melodica** | 6to y 7mo elevados (ascendente) |

### 11.3 Modos Derivados

**De menor armonica**: Locrio nat6, Jonico aug5, Dorico #4, Frigio dominante, Lidio #2, Superlocrio

**De menor melodica**: Dorico b2, Lidio aumentado, Lidio dominante, Mixolidio b6, Locrio nat2, Alterado

---

## Referencias

- [Counterpoint - Wikipedia](https://en.wikipedia.org/wiki/Counterpoint)
- [Voice Leading - Wikipedia](https://en.wikipedia.org/wiki/Voice_leading)
- [Cadence - Wikipedia](https://en.wikipedia.org/wiki/Cadence)
- [Open Music Theory - Species Counterpoint](https://viva.pressbooks.pub/openmusictheory/chapter/species-counterpoint/)
- [Open Music Theory - Tendency Tones](https://viva.pressbooks.pub/openmusictheorycopy/chapter/tendency-tones-and-functional-harmonic-dissonances/)
- [Open Music Theory - Periods](https://elliotthauser.com/openmusictheory/period.html)
- [Fundamentals, Function, and Form - Sentences and Periods](https://milnepublishing.geneseo.edu/fundamentals-function-form/chapter/35-sentences-and-periods/)
- [Fundamentals, Function, and Form - Nonharmonic Tones](https://milnepublishing.geneseo.edu/fundamentals-function-form/chapter/15-nonharmonic-tones/)
- [Music Theory Academy - Cadences](https://www.musictheoryacademy.com/how-to-read-sheet-music/cadences/)
- [Introduction to Non-Chord Tones](https://musictheory.pugetsound.edu/mt21c/NonChordTonesIntroduction.html)

---

*Este documento es la referencia autoritativa para validar la implementacion del algoritmo. Cualquier discrepancia entre el comportamiento del sistema y estas reglas debe considerarse un bug a corregir.*
