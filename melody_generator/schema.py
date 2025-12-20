"""
JSON Schema for melody generation input.

All input methods (form, LilyPond idea, text prompt) must converge
to this standard JSON format before being processed by the system.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Literal
import json


@dataclass
class GenerationInput:
    """
    Standard input schema for melody generation.

    This is the canonical format that all input methods must produce.
    The form is the primary user interface, but internally everything
    is converted to this JSON structure.
    """

    # === REQUIRED FIELDS ===
    # Tonal configuration
    key: str = "C"  # C, D, E, F, G, A, B, Db, Eb, Gb, Ab, Bb, C#, F#
    mode: str = "major"  # major, minor, dorian, phrygian, etc.

    # Metric configuration
    meter_num: int = 4
    meter_den: int = 4
    num_measures: int = 8

    # === OPTIONAL FIELDS (with sensible defaults) ===
    # Rhythm
    complexity: int = 2  # 1=simple, 2=moderate, 3=complex
    impulse: str = "tetic"  # tetic, anacroustic, acephalous
    use_rests: bool = True
    rest_probability: float = 0.15

    # Melody
    climax_position: float = 0.65  # 0.0-1.0
    climax_intensity: float = 1.3
    max_interval: int = 6
    infraction_rate: float = 0.05
    use_tenoris: bool = False
    variation_freedom: int = 2  # 1=strict, 2=moderate, 3=free

    # Generation method
    generation_method: str = "traditional"  # traditional, hierarchical, genetic

    # Genetic algorithm options (only if generation_method == "genetic")
    genetic_generations: int = 15
    genetic_population: int = 30
    genetic_markov_polish: bool = True

    # Bass
    add_bass: bool = False
    bass_style: str = "simple"  # simple, alberti, walking, contrapunto
    bass_octave: int = 3

    # Markov chains
    use_markov: bool = False
    markov_composer: str = "bach"  # bach, mozart, beethoven, combined
    markov_weight: float = 0.4
    markov_order: int = 2

    # Expression
    ornamentation_style: str = "none"  # none, minimal, classical, baroque, romantic
    use_dynamics: bool = True
    use_articulations: bool = True
    base_dynamic: str = "mf"
    climax_dynamic: str = "f"

    # Score info
    title: str = "Melodia Generada"
    composer: str = "CompositorIA"

    # === SPECIAL FIELDS (for specific input modes) ===
    # User's musical idea (for "develop" mode)
    user_motif: Optional[str] = None  # LilyPond notation
    user_motif_validated: bool = False  # True if passed MusicXML validation

    # Original prompt (for "prompt" mode)
    original_prompt: Optional[str] = None

    # Input type tracking (determines system flow)
    # - "form": User completed the form (generate from scratch)
    # - "musical_idea": User provided initial notes (preserve and develop)
    # - "prompt": User entered text description (generate from scratch)
    input_type: str = "form"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationInput":
        """Create from dictionary."""
        # Filter only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> "GenerationInput":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def get_defaults(cls) -> "GenerationInput":
        """Get instance with all default values."""
        return cls()

    def merge_with_defaults(self, defaults: Optional["GenerationInput"] = None) -> "GenerationInput":
        """
        Merge this input with defaults, filling missing/None values.
        Useful for partial inputs (like from develop or prompt modes).
        """
        if defaults is None:
            defaults = GenerationInput.get_defaults()

        result_data = defaults.to_dict()

        # Override with non-None values from self
        for key, value in self.to_dict().items():
            if value is not None:
                result_data[key] = value

        return GenerationInput.from_dict(result_data)


# Mode number to mode name mapping (from CLI)
MODE_NUM_TO_NAME = {
    "1": "major",
    "2": "dorian",
    "3": "phrygian",
    "4": "lydian",
    "5": "mixolydian",
    "6": "minor",
    "7": "locrian",
    "8": "harmonic_minor",
    "9": "melodic_minor",
    "10": "locrian_nat6",
    "11": "ionian_aug5",
    "12": "dorian_sharp4",
    "13": "phrygian_dominant",
    "14": "lydian_sharp2",
    "15": "superlocrian_bb7",
    "16": "dorian_flat2",
    "17": "lydian_augmented",
    "18": "lydian_dominant",
    "19": "mixolydian_flat6",
    "20": "locrian_nat2",
    "21": "altered",
}


def form_to_generation_input(form_data: Dict[str, Any]) -> GenerationInput:
    """
    Convert Flask form data to GenerationInput.

    This is the main entry point for form completion.
    If user_motif is provided, input_type becomes "musical_idea" (Case 2).
    Otherwise, input_type is "form" (Case 1 - generate from scratch).
    """
    # Map mode number to name if needed
    mode = form_data.get("mode", "1")
    if mode in MODE_NUM_TO_NAME:
        mode = MODE_NUM_TO_NAME[mode]

    # Check if user provided a motif (optional field)
    user_motif_raw = form_data.get("user_motif", "")
    user_motif = user_motif_raw.strip() if user_motif_raw else None

    # Determine input type based on whether motif was provided
    input_type = "musical_idea" if user_motif else "form"

    return GenerationInput(
        # Tonal
        key=form_data.get("key", "C"),
        mode=mode,

        # Metric
        meter_num=int(form_data.get("meter_num", 4)),
        meter_den=int(form_data.get("meter_den", 4)),
        num_measures=int(form_data.get("num_measures", 8)),

        # Rhythm
        complexity=int(form_data.get("complexity", 2)),
        impulse=form_data.get("impulse", "tetic"),
        use_rests=form_data.get("use_rests") == "on" or form_data.get("use_rests") is True,

        # Melody
        climax_position=float(form_data.get("climax_position", 0.65)),
        variation_freedom=int(form_data.get("variation_freedom", 2)),
        use_tenoris=form_data.get("use_tenoris") == "on" or form_data.get("use_tenoris") is True,

        # Generation method
        generation_method=form_data.get("generation_method", "traditional"),
        genetic_generations=int(form_data.get("genetic_generations", 15)),
        genetic_population=int(form_data.get("genetic_population", 30)),
        genetic_markov_polish=form_data.get("genetic_markov_polish") == "on" or form_data.get("genetic_markov_polish") is True,

        # Bass
        add_bass=form_data.get("add_bass") == "on" or form_data.get("add_bass") is True,
        bass_style=form_data.get("bass_style", "simple"),
        bass_octave=int(form_data.get("bass_octave", 3)),

        # Markov
        use_markov=form_data.get("use_markov") == "on" or form_data.get("use_markov") is True,
        markov_composer=form_data.get("composer", "bach"),
        markov_weight=float(form_data.get("markov_weight", 0.4)),
        markov_order=int(form_data.get("markov_order", 2)),

        # Expression
        ornamentation_style=form_data.get("ornamentation_style", "none"),
        use_dynamics=form_data.get("use_dynamics") == "on" or form_data.get("use_dynamics") is True,
        use_articulations=form_data.get("use_articulations") == "on" or form_data.get("use_articulations") is True,
        base_dynamic=form_data.get("base_dynamic", "mf"),
        climax_dynamic=form_data.get("climax_dynamic", "f"),

        # Score info
        title=form_data.get("title", "Melodia Generada"),
        composer=form_data.get("score_composer", "CompositorIA"),

        # User's musical idea (optional)
        user_motif=user_motif,

        # Input type: "musical_idea" if motif provided, "form" otherwise
        input_type=input_type,
    )


def develop_form_to_generation_input(form_data: Dict[str, Any]) -> GenerationInput:
    """
    Convert develop mode form data to GenerationInput.

    This is for Case 2 (user provides musical idea).
    Required fields: key, meter, num_measures, user_motif
    """
    # Map mode number to name if needed
    mode = form_data.get("dev_mode", "1")
    if mode in MODE_NUM_TO_NAME:
        mode = MODE_NUM_TO_NAME[mode]

    # Start with defaults
    gen_input = GenerationInput.get_defaults()

    # Override with provided values
    gen_input.key = form_data.get("dev_key", "C")
    gen_input.mode = mode
    gen_input.meter_num = int(form_data.get("dev_meter_num", 4))
    gen_input.meter_den = int(form_data.get("dev_meter_den", 4))
    gen_input.num_measures = int(form_data.get("dev_num_measures", 8))

    # User's musical idea (required)
    gen_input.user_motif = form_data.get("user_motif", "").strip()

    # Optional fields that might be provided
    if "dev_variation_intensity" in form_data:
        gen_input.variation_freedom = int(form_data.get("dev_variation_intensity", 2))

    if form_data.get("dev_add_bass") == "on":
        gen_input.add_bass = True
        gen_input.bass_style = form_data.get("dev_bass_style", "simple")

    # Score info
    gen_input.title = form_data.get("dev_title", "Desarrollo de Idea")
    gen_input.composer = form_data.get("dev_composer", "CompositorIA")

    # Input type: musical_idea means preserve and develop user's motif
    gen_input.input_type = "musical_idea"

    return gen_input


def prompt_response_to_generation_input(
    llm_response: Dict[str, Any],
    original_prompt: str,
    title: str = "Melodia Generada",
    composer: str = "CompositorIA"
) -> GenerationInput:
    """
    Convert LLM response to GenerationInput.

    This is for Case 3 (user provides text prompt).
    The LLM extracts parameters from natural language.
    """
    # Map mode number to name if needed
    mode = llm_response.get("mode", "1")
    if mode in MODE_NUM_TO_NAME:
        mode = MODE_NUM_TO_NAME[mode]

    return GenerationInput(
        # Tonal
        key=llm_response.get("key", "C"),
        mode=mode,

        # Metric
        meter_num=int(llm_response.get("meter_num", 4)),
        meter_den=int(llm_response.get("meter_den", 4)),
        num_measures=int(llm_response.get("num_measures", 8)),

        # Rhythm
        complexity=int(llm_response.get("complexity", 2)),
        impulse=llm_response.get("impulse", "tetic"),
        use_rests=llm_response.get("use_rests", True),

        # Melody
        climax_position=float(llm_response.get("climax_position", 0.65)),
        variation_freedom=int(llm_response.get("variation_freedom", 2)),

        # Generation method
        generation_method=llm_response.get("generation_method", "traditional"),

        # Bass
        add_bass=llm_response.get("add_bass", False),
        bass_style=llm_response.get("bass_style", "simple"),

        # Markov
        use_markov=llm_response.get("use_markov", False),
        markov_composer=llm_response.get("composer", "bach"),

        # Expression
        ornamentation_style=llm_response.get("ornamentation_style", "none"),
        use_dynamics=llm_response.get("use_dynamics", True),
        use_articulations=llm_response.get("use_articulations", True),

        # Score info
        title=title,
        composer=composer,

        # Original prompt
        original_prompt=original_prompt,

        # Input type: prompt means generate from scratch based on AI interpretation
        input_type="prompt",
    )
