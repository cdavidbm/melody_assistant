"""
Generador de Melodías según Teoría Musical Clásica
Implementa el "Protocolo Symmetry & Logic"

Este archivo es un wrapper para mantener compatibilidad hacia atrás.
El código ha sido modularizado en el paquete 'melody_generator/'.

Uso:
    python main.py                    # Ejecutar CLI interactivo
    python -m melody_generator        # Ejecutar como módulo

API programática:
    from melody_generator import MelodicArchitect, ImpulseType

    architect = MelodicArchitect(
        key_name="C",
        mode="major",
        meter_tuple=(4, 4),
        num_measures=8,
    )
    print(architect.generate_and_display(title="Mi Melodía"))
"""

# Re-exportar clases principales para compatibilidad
from melody_generator import (
    MelodicArchitect,
    ImpulseType,
    NoteFunction,
    MotivicVariation,
    RhythmicPattern,
    Motif,
    MelodicContour,
    HarmonicFunction,
    Phrase,
    Semiphrase,
    Period,
)
from melody_generator.cli import main

# Mantener compatibilidad con imports existentes
__all__ = [
    "MelodicArchitect",
    "ImpulseType",
    "NoteFunction",
    "MotivicVariation",
    "RhythmicPattern",
    "Motif",
    "MelodicContour",
    "HarmonicFunction",
    "Phrase",
    "Semiphrase",
    "Period",
    "main",
]

if __name__ == "__main__":
    main()
