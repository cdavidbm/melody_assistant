"""
Gestión de escalas y modos musicales.
Soporta 21 modos: diatónicos, menores, y modos derivados de menor armónica/melódica.
"""

from typing import List, Optional, Tuple
from music21 import key, pitch, interval, scale


def create_modal_scale(tonic_name: str, mode_type: str, mode_number: int = 1):
    """
    Crea una escala modal derivada de menor armónica o menor melódica.

    Args:
        tonic_name: Nombre de la tónica (ej: 'C', 'D', 'F#')
        mode_type: Tipo de modo base ('harmonic_minor' o 'melodic_minor')
        mode_number: Número del modo (1-7)

    Returns:
        ConcreteScale con los pitches del modo derivado
    """
    if mode_type == "harmonic_minor":
        base_scale = scale.HarmonicMinorScale(tonic_name)
    elif mode_type == "melodic_minor":
        base_scale = scale.MelodicMinorScale(tonic_name)
    else:
        raise ValueError(f"Tipo de modo no válido: {mode_type}")

    base_pitches = base_scale.pitches[:7]
    rotation = mode_number - 1
    rotated_pitches = base_pitches[rotation:] + base_pitches[:rotation]

    target_tonic = pitch.Pitch(tonic_name + "4")
    source_tonic = rotated_pitches[0]
    transp_interval = interval.Interval(noteStart=source_tonic, noteEnd=target_tonic)
    modal_pitches = [transp_interval.transposePitch(p) for p in rotated_pitches]
    modal_pitches.append(modal_pitches[0].transpose("P8"))

    return scale.ConcreteScale(pitches=modal_pitches)


# Mapeo de nombres de modo a configuraciones
MODE_CONFIG = {
    # Modos diatónicos (de escala mayor)
    "major": {"type": "diatonic", "scale_class": scale.MajorScale},
    "dorian": {"type": "diatonic", "scale_class": scale.DorianScale},
    "phrygian": {"type": "diatonic", "scale_class": scale.PhrygianScale},
    "lydian": {"type": "diatonic", "scale_class": scale.LydianScale},
    "mixolydian": {"type": "diatonic", "scale_class": scale.MixolydianScale},
    "minor": {"type": "diatonic", "scale_class": scale.MinorScale},
    "locrian": {"type": "diatonic", "scale_class": scale.LocrianScale},
    # Escalas menores
    "harmonic_minor": {"type": "diatonic", "scale_class": scale.HarmonicMinorScale},
    "melodic_minor": {"type": "diatonic", "scale_class": scale.MelodicMinorScale},
    # Modos de menor armónica
    "locrian_nat6": {"type": "harmonic_minor", "mode_number": 2},
    "ionian_aug5": {"type": "harmonic_minor", "mode_number": 3},
    "dorian_sharp4": {"type": "harmonic_minor", "mode_number": 4},
    "phrygian_dominant": {"type": "harmonic_minor", "mode_number": 5},
    "lydian_sharp2": {"type": "harmonic_minor", "mode_number": 6},
    "superlocrian_bb7": {"type": "harmonic_minor", "mode_number": 7},
    # Modos de menor melódica
    "dorian_flat2": {"type": "melodic_minor", "mode_number": 2},
    "lydian_augmented": {"type": "melodic_minor", "mode_number": 3},
    "lydian_dominant": {"type": "melodic_minor", "mode_number": 4},
    "mixolydian_flat6": {"type": "melodic_minor", "mode_number": 5},
    "locrian_nat2": {"type": "melodic_minor", "mode_number": 6},
    "altered": {"type": "melodic_minor", "mode_number": 7},
}


class ScaleManager:
    """
    Gestiona la configuración y operaciones sobre escalas musicales.
    """

    def __init__(self, key_name: str, mode: str):
        """
        Inicializa el gestor de escala.

        Args:
            key_name: Nombre de la tonalidad (ej: "C", "D", "Eb")
            mode: Modo musical (uno de los 21 soportados)
        """
        self.key_name = key_name
        self.mode = mode
        self.key_obj = (
            key.Key(key_name) if mode == "major" else key.Key(key_name, mode="minor")
        )
        self.scale = self._create_scale()
        self._setup_melodic_range()

    def _create_scale(self):
        """Crea el objeto escala según el modo configurado."""
        config = MODE_CONFIG.get(self.mode)

        if config is None:
            return scale.MajorScale(self.key_name)

        if config["type"] == "diatonic":
            return config["scale_class"](self.key_name)
        elif config["type"] == "harmonic_minor":
            return create_modal_scale(
                self.key_name, "harmonic_minor", config["mode_number"]
            )
        elif config["type"] == "melodic_minor":
            return create_modal_scale(
                self.key_name, "melodic_minor", config["mode_number"]
            )

        return scale.MajorScale(self.key_name)

    def _setup_melodic_range(self):
        """Configura el ámbito melódico: octava de la tónica ± cuarta."""
        tonic_pitch = self.key_obj.tonic
        tonic_base = pitch.Pitch(f"{tonic_pitch.name}4")
        self.melodic_range_bottom = tonic_base.transpose("-P4")
        self.melodic_range_top = tonic_base.transpose("P8").transpose("P4")

    def get_pitch_by_degree(self, degree: int, octave: int = 4) -> str:
        """
        Retorna una nota de la escala por su grado (1-7).

        Args:
            degree: Grado de la escala (1-7)
            octave: Octava de la nota

        Returns:
            String con el pitch (ej: "c4", "d#5")
        """
        p = self.scale.pitchFromDegree(degree)
        return f"{p.name.lower().replace('-', 'b')}{octave}"

    def pitch_to_degree(self, pitch_str: str) -> int:
        """Convierte un pitch string a grado de escala."""
        p = pitch.Pitch(pitch_str)
        for deg in range(1, 8):
            scale_pitch = self.scale.pitchFromDegree(deg)
            if p.name == scale_pitch.name:
                return deg
        return 1

    def is_chord_tone(self, degree: int) -> bool:
        """Determina si un grado es nota del acorde tónico (I, III, V)."""
        return degree in [1, 3, 5]

    def is_tendency_tone(self, degree: int) -> bool:
        """Determina si un grado es nota de tendencia (VII, IV)."""
        return degree in [7, 4]

    def is_in_range(self, pitch_obj) -> bool:
        """Verifica si un pitch está dentro del ámbito melódico permitido."""
        return self.melodic_range_bottom.ps <= pitch_obj.ps <= self.melodic_range_top.ps

    def get_tonic(self):
        """Retorna el objeto tónica de la tonalidad."""
        return self.key_obj.tonic

    def get_scale_pitches(self) -> List[str]:
        """
        Retorna una lista de nombres de pitches de la escala (sin octava).

        Returns:
            Lista de nombres de notas (ej: ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
        """
        return [p.name for p in self.scale.pitches[:7]]
