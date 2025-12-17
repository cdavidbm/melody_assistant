# Generador de Melodías - Protocolo "Symmetry & Logic"

Implementación computacional de los principios de composición melódica de la teoría musical clásica, con soporte completo para métricas regulares y amalgama, modos musicales, y el sistema de jerarquía estructural.

## 📁 Estructura del Proyecto

```
Ejercicios music21 y Abjad/
├── main.py                   # Script principal del generador
├── README.md                 # Este archivo (documentación completa)
├── AGENTS.md                 # Guía para agentes de IA
├── tarea.md                  # Especificación teórica detallada
├── showcase_final.ly         # Ejemplo de salida (F Dorian 7/8)
└── main.py.BACKUP_PERFECTO_* # Backups automáticos con timestamp
```

## Características Principales

### 1. Jerarquía Estructural Completa
- **Motivo**: Célula rítmico-melódica fundamental
- **Semifrase**: Agrupación de motivos
- **Antecedente/Consecuente**: Sistema de pregunta-respuesta
- **Período**: Unidad completa con cierre cadencial

### 2. Sistema Tonal/Modal Avanzado
- Soporte para **modos**: Mayor, Menor, Dórico, Frigio, Lidio, Mixolidio
- **Jerarquía de notas**:
  - Notas estructurales (I, III, V del acorde)
  - Notas de paso (movimiento por grado conjunto)
  - Bordaduras (ornamentación)
  - Apoyaturas (tensión-resolución)

### 3. Métricas Regulares y Amalgama
- Métricas simples: 2/4, 3/4, 4/4
- Métricas compuestas: 6/8, 9/8, 12/8
- **Métricas amalgama**: 5/8, 7/8, 11/8 con subdivisiones personalizables
  - Ejemplo: 5/8 = 2+3 o 3+2
  - Ejemplo: 7/8 = 2+2+3 o 3+2+2 o 2+3+2

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

### 7. Variaciones Motívicas ⭐ NUEVO
- **Inversión**: Intervalos se invierten (sube→baja, baja→sube)
- **Retrogradación**: Motivo tocado al revés
- **Retrogradación invertida**: Combinación de ambas técnicas
- **Aumentación**: Valores rítmicos más largos (×2)
- **Disminución**: Valores rítmicos más cortos (÷2)
- **Transposición**: Motivo en otro grado de la escala
- **Secuencia**: Repetición transpuesta del motivo
- Aplicación contextual según proximidad al clímax

### 8. Control Explícito del Clímax Melódico ⭐ NUEVO
- **Posición configurable**: Define dónde ocurre el clímax (0.0-1.0)
- **Aproximación gradual**: 3 compases de construcción hacia el clímax
- **Registro expandido**: Octavas más altas en el clímax
- **Intensidad ajustable**: Factor multiplicador para el registro (1.0-2.0)
- **Tracking de altura**: Seguimiento del registro más alto alcanzado
- Integración con variaciones motívicas para máximo efecto

### 9. Restricciones Melódicas Clásicas ⭐ NUEVO
- **Saltos limitados**: Máximo sexta (configurable), octava solo en clímax
- **Recuperación de saltos**: Todo salto >tercera se recupera por movimiento contrario
- **Ámbito melódico**: Octava de la tónica ± cuarta perfecta (ej: G3-C6 para Sol)
- Seguimiento de dirección intervalar para movimiento contrario

### 10. Sistema Tenoris (Gregoriano) ⭐ NUEVO
- **Nota tenens**: Uso de la quinta (dominante) como nota sostenedora
- Aplicado en tiempos estructurales con probabilidad configurable
- Inspirado en el canto gregoriano donde la quinta actúa como "tono de recitación"
- ⚠️ Advertencia: Probabilidad alta puede aplanar la melodía

### 11. Salida a Archivo LilyPond ⭐ NUEVO
- **Guardado automático**: Opción de guardar como `.ly` directamente
- **Formato profesional**: Notación absoluta con header (título/compositor)
- **Compatibilidad total**: Notación estándar LilyPond (is/es en lugar de s/f)
- **MIDI automático**: Incluye bloque `\midi {}` para exportación

### 12. Ritmo Anclado a Pulsos ⭐ NUEVO
- **Generación beat-by-beat**: Cada pulso se trata como unidad indivisible
- **Respeta jerarquía métrica**: Notas estructurales en pulsos fuertes, notas de paso en débiles
- **Sin síncopas involuntarias**: Las duraciones no cruzan fronteras de pulsos
- **Subdivisiones controladas**: Dentro de cada pulso (corchea-puntillo + semicorchea en un pulso)
- Implementa principios de Wikipedia sobre métrica y tarea.md (líneas 161-166)

### 13. Cohesión Melódica con Motivo Rítmico ⭐ NUEVO
- **Motivo rítmico único**: Se genera UN patrón rítmico base para toda la pieza
- **Economía de materiales**: Reutilización del motivo en lugar de ritmos aleatorios
- **Variaciones sutiles**: Retrogradación aplicada en 30% de compases (excepto cadencias)
- **Estructura de uso**:
  - Compases 1-2: Motivo original (establece identidad)
  - Compases 3-6: 70% original, 30% variaciones
  - Compases 7-8: Motivo original (cadencias para claridad)
- **Resultado**: Melodías más orgánicas, cantábiles y memorables
- Principio (tarea.md líneas 128-130): "No inventes ritmos nuevos constantemente"

## Instalación

```bash
pip install abjad music21
```

**Nota importante sobre notación**: El código generado usa **notación estándar LilyPond** (holandesa):
- Sostenidos: `cis`, `dis`, `fis`, etc. (not `cs`, `ds`, `fs`)
- Bemoles: `bes`, `es`, `as` (not `bf`, `ef`, `af`)
- Dobles alteraciones: `cisis`, `deses`, etc.

Esta es la notación nativa de LilyPond y funciona en todas las instalaciones sin necesidad de `\language "english"`.

## Uso Básico

### Modo Interactivo (Recomendado)

```bash
python3 mainpy
```

El programa te guiará paso a paso:
1. **Tonalidad**: C, D, Eb, F#, etc.
2. **Modo**: Mayor, menor, dórico, frigio, lidio, mixolidio
3. **Compás**: Numerador y denominador (ej: 4/4, 5/8, 7/8)
4. **Subdivisiones**: Para métricas amalgama (ej: 5/8 = 2+3)
5. **Número de compases**: Recomendado: 8
6. **Tipo de impulso**: Tético, anacrúsico, acéfalo
7. **Complejidad rítmica**: 1=simple, 2=moderado, 3=complejo
8. **Usar silencios**: Respiraciones estratégicas (s/n)
9. **Usar tenoris**: Quinta como nota sostenedora (s/n) ⭐ NUEVO
10. **Posición del clímax**: 0.0-1.0 (recomendado: 0.7)
11. **Título y compositor**: Metadata para la partitura
12. **Guardar archivo**: Opción de guardar como `.ly` ⭐ NUEVO

### Modo Programático

```python
from mainpy import MelodicArchitect, ImpulseType

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
    use_motivic_variations=True,       # ⭐ Activar variaciones motívicas
    variation_probability=0.4,         # 40% de aplicar variación
    climax_position=0.75,              # ⭐ Clímax al 75% (compás 6 de 8)
    climax_intensity=1.5,              # ⭐ 50% más intenso en registro
    max_interval=6,                    # ⭐ Máximo salto: sexta (default)
    use_tenoris=False,                 # ⭐ Usar quinta como nota tenens
    tenoris_probability=0.2            # ⭐ Probabilidad de tenoris (si activado)
)

# Generar y mostrar código LilyPond
print(architect.generate_and_display(
    title="Mi Melodía",
    composer="Compositor"
))
```

### Probar en LilyPond/Frescobaldi

Para visualizar las melodías generadas:

1. **Ejecutar el script principal**:
   ```bash
   python3 mainpy
   ```

2. **Copiar la salida** de uno de los ejemplos (desde `\score {` hasta el último `}`)

3. **Pegar en Frescobaldi/LilyPond** y compilar

El código generado incluye automáticamente:
- `\score { ... }` - Bloque de partitura
- `\language "english"` - Compatibilidad con LilyPond en español
- `\midi {}` - Generación automática de archivo MIDI

**Resultado**: Obtendrás tanto la partitura PDF como un archivo MIDI para reproducción.

### Prueba Rápida

El proyecto incluye un archivo `EJEMPLO_PARA_PROBAR.ly` que puedes abrir directamente en Frescobaldi para verificar que todo funciona correctamente.

## Ejemplos Avanzados

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

## Parámetros de Configuración

| Parámetro | Tipo | Descripción | Valores |
|-----------|------|-------------|---------|
| `key_name` | str | Tonalidad | "C", "D", "Eb", "F#", etc. |
| `mode` | str | Modo musical | "major", "minor", "dorian", "phrygian", "lydian", "mixolydian" |
| `meter_tuple` | tuple | Compás | (4,4), (3,4), (5,8), (7,8), etc. |
| `subdivisions` | list | Subdivisión de amalgama | [2,3], [3,2], [2,2,3], etc. |
| `num_measures` | int | Número de compases | 4, 8, 16, etc. (par recomendado) |
| `impulse_type` | ImpulseType | Tipo de impulso inicial | TETIC, ANACROUSTIC, ACEPHALOUS |
| `infraction_rate` | float | Tasa de infracción | 0.0 (estricto) a 1.0 (muy libre) |
| `rhythmic_complexity` | int | Complejidad rítmica | 1 (simple) a 5 (muy complejo) |
| `use_rests` | bool | Usar silencios estratégicos | True/False (default: True) |
| `rest_probability` | float | Probabilidad de silencio | 0.0 (sin silencios) a 1.0 (máximo) |
| `use_motivic_variations` | bool | ⭐ Usar variaciones motívicas | True/False (default: True) |
| `variation_probability` | float | ⭐ Probabilidad de variación | 0.0 (sin variaciones) a 1.0 (máximo) |
| `climax_position` | float | ⭐ Posición del clímax | 0.0 (inicio) a 1.0 (final), típico: 0.7-0.8 |
| `climax_intensity` | float | ⭐ Intensidad del clímax | 1.0 (normal) a 2.0 (muy intenso) |
| `max_interval` | int | ⭐ Máximo salto melódico | 6 (sexta, default), valores típicos: 4-9 |
| `use_tenoris` | bool | ⭐ Usar tenoris (quinta) | True/False (default: False) |
| `tenoris_probability` | float | ⭐ Probabilidad de tenoris | 0.0 (nunca) a 1.0 (siempre), recomendado: 0.15-0.25 |

## Teoría Musical Implementada

El generador implementa los conceptos descritos en `tarea.md`:

1. **Jerarquía Métrica**: Pulsos fuertes vs. débiles
2. **Inicio del Motivo**: Tético, Anacrúsico, Acéfalo
3. **Notas Estructurales**: Corresponden a acordes implícitos
4. **Notas de Paso**: Movimiento por grado conjunto en tiempos débiles
5. **Contorno Melódico**: Control de rango y dirección
6. **Cadencias**: Semicadencia (antecedente) y auténtica (consecuente)
7. **Progresión Armónica**: I-IV-V-I implícita
8. **Silencios Estratégicos**:
   - Respiraciones al final de semifrases
   - Impulsos anacrúsicos (silencio antes del tiempo fuerte)
   - Silencios acéfalos (silencio en el tiempo fuerte)
   - Silencios decorativos que no interrumpen la continuidad melódica
9. **Variaciones Motívicas**: ⭐ NUEVO
   - Inversión de intervalos
   - Retrogradación (motivo al revés)
   - Aumentación y disminución rítmica
   - Transposición y secuencias
   - Aplicación contextual según el clímax
10. **Clímax Melódico Controlado**: ⭐ NUEVO
     - Posición configurable del punto más alto
     - Aproximación gradual (3 compases antes)
     - Expansión del registro hacia octavas superiores
     - Tracking del registro más alto alcanzado
11. **Restricciones de Saltos**: ⭐ NUEVO
     - Máximo salto: sexta (9 semitonos) configurable
     - Octava permitida solo en clímax estructural
     - Recuperación obligatoria por movimiento contrario
     - Preferencia por grado conjunto (2ª) en recuperación
12. **Ámbito Melódico Controlado**: ⭐ NUEVO
     - Rango: octava de la tónica ± cuarta perfecta
     - Ejemplo C mayor: G3 (C4-P4) hasta F5 (C5+P4)
     - Validación automática de todas las notas generadas
13. **Sistema Tenoris**: ⭐ NUEVO
     - Uso de la quinta (dominante) como "nota tenens"
     - Aplicado en tiempos estructurales (no en paso)
     - Tradición gregoriana: quinta como tono de recitación
     - Configurable con probabilidad ajustable

## Arquitectura del Código

```
MelodicArchitect
├── Capa I: Configuración de la Realidad Musical
│   ├── Escala/Modo (music21)
│   ├── Métrica y subdivisiones
│   ├── Parámetros de control
│   └── Control del clímax melódico ⭐
├── Capa II: Generación del ADN (Motivo y Frase)
│   ├── Patrones rítmicos
│   ├── Selección de tonos (estructurales vs. paso)
│   ├── Variaciones motívicas ⭐
│   │   ├── Inversión
│   │   ├── Retrogradación
│   │   ├── Aumentación/Disminución
│   │   └── Transposición/Secuencia
│   └── Control de contorno melódico con clímax ⭐
└── Capa III: Desarrollo y Cierre (Período y Cadencia)
    ├── Estructura antecedente-consecuente
    ├── Cadencias (semicadencia y auténtica)
    ├── Aproximación al clímax ⭐
    └── Salida en formato Abjad/LilyPond
```

## Cómo Observar las Nuevas Características

### Identificar el Clímax Melódico

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

### Detectar Variaciones Motívicas

Compara los primeros compases con compases posteriores:
- **Inversión**: Mismos intervalos pero dirección opuesta
- **Retrogradación**: Secuencia de notas al revés
- **Secuencia**: Mismo patrón en otro grado
- **Aumentación**: Duraciones dobles (cuartos → medios)
- **Disminución**: Duraciones reducidas (cuartos → octavos)

## Formato de Salida LilyPond

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

## Limitaciones Conocidas

1. Las duraciones complejas (ej: 5/16) se simplifican
2. Tenoris con probabilidad muy alta (>0.3) puede aplanar la melodía
3. La variación motívica (aumentación/disminución) es básica
4. No hay soporte para polifonía o armonización explícita

## Mejoras Futuras

- [x] Implementar variaciones motívicas (inversión, retrogradación) ✅
- [x] Añadir control explícito del clímax melódico ✅
- [x] Restricciones de saltos y recuperación ✅
- [x] Ámbito melódico controlado ✅
- [x] Sistema tenoris (gregoriano) ✅
- [x] Salida a archivo .ly ✅
- [ ] Soporte para articulaciones y dinámicas
- [ ] Generación de acompañamiento armónico
- [ ] Análisis automático de melodías generadas
- [ ] Ornamentación (trinos, mordentes)

## Contribuciones

Este proyecto implementa la teoría musical descrita en `tarea.md`. Para contribuir o reportar problemas, consulte la documentación teórica primero.

## Licencia

Proyecto educativo - uso libre para aprendizaje y experimentación musical.
