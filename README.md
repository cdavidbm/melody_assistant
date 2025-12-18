# Generador de Melodias Clasicas

Generador de melodias basado en teoria musical clasica. Produce codigo LilyPond con soporte para 21 modos musicales, metricas regulares y amalgama.

## Instalacion

```bash
pip install abjad music21 flask
```

Requisito opcional para renderizar partituras: [LilyPond](https://lilypond.org/)

## Uso

```bash
python3 main.py
```

El programa ofrece dos modos de ejecucion:

### Modo CLI (Linea de comandos)

Menu interactivo que guia paso a paso la configuracion:
- Tonalidad y modo (21 modos disponibles)
- Compas y numero de compases
- Complejidad ritmica
- Tipo de impulso (tetico, anacrusico, acefalo)
- Opciones avanzadas (Markov, validacion, etc.)

### Modo Web

Interfaz web con formulario visual:
- Acceder en `http://localhost:5000`
- Visualizador PDF integrado
- Reproductor MIDI
- Descarga de archivos .ly, .pdf, .midi

## Uso Programatico

```python
from melody_generator import MelodicArchitect, ImpulseType

architect = MelodicArchitect(
    key_name="C",
    mode="major",
    meter_tuple=(4, 4),
    num_measures=8,
    impulse_type=ImpulseType.TETIC,
)

# Metodo tradicional
print(architect.generate_and_display(title="Mi Melodia"))

# Metodo jerarquico
staff = architect.generate_period_hierarchical()
print(architect.format_as_lilypond(staff, title="Mi Melodia"))
```

## Modos Musicales Soportados

| Categoria | Modos |
|-----------|-------|
| Diatonicos | major, dorian, phrygian, lydian, mixolydian, minor, locrian |
| Menores | harmonic_minor, melodic_minor |
| Menor armonica | locrian_nat6, ionian_aug5, dorian_sharp4, phrygian_dominant, lydian_sharp2, superlocrian_bb7 |
| Menor melodica | dorian_flat2, lydian_augmented, lydian_dominant, mixolydian_flat6, locrian_nat2, altered |

## Metodos de Generacion

| Metodo | Descripcion |
|--------|-------------|
| **Tradicional** | Cohesion ritmica mediante motivo unico reutilizado |
| **Jerarquico** | Jerarquia formal: Motivo -> Frase -> Periodo |

## Caracteristicas

- 21 modos musicales
- Metricas simples, compuestas y amalgama (5/8, 7/8, 11/8)
- Cadencias autenticas y semicadencias
- Variaciones motivicas (inversion, retrogradacion, aumentacion, etc.)
- Control de climax melodico
- Sistema de validacion musical
- Cadenas de Markov opcionales (Bach, Mozart, Beethoven)
- Salida LilyPond con PDF y MIDI

## Estructura del Proyecto

```
melody_generator/     # Paquete principal (17 modulos)
web/                  # Interfaz web Flask
models/               # Modelos Markov pre-entrenados
output/               # Archivos generados
scripts/              # Utilidades (entrenamiento Markov)
```

## Documentacion

- **[bases_teoricas.md](bases_teoricas.md)**: Reglas de teoria musical implementadas
- **[CLAUDE.md](CLAUDE.md)**: Guia para desarrollo con IA

## Dependencias

| Paquete | Uso |
|---------|-----|
| music21 | Logica musical, escalas, intervalos |
| abjad | Generacion de codigo LilyPond |
| flask | Interfaz web |

## Licencia

Proyecto educativo - uso libre para aprendizaje y experimentacion musical.
