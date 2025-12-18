"""
Factories y loaders para el generador de melodías.
Centraliza la lógica de carga de modelos y recursos.
"""

from pathlib import Path
from typing import Optional, Tuple

from .config import MarkovConfig
from .markov import MelodicMarkovModel, RhythmicMarkovModel


class MarkovModelLoader:
    """
    Factory para cargar modelos Markov pre-entrenados.

    Centraliza la lógica de carga que antes estaba en MelodicArchitect.__init__,
    siguiendo el principio de Single Responsibility (SRP).
    """

    # Directorio base de modelos (relativo al paquete)
    MODELS_DIR = Path(__file__).parent.parent / "models"

    @classmethod
    def load_melodic_model(
        cls, config: MarkovConfig
    ) -> Optional[MelodicMarkovModel]:
        """
        Carga un modelo melódico pre-entrenado.

        Args:
            config: Configuración de Markov

        Returns:
            MelodicMarkovModel cargado, o None si falla
        """
        if not config.enabled:
            return None

        model_path = (
            cls.MODELS_DIR
            / "melody_markov"
            / f"{config.composer}_intervals.json"
        )

        if not model_path.exists():
            print(
                f"⚠️  Modelo melódico de {config.composer} no encontrado en {model_path}"
            )
            return None

        try:
            model = MelodicMarkovModel(order=config.order, composer=config.composer)
            model.chain.load(str(model_path))
            return model
        except Exception as e:
            print(f"⚠️  No se pudo cargar modelo melódico de {config.composer}: {e}")
            return None

    @classmethod
    def load_rhythmic_model(
        cls, config: MarkovConfig
    ) -> Optional[RhythmicMarkovModel]:
        """
        Carga un modelo rítmico pre-entrenado.

        Args:
            config: Configuración de Markov

        Returns:
            RhythmicMarkovModel cargado, o None si falla
        """
        if not config.enabled:
            return None

        model_path = (
            cls.MODELS_DIR
            / "rhythm_markov"
            / f"{config.composer}_rhythms.json"
        )

        if not model_path.exists():
            print(
                f"⚠️  Modelo rítmico de {config.composer} no encontrado en {model_path}"
            )
            return None

        try:
            model = RhythmicMarkovModel(order=config.order, composer=config.composer)
            model.chain.load(str(model_path))
            return model
        except Exception as e:
            print(f"⚠️  No se pudo cargar modelo rítmico de {config.composer}: {e}")
            return None

    @classmethod
    def load_all(
        cls, config: MarkovConfig
    ) -> Tuple[Optional[MelodicMarkovModel], Optional[RhythmicMarkovModel]]:
        """
        Carga ambos modelos (melódico y rítmico).

        Args:
            config: Configuración de Markov

        Returns:
            Tupla (modelo_melódico, modelo_rítmico)
        """
        melodic = cls.load_melodic_model(config)
        rhythmic = cls.load_rhythmic_model(config)
        return melodic, rhythmic

    @classmethod
    def get_available_composers(cls) -> list:
        """
        Lista los compositores con modelos disponibles.

        Returns:
            Lista de nombres de compositores
        """
        composers = set()

        melody_dir = cls.MODELS_DIR / "melody_markov"
        if melody_dir.exists():
            for f in melody_dir.glob("*_intervals.json"):
                composer = f.stem.replace("_intervals", "")
                composers.add(composer)

        rhythm_dir = cls.MODELS_DIR / "rhythm_markov"
        if rhythm_dir.exists():
            for f in rhythm_dir.glob("*_rhythms.json"):
                composer = f.stem.replace("_rhythms", "")
                composers.add(composer)

        return sorted(composers)

    @classmethod
    def models_exist(cls, composer: str) -> Tuple[bool, bool]:
        """
        Verifica si existen modelos para un compositor.

        Args:
            composer: Nombre del compositor

        Returns:
            Tupla (existe_melódico, existe_rítmico)
        """
        melody_exists = (
            cls.MODELS_DIR / "melody_markov" / f"{composer}_intervals.json"
        ).exists()
        rhythm_exists = (
            cls.MODELS_DIR / "rhythm_markov" / f"{composer}_rhythms.json"
        ).exists()
        return melody_exists, rhythm_exists
