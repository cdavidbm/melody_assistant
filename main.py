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
from melody_generator.cli import main as cli_main

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


def main():
    """Punto de entrada principal con seleccion de modo."""
    print("=" * 60)
    print("GENERADOR DE MELODIAS - PROTOCOLO SYMMETRY & LOGIC")
    print("=" * 60)
    print()
    print("Seleccione el modo de ejecucion:")
    print("  1. CLI (Linea de comandos interactiva)")
    print("  2. Web (Interfaz web en navegador)")
    print()

    choice = input("Seleccione modo [1]: ").strip() or "1"

    if choice == "2":
        print()
        print("Iniciando servidor web...")
        print("Abra su navegador en: http://localhost:5000")
        print("Presione Ctrl+C para detener el servidor")
        print()

        try:
            from web.app import app
            app.run(debug=True, port=5000, use_reloader=False)
        except ImportError as e:
            print(f"Error: No se pudo importar Flask. {e}")
            print("Instale Flask con: pip install flask")
        except Exception as e:
            print(f"Error al iniciar servidor web: {e}")
    else:
        cli_main()


if __name__ == "__main__":
    main()
