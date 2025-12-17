# 🎼 Generador de Melodías Clásicas - Protocolo "Symmetry & Logic"

Implementación computacional completa de los principios de composición melódica de la teoría musical clásica, con soporte para métricas regulares y amalgama, 21 modos musicales, y dos métodos de generación: **Tradicional** (cohesión rítmica) y **Jerárquico** (jerarquía formal auténtica).

---

## 📑 Tabla de Contenidos

1. [Inicio Rápido](#-inicio-rápido)
2. [Características Principales](#-características-principales)
3. [Instalación](#-instalación)
4. [Uso](#-uso)
   - [Modo Interactivo](#modo-interactivo-recomendado)
   - [Modo Programático](#modo-programático)
5. [Modos Musicales (21 Modos)](#-modos-musicales-21-modos)
6. [Dos Métodos de Generación](#-dos-métodos-de-generación)
7. [Parámetros de Configuración](#-parámetros-de-configuración)
8. [Teoría Musical Implementada](#-teoría-musical-implementada)
9. [Arquitectura del Código](#-arquitectura-del-código)
10. [Guía para Desarrolladores](#-guía-para-desarrolladores)
11. [Ejemplos Avanzados](#-ejemplos-avanzados)
12. [Limitaciones y Mejoras Futuras](#-limitaciones-y-mejoras-futuras)

---

## 🚀 Inicio Rápido

### Instalación (Una sola vez)

```bash
pip install abjad music21
```

### Generar tu Primera Melodía

```bash
python3 main.py
```

El programa te guiará paso a paso con un menú interactivo de 14 preguntas.

### Probar en LilyPond/Frescobaldi

1. Ejecuta: `python3 main.py`
2. Copia la salida (desde `\score {` hasta el último `}`)
3. Abre Frescobaldi y pega el código
4. Compila (Ctrl+M)
5. ¡Disfruta tu melodía en PDF + MIDI!

---

## ✨ Características Principales

### 1. Jerarquía Estructural Completa
- **Motivo**: Célula rítmico-melódica fundamental (2-5 notas)
- **Semifrase**: Agrupación de motivos
- **Antecedente/Consecuente**: Sistema de pregunta-respuesta
- **Período**: Unidad completa con cierre cadencial

### 2. Sistema Tonal/Modal Avanzado ⭐ 21 MODOS
- **Modos diatónicos** (7): Jónico/Mayor, Dórico, Frigio, Lidio, Mixolidio, Eólico/Menor, Locrio
- **Escalas menores** (2): Menor armónica, Menor melódica
- **Modos de menor armónica** (7): Locrio ♮6, Jónico aumentado, Dórico #4, Frigio dominante, Lidio #2, Ultralocrio
- **Modos de menor melódica** (7): Dórico ♭2, Lidio aumentado, Lidio dominante, Mixolidio ♭6, Locrio ♮2, Alterado/Superlocrio
- **Jerarquía de notas**:
  - Notas estructurales (I, III, V del acorde)
  - Notas de paso (movimiento por grado conjunto)
  - Bordaduras (ornamentación)
  - Apoyaturas (tensión-resolución)

### 3. Métricas Regulares y Amalgama
- Métricas simples: 2/4, 3/4, 4/4
- Métricas compuestas: 6/8, 9/8, 12/8
- **Métricas amalgama**: 5/8, 7/8, 11/8 con subdivisiones personalizables
  - Ejemplo: 5/8 = [2,3] o [3,2]
  - Ejemplo: 7/8 = [2,2,3] o [3,2,2] o [2,3,2]

### 4. Cadencias Auténticas
- **Semicadencia**: Final del antecedente (reposo en V)
- **Cadencia auténtica**: Final del consecuente (V→I)
- Progresión armónica implícita (I-IV-V-I)

### 5. Sistema de Infracción y Compensación
- Control probabilístico de "reglas rotas"
- Compensación automática para mantener coherencia
- Parámetro `infraction_rate` ajustable (0.0-1.0)

### 6. Silencios Musicales Estratégicos
- **Respiraciones**: Silencios al final de semifrases para articulación
- **Impulsos anacrúsicos**: Silencios antes del tiempo fuerte como preparación
- **Silencios acéfalos**: Silencios en el tiempo fuerte para efecto rítmico
- **Puntos de inflexión**: Silencios decorativos que no interrumpen la melodía
- Control mediante `use_rests` y `rest_probability` (0.0-1.0)

### 7. Variaciones Motívicas Clásicas
- **Inversión**: Intervalos se invierten (sube→baja, baja→sube)
- **Retrogradación**: Motivo tocado al revés
- **Aumentación**: Valores rítmicos más largos (×2)
- **Disminución**: Valores rítmicos más cortos (÷2)
- **Transposición**: Motivo en otro grado de la escala
- Aplicación contextual según proximidad al clímax

### 8. Control Explícito del Clímax Melódico
- **Posición configurable**: Define dónde ocurre el clímax (0.0-1.0)
- **Aproximación gradual**: 3 compases de construcción hacia el clímax
- **Registro expandido**: Octavas más altas en el clímax
- **Intensidad ajustable**: Factor multiplicador para el registro (1.0-2.0)
- **Tracking de altura**: Seguimiento del registro más alto alcanzado
- Integración con variaciones motívicas para máximo efecto

### 9. Restricciones Melódicas Clásicas
- **Saltos limitados**: Máximo sexta (configurable), octava solo en clímax
- **Recuperación de saltos**: Todo salto >tercera se recupera por movimiento contrario
- **Ámbito melódico**: Octava de la tónica ± cuarta perfecta (ej: G3-C6 para Sol)
- Seguimiento de dirección intervalar para movimiento contrario

### 10. Sistema Tenoris (Gregoriano)
- **Nota tenens**: Uso de la quinta (dominante) como nota sostenedora
- Aplicado en tiempos estructurales con probabilidad configurable
- Inspirado en el canto gregoriano donde la quinta actúa como "tono de recitación"
- ⚠️ Advertencia: Probabilidad alta puede aplanar la melodía

### 11. Salida a Archivo LilyPond
- **Guardado automático**: Opción de guardar como `.ly` directamente
- **Formato profesional**: Notación absoluta con header (título/compositor)
- **Compatibilidad total**: Notación estándar LilyPond (is/es en lugar de s/f)
- **MIDI automático**: Incluye bloque `\midi {}` para exportación

### 12. Ritmo Anclado a Pulsos
- **Generación beat-by-beat**: Cada pulso se trata como unidad indivisible
- **Respeta jerarquía métrica**: Notas estructurales en pulsos fuertes, notas de paso en débiles
- **Sin síncopas involuntarias**: Las duraciones no cruzan fronteras de pulsos
- **Subdivisiones controladas**: Dentro de cada pulso (corchea-puntillo + semicorchea)

### 13. Cohesión Melódica con Motivo Rítmico (Método Tradicional)
- **Motivo rítmico único**: Se genera UN patrón rítmico base para toda la pieza
- **Economía de materiales**: Reutilización del motivo en lugar de ritmos aleatorios
- **Variaciones sutiles**: Retrogradación aplicada en 30% de compases (excepto cadencias)
- **Estructura de uso**:
  - Compases 1-2: Motivo original (establece identidad)
  - Compases 3-6: 70% original, 30% variaciones
  - Compases 7-8: Motivo original (cadencias para claridad)
- **Resultado**: Melodías más orgánicas, cantábiles y memorables

### 14. Generación Jerárquica (Método Nuevo) ⭐ REVOLUCIONARIO
- **Dos métodos de generación disponibles**:
  1. **Tradicional**: Sistema de cohesión rítmica (método probado)
  2. **Jerárquico**: Jerarquía formal auténtica (NUEVO)
- **Estructura jerárquica verdadera**:
  - **Motivo** (2-4 notas): Célula generadora, como palabras en una oración
  - **Frase** (2 compases): Motivo + respuesta/variación, idea musical completa
  - **Semifrase** (4 compases): Agrupación de frases
  - **Período** (8 compases): Unidad completa con antecedente y consecuente
- **Armonía implícita por compás**: Cada compás tiene función armónica asignada
  - Progresión 8 compases: [I, I, IV, V, I, I, IV, I]
  - Guía selección de notas (tonos de acorde vs. notas de paso)
  - Proporciona "campo de movimiento" para la melodía
- **Economía de materiales**: Un motivo base variado constantemente, no material aleatorio
- **Fórmula fractal**: Para obras >8 compases, divide en múltiples períodos recursivamente
- **Libertad de variación**: 3 niveles configurables
  - **Nivel 1 (Estricta)**: Motivo siempre reconocible (original, retrogradación, transposición)
  - **Nivel 2 (Moderada)**: Balance familiar/nuevo (añade inversión, aumentación, disminución)
  - **Nivel 3 (Libre)**: Máxima creatividad (todas las variaciones posibles)
- **Equilibrio familiar/novedoso**: Balance automático entre repetición (comodidad) y variación (desarrollo)

---

## 📦 Instalación

```bash
pip install abjad music21
```

**Nota importante sobre notación**: El código generado usa **notación estándar LilyPond** (holandesa):
- Sostenidos: `cis`, `dis`, `fis`, etc. (not `cs`, `ds`, `fs`)
- Bemoles: `bes`, `es`, `as` (not `bf`, `ef`, `af`)
- Dobles alteraciones: `cisis`, `deses`, etc.

Esta es la notación nativa de LilyPond y funciona en todas las instalaciones sin necesidad de `\language "english"`.

---

## 🎮 Uso

### Modo Interactivo (Recomendado)

```bash
python3 main.py
```

El programa te guiará paso a paso:

1. **Tonalidad**: C, D, Eb, F#, etc.
2. **Modo**: 21 modos disponibles (ver sección "Modos Musicales")
3. **Compás**: Numerador y denominador (ej: 4/4, 5/8, 7/8)
4. **Subdivisiones**: Para métricas amalgama (ej: 5/8 = [2,3])
5. **Número de compases**: Recomendado: 8
6. **Tipo de impulso**: Tético, anacrúsico, acéfalo
7. **Complejidad rítmica**: 1=simple, 2=moderado, 3=complejo
8. **Usar silencios**: Respiraciones estratégicas (s/n)
9. **Usar tenoris**: Quinta como nota sostenedora (s/n)
10. **Posición del clímax**: 0.0-1.0 (recomendado: 0.7)
11. **Libertad de variación**: 1=estricta, 2=moderada, 3=libre ⭐ NUEVO
12. **Método de generación**: Tradicional vs. Jerárquico ⭐ REVOLUCIONARIO
13. **Título y compositor**: Metadata para la partitura
14. **Guardar archivo**: Opción de guardar como `.ly`

### Modo Programático

```python
from main import MelodicArchitect, ImpulseType

# Ejemplo: Melodía con clímax controlado y variaciones motívicas
architect = MelodicArchitect(
    key_name="C",
    mode="major",
    meter_tuple=(4, 4),
    num_measures=8,
    impulse_type=ImpulseType.TETIC,
    infraction_rate=0.05,
    rhythmic_complexity=2,
    use_rests=True,                    # Activar silencios
    rest_probability=0.15,             # 15% de probabilidad de silencio
    use_motivic_variations=True,       # Activar variaciones motívicas
    variation_probability=0.4,         # 40% de aplicar variación
    climax_position=0.75,              # Clímax al 75% (compás 6 de 8)
    climax_intensity=1.5,              # 50% más intenso en registro
    max_interval=6,                    # Máximo salto: sexta (default)
    use_tenoris=False,                 # Usar quinta como nota tenens
    tenoris_probability=0.2,           # Probabilidad de tenoris (si activado)
    variation_freedom=2                # Libertad variación (1=estricta, 2=moderada, 3=libre)
)

# MÉTODO TRADICIONAL (cohesión rítmica)
print(architect.generate_and_display(
    title="Mi Melodía (Tradicional)",
    composer="Compositor"
))

# MÉTODO JERÁRQUICO (jerarquía formal auténtica) ⭐ NUEVO
staff = architect.generate_period_hierarchical()
print(architect._format_as_lilypond(
    staff,
    title="Mi Melodía (Jerárquico)",
    composer="Compositor"
))
```

---

## 🎵 Modos Musicales (21 Modos)

El generador soporta **21 modos musicales** organizados en cuatro categorías. Cada modo tiene su propia estructura interválica única y carácter tonal distintivo.

### Modos Diatónicos (de Escala Mayor)

Estos son los 7 modos tradicionales derivados de la escala mayor:

| Modo | Nombre | Código | Intervalos (semitonos) | Carácter |
|------|--------|--------|------------------------|----------|
| 1 | Jónico / Mayor | `major` | 0-2-4-5-7-9-11 | Brillante, feliz |
| 2 | Dórico | `dorian` | 0-2-3-5-7-9-10 | Modal, jazzy |
| 3 | Frigio | `phrygian` | 0-1-3-5-7-8-10 | Español, oscuro |
| 4 | Lidio | `lydian` | 0-2-4-6-7-9-11 | Etéreo, soñador |
| 5 | Mixolidio | `mixolydian` | 0-2-4-5-7-9-10 | Blues, rock |
| 6 | Eólico / Menor natural | `minor` | 0-2-3-5-7-8-10 | Triste, melancólico |
| 7 | Locrio | `locrian` | 0-1-3-5-6-8-10 | Inestable, dissonante |

### Escalas Menores

Variantes clásicas de la escala menor:

| Escala | Código | Intervalos (semitonos) | Característica distintiva |
|--------|--------|------------------------|---------------------------|
| Menor armónica | `harmonic_minor` | 0-2-3-5-7-8-11 | Segunda aumentada entre 6º y 7º grado |
| Menor melódica | `melodic_minor` | 0-2-3-5-7-9-11 | 6º y 7º grados elevados (versión ascendente) |

### Modos de Menor Armónica

7 modos derivados de la escala menor armónica, ampliamente usados en jazz y música del Medio Oriente:

| Modo | Nombre | Código | Uso característico |
|------|--------|--------|--------------------|
| 1 | Menor armónica | `harmonic_minor` | Menor clásico con sensible |
| 2 | Locrio ♮6 | `locrian_nat6` | Modal oscuro con color |
| 3 | Jónico aumentado | `ionian_aug5` | Impresionista, augmentado |
| 4 | Dórico #4 / Ucraniano | `dorian_sharp4` | Folklore eslavo |
| 5 | Frigio dominante | `phrygian_dominant` | Flamenco, español, árabe |
| 6 | Lidio #2 | `lydian_sharp2` | Exótico, oriental |
| 7 | Ultralocrio | `superlocrian_bb7` | Muy tenso, experimental |

### Modos de Menor Melódica

7 modos derivados de la escala menor melódica, fundamentales en jazz moderno:

| Modo | Nombre | Código | Uso característico |
|------|--------|--------|--------------------|
| 1 | Menor melódica | `melodic_minor` | Jazz menor, clásico |
| 2 | Dórico ♭2 / Frigio #6 | `dorian_flat2` | Modal exótico |
| 3 | Lidio aumentado | `lydian_augmented` | Impresionista, etéreo |
| 4 | Lidio dominante | `lydian_dominant` | Acordes dominantes alterados (jazz) |
| 5 | Mixolidio ♭6 | `mixolydian_flat6` | Modal oscuro |
| 6 | Locrio ♮2 / Semilocrio | `locrian_nat2` | Menos tenso que locrio |
| 7 | Alterado / Superlocrio | `altered` | Dominante alterado (jazz avanzado) |

### Ejemplos de Uso

```python
# Frigio dominante en E (flamenco)
architect = MelodicArchitect(
    key_name="E",
    mode="phrygian_dominant",
    meter_tuple=(3, 4),
    num_measures=8
)

# Lidio dominante en F (jazz)
architect = MelodicArchitect(
    key_name="F",
    mode="lydian_dominant",
    meter_tuple=(4, 4),
    num_measures=8
)

# Alterado en B (sobre dominante B7alt → Em)
architect = MelodicArchitect(
    key_name="B",
    mode="altered",
    meter_tuple=(4, 4),
    num_measures=8
)

# Ucraniano en D (folklore)
architect = MelodicArchitect(
    key_name="D",
    mode="dorian_sharp4",
    meter_tuple=(7, 8),
    subdivisions=[2, 2, 3],
    num_measures=8
)

# Comparación de métodos (misma configuración)

# MÉTODO TRADICIONAL (cohesión rítmica)
architect_trad = MelodicArchitect(
    key_name="C",
    mode="major",
    meter_tuple=(3, 4),
    num_measures=8
)
print(architect_trad.generate_and_display(title="Vals (Tradicional)"))

# MÉTODO JERÁRQUICO (jerarquía formal)
architect_hier = MelodicArchitect(
    key_name="C",
    mode="major",
    meter_tuple=(3, 4),
    num_measures=8,
    variation_freedom=2  # Moderada
)
staff = architect_hier.generate_period_hierarchical()
print(architect_hier._format_as_lilypond(staff, title="Vals (Jerárquico)"))
```

### Nota sobre LilyPond

LilyPond solo soporta nativamente los 7 modos diatónicos (`\major`, `\minor`, `\dorian`, `\phrygian`, `\lydian`, `\mixolydian`, `\locrian`). Los modos exóticos derivados de menor armónica y melódica se mapean al modo diatónico más cercano en la armadura, pero las alteraciones específicas se aplican nota por nota en el código generado.

---

## 🔄 Dos Métodos de Generación

El sistema ofrece dos enfoques complementarios para generar melodías, cada uno basado en diferentes principios de la teoría musical clásica:

### Comparación: Método Tradicional vs. Jerárquico

| Aspecto | Tradicional | Jerárquico ⭐ NUEVO |
|---------|-------------|---------------------|
| **Enfoque** | Cohesión rítmica | Jerarquía formal auténtica |
| **Estructura** | Motivo rítmico único reutilizado | Motivo → Frase → Período |
| **Armonía** | Implícita en cadencias | Implícita por compás |
| **Economía** | Ritmo consistente, 70% original | Motivo melódico variado constantemente |
| **Variaciones** | Retrogradación (30%) | 6 tipos (inversión, retro, aumento, etc.) |
| **Libertad** | Fija (30% variación) | Configurable (estricta/moderada/libre) |
| **Longitud** | Cualquiera | Fórmula fractal (8, 9, 11, 16, 23+) |
| **Uso recomendado** | Melodías cantábiles simples | Obras estructuradas complejas |
| **Inspiración** | Economía de materiales | Wikipedia (forma musical clásica) |

**Ambos métodos**:
- ✅ Coexisten en el mismo código
- ✅ Comparten parámetros (tonalidad, modo, métrica, etc.)
- ✅ Usuario elige en tiempo de ejecución (menú interactivo)
- ✅ Generan código LilyPond compatible

### Método 1: Tradicional (Cohesión Rítmica)

**Principio**: Un motivo rítmico único es la columna vertebral de toda la melodía.

**Características**:
- Generación beat-by-beat (cada pulso es indivisible)
- Motivo rítmico base generado al inicio
- Variaciones sutiles (retrogradación en 30% de compases)
- Estructura: Compases 1-2 (identidad), 3-6 (variaciones), 7-8 (original para cadencias)
- Sin síncopas involuntarias
- Resultado: Melodías orgánicas, cantábiles, memorables

**Cuándo usar**:
- Melodías populares o folclóricas
- Canciones infantiles
- Piezas didácticas
- Cuando se busca máxima claridad y coherencia rítmica

### Método 2: Jerárquico ⭐ REVOLUCIONARIO

**Principio**: Jerarquía formal auténtica según teoría musical académica (Wikipedia: "Forma musical", "Melodía").

**Características**:
- **Motivo base** (2-4 notas): Célula generadora para toda la pieza
- **Frase** (2 compases): Motivo + respuesta/variación
- **Período** (8 compases): Antecedente (pregunta) + Consecuente (respuesta)
- **Armonía implícita**: Cada compás tiene función armónica [I, I, IV, V, I, I, IV, I]
- **6 tipos de variación**:
  - ORIGINAL (baseline)
  - RETROGRADE (notas al revés)
  - INVERSION (intervalos invertidos)
  - TRANSPOSITION (trasladado a otro grado)
  - AUGMENTATION (duraciones ×2)
  - DIMINUTION (duraciones ÷2)
- **Libertad de variación configurable**:
  - Nivel 1 (Estricta): 40% original, 30% retro, 30% transposición
  - Nivel 2 (Moderada): + inversión, aumentación, disminución
  - Nivel 3 (Libre): Todas las variaciones posibles
- **Fórmula fractal**: Divide obras largas en períodos de ~8 compases
  - 8 compases: Un período
  - 16 compases: Dos períodos completos
  - 23 compases: Tres períodos + extensión

**Cuándo usar**:
- Obras formales complejas
- Análisis de formas clásicas
- Experimentación con variaciones motívicas
- Cuando se busca desarrollo temático sofisticado

### Cómo Identificar el Método en la Salida

**Método Tradicional**:
- Busca el patrón rítmico: un ritmo base aparece repetidamente
- Los compases 1-2 y 7-8 tienen ritmo idéntico (cadencias)
- Variaciones rítmicas sutiles en compases 3-6

**Método Jerárquico**:
- Busca el motivo melódico: una célula de 2-4 notas como "tema"
- Cada compás tiene carácter armónico claro (I, IV, o V)
- Variaciones más dramáticas: inversión, aumentación, transposición
- Estructura formal evidente: pregunta (compases 1-4) + respuesta (5-8)

---

## ⚙️ Parámetros de Configuración

| Parámetro | Tipo | Descripción | Valores |
|-----------|------|-------------|---------|
| `key_name` | str | Tonalidad | "C", "D", "Eb", "F#", etc. |
| `mode` | str | Modo musical | Ver sección "Modos Disponibles" (21 modos) |
| `meter_tuple` | tuple | Compás | (4,4), (3,4), (5,8), (7,8), etc. |
| `subdivisions` | list | Subdivisión de amalgama | [2,3], [3,2], [2,2,3], etc. |
| `num_measures` | int | Número de compases | 4, 8, 16, etc. (par recomendado) |
| `impulse_type` | ImpulseType | Tipo de impulso inicial | TETIC, ANACROUSTIC, ACEPHALOUS |
| `infraction_rate` | float | Tasa de infracción | 0.0 (estricto) a 1.0 (muy libre) |
| `rhythmic_complexity` | int | Complejidad rítmica | 1 (simple) a 5 (muy complejo) |
| `use_rests` | bool | Usar silencios estratégicos | True/False (default: True) |
| `rest_probability` | float | Probabilidad de silencio | 0.0 (sin silencios) a 1.0 (máximo) |
| `use_motivic_variations` | bool | Usar variaciones motívicas | True/False (default: True) |
| `variation_probability` | float | Probabilidad de variación | 0.0 (sin variaciones) a 1.0 (máximo) |
| `climax_position` | float | Posición del clímax | 0.0 (inicio) a 1.0 (final), típico: 0.7-0.8 |
| `climax_intensity` | float | Intensidad del clímax | 1.0 (normal) a 2.0 (muy intenso) |
| `max_interval` | int | Máximo salto melódico | 6 (sexta, default), valores típicos: 4-9 |
| `use_tenoris` | bool | Usar tenoris (quinta) | True/False (default: False) |
| `tenoris_probability` | float | Probabilidad de tenoris | 0.0 (nunca) a 1.0 (siempre), recomendado: 0.15-0.25 |
| `variation_freedom` | int | Libertad de variación motívica | 1 (estricta), 2 (moderada), 3 (libre) - solo método jerárquico |

---

## 📚 Teoría Musical Implementada

El generador implementa los conceptos fundamentales de la composición melódica clásica:

### 1. Jerarquía Estructural

La melodía se construye "de abajo hacia arriba", uniendo piezas pequeñas para formar estructuras mayores.

#### El Motivo (La Célula)
Es la unidad mínima con sentido musical. Suele tener entre 2 y 5 notas y se define por un **perfil rítmico** y un **intervalo** característico. El motivo es la "semilla": toda la melodía posterior suele ser una variación, repetición o desarrollo de este pequeño fragmento.

#### La Frase y la Semifrase
La unión de varios motivos forma una **semifrase**. Normalmente, dos semifrases forman una **frase** (que suele durar 4 compases). La Frase es la unidad menor que presenta una idea completa, pero que suele necesitar una respuesta para alcanzar el equilibrio total.

#### Antecedente y Consecuente (Pregunta y Respuesta)
Este es el concepto de "simetría". Cuando dos frases se relacionan entre sí, forman un **Período**:

1. **Antecedente (Sucedente):** Es la primera frase. Termina con una sensación de "suspense" o pregunta, generalmente mediante una **semicadencia** (reposo en el V grado o dominante).
2. **Consecuente:** Es la segunda frase. Funciona como la respuesta. Suele empezar igual o similar al antecedente, pero termina con una **cadencia auténtica** (reposo en el I grado o tónica), dando una sensación de cierre total.

#### El Tema
A diferencia de una simple melodía, el **Tema** es una estructura más compleja y cerrada (a menudo de 8 o 16 compases) que sirve como base para una obra entera o un movimiento (como en una Sonata). Un tema contiene varios motivos y está perfectamente equilibrado por antecedentes y consecuentes.

| Nivel | Componente | Función |
|-------|------------|---------|
| **Micro** | Motivo | Identidad rítmica y melódica básica |
| **Medio** | Semifrase | Agrupación de motivos |
| **Macro** | Antecedente | Plantea el conflicto (Pregunta) |
| **Macro** | Consecuente | Resuelve el conflicto (Respuesta) |
| **Total** | Período / Tema | Unidad completa con sentido narrativo |

### 2. Determinación del Ritmo

En la teoría estricta, el ritmo melódico no es aleatorio; está dictado por la **métrica** y la **armonía implícita**.

#### A. El Sistema de Acentuación (Métrica)
El ritmo se adapta al compás elegido (2/4, 3/4, 4/4, etc.). La melodía debe respetar la jerarquía de los pulsos:

- **Tiempos Fuertes:** Las notas más importantes de la melodía (las que definen el acorde) suelen caer en el primer tiempo del compás.
- **Síncopas o Contratiempos:** Se usan para generar tensión, desplazando el acento natural hacia los tiempos débiles.

#### B. El Ritmo Armónico
Es la velocidad con la que cambian los acordes de fondo. La melodía "determina" su ritmo basándose en este cambio:

- Si la armonía cambia cada compás, la melodía suele tener notas largas o diseños que refuercen ese cambio.
- Si el ritmo armónico es lento, la melodía suele volverse más activa rítmicamente (corcheas, semicorcheas) para mantener el interés.

#### C. Tipos de Inicio y Final
El ritmo inicial define el carácter:

- **Tético:** Comienza justo en el primer tiempo fuerte (sensación de estabilidad).
- **Anacrúsico:** Comienza antes del primer tiempo fuerte, como un impulso hacia arriba (sensación de dirección).
- **Acéfalo:** Comienza después del primer tiempo fuerte (sensación de duda o síncopa).

### 3. Notas Estructurales vs. Ornamentación

Al componer un motivo, se decide qué notas son la "columna vertebral" y cuáles son el "adorno":

#### Notas Estructurales
Son las que coinciden con los **acentos métricos** o los cambios de armonía. Suelen ser notas del acorde (tónica, tercera o quinta). Si quitas todo lo demás y dejas solo estas notas, la melodía sigue siendo reconocible.

**Regla de Oro:** Si la melodía salta (un intervalo mayor a una 3ª), **ambas notas** deben ser estructurales. El salto en la música clásica es una "arpegiación" de la armonía.

#### Notas de Paso y Bordaduras
- **Notas de Paso:** Notas que unen dos notas estructurales por grados conjuntos (escalísticos) en tiempos débiles. Deben moverse por **grado conjunto** (segundas) y preferiblemente en **tiempos débiles**.
- **Bordaduras:** Notas que adornan una nota estructural y vuelven a ella.
- **Apoyaturas:** Una nota que "golpea" en tiempo fuerte pero no pertenece al acorde, resolviendo inmediatamente en una nota estructural. Es la base de la expresión emocional (el "suspiro" clásico).

### 4. El Sistema de Castas de la Escala

En una tonalidad (por ejemplo, Do Mayor), no todas las notas nacen iguales:

#### A. Notas de Estabilidad (Nivel 1: El Tríptico de la Tónica)
Son los grados **I, III y V** (la tríada de tónica).
- **Función:** Son las únicas notas que pueden ser "finales" o puntos de reposo absoluto.
- **En la estructura:** Son las candidatas principales para ocupar los **tiempos fuertes** y ser el destino de los saltos melódicos.

#### B. Notas de Tensión o Tendencia (Nivel 2)
Son los grados que "quieren" moverse hacia las estables:
- **La Sensible (VII):** Tiene una atracción magnética hacia la tónica (I).
- **La Cuarta (IV):** Tiende a bajar a la tercera (III).
- **Función:** Crean la propulsión rítmica. Se usan en tiempos débiles como notas de paso o en tiempos fuertes para crear **apoyaturas** (tensión que resuelve).

### 5. La Armonía Implícita

Una melodía tradicional bien construida debe sugerir sus propios acordes aunque no haya un piano acompañando. Esto se logra mediante la **Cadencia**:

- **Para el Antecedente (Sucedente):** El algoritmo debe dirigir la melodía hacia una nota que pertenezca al acorde de **Dominante (V)** al final del compás 4. Esto crea la "pregunta".
- **Para el Consecuente:** El algoritmo debe forzar un movimiento **VII → I** o **V → I** al final del compás 8. Esto crea la "respuesta".

### 6. Métricas Amalgama (Pulsos Irregulares)

En compases como 5/8, 7/8 o 11/8, la "rejilla de pesos" ya no es uniforme. El algoritmo debe conocer la **subdivisión interna**:

- **Ejemplo 5/8 (2+3):** Pulso Binario (Fuerte-débil) + Pulso Ternario (Fuerte-débil-débil).
- **Acentuación:** El "1" siempre es el acento principal, pero el "3" (en el caso de 2+3) recibe un acento secundario que actúa como un nuevo anclaje para una nota estructural.

### 7. Módulo de "Infracción y Compensación"

Para evitar la rigidez, se introduce una **Probabilidad de Desequilibrio** (típicamente 10-15%):

- **La Infracción:** El algoritmo puede decidir colocar una nota no-cordal (disonancia) en un tiempo fuerte sin ser una apoyatura estándar, o desplazar una nota estructural a un tiempo débil (síncopa extrema).
- **La Compensación (Ley de Hierro):** Si se rompe la regla de la estabilidad, el siguiente evento musical **debe** ser hiper-estable.
  - Si hay salto disonante: La siguiente nota debe moverse por grado conjunto en dirección opuesta.
  - Si hay síncopa (desplazamiento rítmico): El siguiente pulso fuerte debe ser un silencio o una nota larga que "reabsorba" la energía desplazada.

### 8. El Secreto de la "Unidad en la Variedad"

La teoría estricta dice que para que una sección sea coherente, debe haber una **economía de materiales**. No inventes ritmos nuevos constantemente; usa el ritmo del motivo inicial, dale la vuelta, estíralo (aumentación) o encógelo (disminución), pero mantén siempre esa "semilla rítmica" presente para que el oyente no se pierda.

### Resumen de Principios Implementados

1. **Jerarquía Métrica**: Pulsos fuertes vs. débiles
2. **Inicio del Motivo**: Tético, Anacrúsico, Acéfalo
3. **Notas Estructurales**: Corresponden a acordes implícitos
4. **Notas de Paso**: Movimiento por grado conjunto en tiempos débiles
5. **Contorno Melódico**: Control de rango y dirección
6. **Cadencias**: Semicadencia (antecedente) y auténtica (consecuente)
7. **Progresión Armónica**: I-IV-V-I implícita
8. **Silencios Estratégicos**: Respiraciones, impulsos, decorativos
9. **Variaciones Motívicas**: Inversión, retrogradación, aumentación, disminución, transposición
10. **Clímax Melódico Controlado**: Posición configurable, aproximación gradual, registro expandido
11. **Restricciones de Saltos**: Máximo sexta, recuperación por movimiento contrario
12. **Ámbito Melódico Controlado**: Octava de la tónica ± cuarta perfecta
13. **Sistema Tenoris**: Quinta como nota sostenedora (tradición gregoriana)
14. **Jerarquía Formal Auténtica** (Método Jerárquico): Motivo → Frase → Semifrase → Período

---

## 🏗️ Arquitectura del Código

```
MelodicArchitect (~2700 líneas)
│
├── Capa I: Configuración de la Realidad Musical
│   ├── Escala/Modo (music21)
│   ├── Métrica y subdivisiones
│   ├── Parámetros de control
│   └── Control del clímax melódico
│
├── Capa II: Generación del ADN (Motivo y Frase)
│   ├── MÉTODO TRADICIONAL:
│   │   ├── Patrones rítmicos (motivo único reutilizado)
│   │   ├── Selección de tonos (estructurales vs. paso)
│   │   ├── Cohesión rítmica (economía de materiales)
│   │   └── Variaciones sutiles (retrogradación 30%)
│   │
│   └── MÉTODO JERÁRQUICO: ⭐ NUEVO
│       ├── create_base_motif() - Genera motivo de 2-4 notas
│       ├── create_harmonic_progression() - Progresión I-IV-V-I
│       ├── apply_motif_variation() - 6 tipos de variación
│       │   ├── ORIGINAL, RETROGRADE
│       │   ├── INVERSION, TRANSPOSITION
│       │   ├── AUGMENTATION, DIMINUTION
│       │   └── Nivel de libertad: estricta/moderada/libre
│       └── Estructura Motivo → Frase (2 bars) → Período (8 bars)
│
└── Capa III: Desarrollo y Cierre (Período y Cadencia)
    ├── generate_period() - MÉTODO TRADICIONAL
    │   ├── Estructura antecedente-consecuente
    │   ├── Cadencias (semicadencia y auténtica)
    │   └── Motivo rítmico consistente
    │
    ├── generate_period_hierarchical() - MÉTODO JERÁRQUICO ⭐
    │   ├── Jerarquía formal auténtica
    │   ├── Armonía implícita por compás
    │   ├── Fórmula fractal (obras de cualquier longitud)
    │   └── Balance familiar/novedoso
    │
    └── Salida en formato Abjad/LilyPond
        ├── Notación estándar (is/es)
        ├── Header profesional
        └── Bloques \layout y \midi
```

### Ubicación de Métodos Clave

| Feature | Lines | Method/Class |
|---------|-------|--------------|
| **Data structures** | 123-161 | HarmonicFunction, Phrase, Semiphrase, Period |
| **Variation freedom param** | 192, 323 | `__init__`, stored in `self.variation_freedom` |
| **Motif generator** | 877-1004 | `create_base_motif()` |
| **Harmonic progression** | 1006-1124 | `create_harmonic_progression()` |
| **Motif variation** | 1126-1292 | `apply_motif_variation()` |
| **Traditional method** | 1826-1886 | `generate_period()` (ORIGINAL) |
| **Hierarchical method** | 1889-1985 | `generate_period_hierarchical()` (NEW) |
| **Measure from motif** | 1987-2053 | `_create_measure_from_motif()` |
| **Menu questions** | 2597-2619 | `main()` - variation freedom & method selection |
| **Method routing** | 2631-2645 | `main()` - calls hierarchical or traditional |

---

## 👨‍💻 Guía para Desarrolladores

### Convenciones de Código

#### Imports
- Standard library (random, enum, dataclasses, typing)
- music21 (key, pitch, interval, scale)
- abjad (for LilyPond generation)
- Order: stdlib → music21 → abjad

#### Naming Conventions
- **Classes**: PascalCase (`MelodicArchitect`, `ImpulseType`, `NoteFunction`)
- **Methods**: snake_case (`get_pitch_by_degree`, `create_measure`, `generate_period`)
- **Variables**: snake_case, descriptive (`strong_beats`, `is_cadence`, `harmonic_function`)
- **Enums**: SCREAMING_SNAKE_CASE for values (`ImpulseType.TETIC`)

#### Code Organization
- **3-Layer Architecture**:
  1. Configuración de Realidad Musical (tonalidad, métrica, parámetros)
  2. Generación del ADN Melódico (motivos, ritmos, selección de tonos)
  3. Desarrollo y Cierre (períodos, cadencias, output)
- Use dataclasses for data structures (`RhythmicPattern`, `MelodicContour`)
- Separate music21 (musical logic) from abjad (output formatting)

### Abjad API Specifics
- `abjad.Note()` takes string format: `"c'4"` (pitch + duration)
- Pitch format: `c'` = C4, `c''` = C5, `c` = C3, `c,` = C2
- Flats use 'f' (`ef` = Eb), sharps use 's' (`cs` = C#)
- Duration: number after pitch (4 = quarter, 8 = eighth, 2 = half, 1 = whole)
- Dotted notes: append dot (`c'4.` = dotted quarter)
- Notes in Container cannot be reused; create new instances

### LilyPond Output Format
- Output wrapped in `\score { ... }` block
- Automatic `\midi {}` block for MIDI file generation
- Compatible with Frescobaldi and standalone LilyPond
- **CRITICAL**: Use standard LilyPond notation (is/es, not s/f)
  - Sharps: `cis`, `dis`, `fis` (not `cs`, `ds`, `fs`)
  - Flats: `bes`, `es`, `as` (not `bf`, `ef`, `af`)
  - Method `_english_to_standard_pitch()` handles conversion

### Modificar el Código

Para añadir nuevas características:

1. **Nuevos modos musicales**: Edita el diccionario `MODE_INTERVALS` (línea ~50)
2. **Nuevas variaciones motívicas**: Añade casos en `apply_motif_variation()` (línea 1126)
3. **Nueva progresión armónica**: Modifica `create_harmonic_progression()` (línea 1006)
4. **Nuevo método de generación**: Crea método similar a `generate_period_hierarchical()` (línea 1889)

---

## 💡 Ejemplos Avanzados

### Métrica Amalgama 5/8 en Re menor

```python
architect = MelodicArchitect(
    key_name="D",
    mode="minor",
    meter_tuple=(5, 8),
    subdivisions=[2, 3],  # 2+3 pulsos
    num_measures=8,
    impulse_type=ImpulseType.ANACROUSTIC,
    infraction_rate=0.15,
    rhythmic_complexity=3
)
```

### Modo Dórico con métrica 7/8 y silencios acéfalos

```python
architect = MelodicArchitect(
    key_name="E",
    mode="dorian",
    meter_tuple=(7, 8),
    subdivisions=[2, 2, 3],  # 2+2+3 pulsos
    num_measures=8,
    impulse_type=ImpulseType.ACEPHALOUS,
    infraction_rate=0.2,
    rhythmic_complexity=4,
    use_rests=True,
    rest_probability=0.18
)
```

### Método Jerárquico con Libertad Libre

```python
architect = MelodicArchitect(
    key_name="C",
    mode="major",
    meter_tuple=(4, 4),
    num_measures=16,
    variation_freedom=3,  # Libre (todas las variaciones)
    climax_position=0.7,
    climax_intensity=1.8
)

staff = architect.generate_period_hierarchical()
print(architect._format_as_lilypond(staff, title="Sonata Op. 1"))
```

### Identificar Características en la Salida

#### Clímax Melódico
En el código LilyPond generado, busca notas con múltiples apóstrofes (`'`):
- `c'` = Do4 (normal)
- `c''` = Do5 (una octava arriba)
- `c'''` = Do6 (dos octavas arriba) ← **Indicador de clímax**

Ejemplo:
```lilypond
{
    g''4    % Aproximación al clímax
    a'''4   % ¡CLÍMAX! (La en octava 6)
    c'''4   % Después del clímax
}
```

#### Variaciones Motívicas
Compara los primeros compases con compases posteriores:
- **Inversión**: Mismos intervalos pero dirección opuesta
- **Retrogradación**: Secuencia de notas al revés
- **Secuencia**: Mismo patrón en otro grado
- **Aumentación**: Duraciones dobles (cuartos → medios)
- **Disminución**: Duraciones reducidas (cuartos → octavos)

### Formato de Salida LilyPond

El generador produce código LilyPond con formato profesional:

```lilypond
\header {
  title = "Título de la Melodía"
  composer = "Nombre del Compositor"
}

\score {
  {
    \time 4/4
    \key c \major
    \clef "treble"
    \set strictBeatBeaming = ##t
    c'4 e'4 g'4 c''4 |
    ...
  }
  
  \layout {}
  \midi {}
}
```

**Características**:
- ✅ Notación absoluta (no relativa)
- ✅ Notación estándar LilyPond (is/es en lugar de s/f)
- ✅ Header con título y compositor
- ✅ Bloques `\layout` y `\midi` automáticos
- ✅ Barlines simples `|` entre compases, `\bar "|."` al final
- ✅ `\set strictBeatBeaming` para agrupación correcta

---

## ⚠️ Limitaciones y Mejoras Futuras

### Limitaciones Conocidas

1. Las duraciones complejas (ej: 5/16) se simplifican
2. Tenoris con probabilidad muy alta (>0.3) puede aplanar la melodía
3. La variación motívica (aumentación/disminución) es básica
4. No hay soporte para polifonía o armonización explícita
5. Método jerárquico: RETROGRADE_INVERSION y SEQUENCE no implementados (devuelven original)
6. Método jerárquico: Relleno de compases usa solo tonos de acorde (podría usar notas de paso)

### Mejoras Futuras

#### Completadas ✅
- [x] Implementar variaciones motívicas (inversión, retrogradación)
- [x] Añadir control explícito del clímax melódico
- [x] Restricciones de saltos y recuperación
- [x] Ámbito melódico controlado
- [x] Sistema tenoris (gregoriano)
- [x] Salida a archivo .ly
- [x] Jerarquía formal auténtica (método jerárquico)
- [x] 21 modos musicales (diatónicos + harmonic/melodic minor)
- [x] Ritmo anclado a pulsos (sin síncopas involuntarias)
- [x] Cohesión rítmica con motivo único

#### Pendientes 📝
- [ ] Implementar RETROGRADE_INVERSION y SEQUENCE (método jerárquico)
- [ ] Mejorar relleno de compases en método jerárquico (notas de paso, bordaduras)
- [ ] Soporte para articulaciones y dinámicas
- [ ] Generación de acompañamiento armónico
- [ ] Análisis automático de melodías generadas
- [ ] Ornamentación (trinos, mordentes)
- [ ] Exportar directamente a PDF/MIDI (sin pasar por LilyPond)
- [ ] Soporte para texturas polifónicas simples

---

## 📄 Licencia

Proyecto educativo - uso libre para aprendizaje y experimentación musical.

---

## 🤝 Contribuciones

Este proyecto implementa la teoría musical clásica con rigor académico. Para contribuir:

1. Lee la documentación teórica completa (sección "Teoría Musical Implementada")
2. Mantén las convenciones de código (sección "Guía para Desarrolladores")
3. Preserva la compatibilidad con ambos métodos (Tradicional y Jerárquico)
4. Añade tests para nuevas características
5. Documenta todos los cambios

---

## 📞 Soporte

Para problemas técnicos o preguntas sobre teoría musical, consulta:
- Sección "Teoría Musical Implementada" (conceptos fundamentales)
- Sección "Arquitectura del Código" (ubicación de métodos)
- Sección "Ejemplos Avanzados" (casos de uso)

---

**¡Disfruta creando melodías con rigor académico y creatividad computacional!** 🎵✨
