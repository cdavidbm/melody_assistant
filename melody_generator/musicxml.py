"""
Exportador MusicXML para validación con music21.

Crea archivos MusicXML temporales que music21 puede analizar,
permitiendo validación detallada antes de generar la partitura final.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime

import abjad
from music21 import converter, stream

from .converters import AbjadMusic21Converter


class MusicXMLExporter:
    """
    Exporta staffs de Abjad a MusicXML para validación.

    El archivo MusicXML es temporal y se elimina después de la validación.
    Se guarda en la carpeta output/ como cache temporal.
    """

    DEFAULT_OUTPUT_DIR = "output"
    TEMP_PREFIX = "temp_validation_"

    def __init__(self, output_dir: Optional[str] = None):
        """
        Inicializa el exportador.

        Args:
            output_dir: Directorio para archivos temporales (default: output/)
        """
        self.output_dir = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._temp_files: list = []

    def export_for_validation(
        self,
        staff: abjad.Staff,
        key_name: str,
        mode: str,
        meter_tuple: Tuple[int, int],
        title: Optional[str] = None,
    ) -> str:
        """
        Exporta un staff a MusicXML temporal para validación.

        Args:
            staff: Staff de Abjad a exportar
            key_name: Tonalidad (ej: "C", "G", "F#")
            mode: Modo (ej: "major", "minor", "dorian")
            meter_tuple: Compás (ej: (4, 4))
            title: Título opcional

        Returns:
            Ruta del archivo MusicXML creado
        """
        # Convertir a music21
        score = AbjadMusic21Converter.abjad_staff_to_music21_score(
            staff=staff,
            key_name=key_name,
            mode=mode,
            meter_tuple=meter_tuple,
        )

        # Añadir metadatos
        if title:
            score.metadata = stream.metadata.Metadata()
            score.metadata.title = title

        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.TEMP_PREFIX}{timestamp}.xml"
        filepath = self.output_dir / filename

        # Exportar a MusicXML
        score.write('musicxml', fp=str(filepath))

        # Registrar para limpieza posterior
        self._temp_files.append(filepath)

        return str(filepath)

    def load_for_analysis(self, filepath: str) -> stream.Score:
        """
        Carga un archivo MusicXML para análisis con music21.

        Args:
            filepath: Ruta del archivo MusicXML

        Returns:
            Score de music21 listo para análisis
        """
        return converter.parse(filepath)

    def cleanup(self, filepath: Optional[str] = None):
        """
        Elimina archivos temporales de validación.

        Args:
            filepath: Archivo específico a eliminar.
                     Si es None, elimina todos los archivos temporales.
        """
        if filepath:
            path = Path(filepath)
            if path.exists() and path.name.startswith(self.TEMP_PREFIX):
                path.unlink()
                if path in self._temp_files:
                    self._temp_files.remove(path)
        else:
            # Eliminar todos los archivos temporales registrados
            for temp_path in self._temp_files[:]:
                if temp_path.exists():
                    temp_path.unlink()
                self._temp_files.remove(temp_path)

    def cleanup_all_temp_files(self):
        """
        Elimina TODOS los archivos temporales de validación en output/.

        Útil para limpiar archivos huérfanos de ejecuciones anteriores.
        """
        for filepath in self.output_dir.glob(f"{self.TEMP_PREFIX}*.xml"):
            filepath.unlink()
        self._temp_files.clear()

    def get_temp_files(self) -> list:
        """Obtiene lista de archivos temporales pendientes de limpieza."""
        return [str(f) for f in self._temp_files if f.exists()]

    def __enter__(self):
        """Context manager: inicio."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: limpieza automática al salir."""
        self.cleanup()
        return False


def export_staff_to_musicxml(
    staff: abjad.Staff,
    key_name: str,
    mode: str,
    meter_tuple: Tuple[int, int],
    output_dir: Optional[str] = None,
) -> str:
    """
    Función de conveniencia para exportar un staff a MusicXML.

    Args:
        staff: Staff de Abjad
        key_name: Tonalidad
        mode: Modo
        meter_tuple: Compás
        output_dir: Directorio de salida (default: output/)

    Returns:
        Ruta del archivo MusicXML creado
    """
    exporter = MusicXMLExporter(output_dir=output_dir)
    return exporter.export_for_validation(
        staff=staff,
        key_name=key_name,
        mode=mode,
        meter_tuple=meter_tuple,
    )


def load_musicxml_for_analysis(filepath: str) -> stream.Score:
    """
    Función de conveniencia para cargar MusicXML para análisis.

    Args:
        filepath: Ruta del archivo MusicXML

    Returns:
        Score de music21
    """
    return converter.parse(filepath)


def cleanup_temp_musicxml(filepath: str):
    """
    Función de conveniencia para eliminar un archivo temporal.

    Args:
        filepath: Ruta del archivo a eliminar
    """
    path = Path(filepath)
    if path.exists() and MusicXMLExporter.TEMP_PREFIX in path.name:
        path.unlink()
