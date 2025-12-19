"""
Flask application for the melody generator web interface.
"""

import os
import random
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from melody_generator import MelodicArchitect, GenerationConfig, ExpressionConfig
from melody_generator.config import (
    TonalConfig,
    MeterConfig,
    RhythmConfig,
    MelodyConfig,
    MotifConfig,
    MarkovConfig,
)
from melody_generator.models import ImpulseType
from melody_generator.cli import MODE_MAP, COMPOSER_MAP
from melody_generator.ornamentation import OrnamentStyle
from melody_generator.bass import BassStyle, BassConfig

app = Flask(__name__)

# Directory for output files
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# Available options for the form
KEYS = ["C", "D", "E", "F", "G", "A", "B", "Db", "Eb", "Gb", "Ab", "Bb", "C#", "F#"]
METERS = [(4, 4), (3, 4), (2, 4), (6, 8), (9, 8), (12, 8), (5, 4), (7, 8)]
MEASURE_OPTIONS = [4, 8, 12, 16]
COMPLEXITY_OPTIONS = [1, 2, 3]
IMPULSE_OPTIONS = [
    ("tetic", "Tético (comienza en tiempo fuerte)"),
    ("anacroustic", "Anacrúsico (comienza antes del tiempo fuerte)"),
    ("acephalous", "Acéfalo (comienza después del tiempo fuerte)"),
]
COMPOSERS = [
    ("bach", "Bach (estilo contrapuntístico)"),
    ("mozart", "Mozart (estilo clásico elegante)"),
    ("beethoven", "Beethoven (estilo dramático)"),
    ("combined", "Combinado (mezcla de estilos)"),
]
ORNAMENTATION_STYLES = [
    ("none", "Sin ornamentos"),
    ("minimal", "Mínimo (solo esenciales)"),
    ("classical", "Clásico (moderado)"),
    ("baroque", "Barroco (muchos ornamentos)"),
    ("romantic", "Romántico (expresivo)"),
]
DYNAMIC_LEVELS = [
    ("pp", "Pianissimo (pp)"),
    ("p", "Piano (p)"),
    ("mp", "Mezzo piano (mp)"),
    ("mf", "Mezzo forte (mf)"),
    ("f", "Forte (f)"),
    ("ff", "Fortissimo (ff)"),
]
GENERATION_METHODS = [
    ("traditional", "Tradicional (cohesion ritmica)"),
    ("hierarchical", "Jerarquico (Motivo - Frase - Periodo)"),
    ("genetic", "Genetico (Evolucion de motivos con DEAP)"),
]
BASS_STYLES = [
    ("simple", "Simple (una nota por compas)"),
    ("alberti", "Alberti (arpegio clasico)"),
    ("walking", "Walking (movimiento diatonico)"),
    ("contrapunto", "Contrapunto (linea melodica independiente)"),
]
MARKOV_ORDERS = [
    (1, "1 (menos contexto)"),
    (2, "2 (recomendado)"),
    (3, "3 (maximo contexto)"),
]


def get_random_defaults():
    """Generate random default values for the form."""
    return {
        "key": random.choice(["C", "D", "E", "F", "G", "A", "B"]),
        "mode": random.choice(["1", "2", "5", "6", "8", "13"]),  # Common modes
        "meter_num": random.choice([4, 3, 6]),
        "meter_den": random.choice([4, 8]),
        "num_measures": random.choice([4, 8]),
        "complexity": random.choice([1, 2]),
        "impulse": random.choice(["tetic", "anacroustic"]),
        "use_rests": random.choice([True, False]),
        "use_tenoris": False,
        "use_markov": False,
        "composer": "bach",
        "markov_weight": 0.3,
        "markov_order": 2,
        "climax_position": round(random.uniform(0.6, 0.8), 2),
        "variation_freedom": random.choice([1, 2, 3]),
        # Generation method
        "generation_method": "traditional",
        # Genetic options
        "genetic_generations": 15,
        "genetic_population": 30,
        "genetic_markov_polish": True,
        # Bass options (independent)
        "add_bass": False,
        "bass_style": "simple",
        "bass_octave": 3,
        # Expression options
        "ornamentation_style": "none",
        "use_dynamics": True,
        "base_dynamic": "mf",
        "climax_dynamic": "f",
        "use_articulations": True,
        "title": random.choice([
            "Melodía en el Bosque",
            "Danza del Atardecer",
            "Serenata Nocturna",
            "Vals de Primavera",
            "Canción del Río",
            "Elegía",
            "Impromptu",
        ]),
        "score_composer": "MelodicArchitect AI",
    }


@app.route("/")
def index():
    """Render the main form with random defaults."""
    defaults = get_random_defaults()
    return render_template(
        "form.html",
        defaults=defaults,
        mode_map=MODE_MAP,
        keys=KEYS,
        meters=METERS,
        measure_options=MEASURE_OPTIONS,
        complexity_options=COMPLEXITY_OPTIONS,
        impulse_options=IMPULSE_OPTIONS,
        composers=COMPOSERS,
        ornamentation_styles=ORNAMENTATION_STYLES,
        dynamic_levels=DYNAMIC_LEVELS,
        generation_methods=GENERATION_METHODS,
        bass_styles=BASS_STYLES,
        markov_orders=MARKOV_ORDERS,
    )


@app.route("/generate", methods=["POST"])
def generate():
    """Generate a melody based on form data."""
    try:
        # Check generation mode
        generation_mode = request.form.get("generation_mode", "spontaneous")

        if generation_mode == "develop":
            return generate_develop_mode()

        # Parse form data (spontaneous mode)
        key_name = request.form.get("key", "C")
        mode = MODE_MAP.get(request.form.get("mode", "1"), "major")
        meter_num = int(request.form.get("meter_num", 4))
        meter_den = int(request.form.get("meter_den", 4))
        num_measures = int(request.form.get("num_measures", 8))
        complexity = int(request.form.get("complexity", 2))
        impulse_str = request.form.get("impulse", "tetic")
        use_rests = request.form.get("use_rests") == "on"
        use_tenoris = request.form.get("use_tenoris") == "on"
        use_markov = request.form.get("use_markov") == "on"
        composer = request.form.get("composer", "bach")
        markov_weight = float(request.form.get("markov_weight", 0.5))
        markov_order = int(request.form.get("markov_order", 2))
        climax_position = float(request.form.get("climax_position", 0.75))
        variation_freedom = int(request.form.get("variation_freedom", 2))
        title = request.form.get("title", "Melodía Generada")
        score_composer = request.form.get("score_composer", "MelodicArchitect AI")
        generation_method = request.form.get("generation_method", "traditional")

        # Parse genetic options
        genetic_generations = int(request.form.get("genetic_generations", 15))
        genetic_population = int(request.form.get("genetic_population", 30))
        genetic_markov_polish = request.form.get("genetic_markov_polish") == "on"

        # Parse bass options (independent checkbox)
        add_bass = request.form.get("add_bass") == "on"
        bass_style_str = request.form.get("bass_style", "simple")
        bass_octave = int(request.form.get("bass_octave", 3))

        # Parse expression options
        ornamentation_style = request.form.get("ornamentation_style", "none")
        use_dynamics = request.form.get("use_dynamics") == "on"
        base_dynamic = request.form.get("base_dynamic", "mf")
        climax_dynamic = request.form.get("climax_dynamic", "f")
        use_articulations = request.form.get("use_articulations") == "on"

        # Map impulse type
        impulse_map = {
            "tetic": ImpulseType.TETIC,
            "anacroustic": ImpulseType.ANACROUSTIC,
            "acephalous": ImpulseType.ACEPHALOUS,
        }
        impulse_type = impulse_map.get(impulse_str, ImpulseType.TETIC)

        # Map bass style
        bass_style_map = {
            "simple": BassStyle.SIMPLE,
            "alberti": BassStyle.ALBERTI,
            "walking": BassStyle.WALKING,
            "contrapunto": BassStyle.CONTRAPUNTO,
        }
        bass_style = bass_style_map.get(bass_style_str, BassStyle.SIMPLE)

        # Create configuration
        config = GenerationConfig(
            tonal=TonalConfig(key_name=key_name, mode=mode),
            meter=MeterConfig(
                meter_tuple=(meter_num, meter_den),
                num_measures=num_measures,
            ),
            rhythm=RhythmConfig(
                complexity=complexity,
                use_rests=use_rests,
                rest_probability=0.15,
            ),
            melody=MelodyConfig(
                impulse_type=impulse_type,
                climax_position=climax_position,
                climax_intensity=1.5,
                max_interval=6,
                infraction_rate=0.1,
                use_tenoris=use_tenoris,
                tenoris_probability=0.2,
            ),
            motif=MotifConfig(
                use_motivic_variations=True,
                variation_probability=0.4,
                variation_freedom=variation_freedom,
            ),
            markov=MarkovConfig(
                enabled=use_markov,
                composer=composer,
                weight=markov_weight,
                order=markov_order,
            ),
        )

        # Create expression config
        expression_config = ExpressionConfig(
            use_ornamentation=(ornamentation_style != "none"),
            ornamentation_style=ornamentation_style if ornamentation_style != "none" else "classical",
            use_dynamics=use_dynamics,
            base_dynamic=base_dynamic,
            climax_dynamic=climax_dynamic,
            use_articulations=use_articulations,
        )

        # Generate melody
        architect = MelodicArchitect(config=config, expression_config=expression_config)
        lilypond_code = None

        # Step 1: Generate melody with chosen method
        if generation_method == "genetic":
            staff = architect.generate_period_genetic(
                generations=genetic_generations,
                population_size=genetic_population,
                use_markov_polish=genetic_markov_polish,
            )
        elif generation_method == "hierarchical":
            result = architect.generate_period_hierarchical()
            staff = result[0] if isinstance(result, tuple) else result
        else:  # traditional
            staff = architect.generate_period()

        # Step 2: Add bass if requested (can combine with any method)
        if add_bass:
            bass_config = BassConfig(
                style=bass_style,
                octave=bass_octave,
            )
            lilypond_code = architect.generate_period_with_bass(
                bass_style=bass_style,
                bass_config=bass_config,
                return_staffs=False,
            )

        # Apply expression if any expression option is enabled
        if expression_config.use_ornamentation or expression_config.use_dynamics or expression_config.use_articulations:
            staff = architect.apply_expression(staff)

        # Format as LilyPond (if not already generated with bass)
        if lilypond_code is None:
            lilypond_code = architect.format_as_lilypond(
                staff,
                title=title,
                composer=score_composer,
            )
        else:
            # Add header to bass lilypond code
            header_code = ""
            if title or score_composer:
                header_code = "\\header {\n"
                if title:
                    header_code += f'  title = "{title}"\n'
                if score_composer:
                    header_code += f'  composer = "{score_composer}"\n'
                header_code += "}\n\n"
            lilypond_code = header_code + lilypond_code

        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"melody_{key_name}_{mode}_{timestamp}"
        ly_filepath = OUTPUT_DIR / f"{base_filename}.ly"

        with open(ly_filepath, "w", encoding="utf-8") as f:
            f.write(lilypond_code)

        # Run LilyPond to generate PDF and MIDI
        pdf_path = None
        midi_path = None
        lilypond_error = None

        try:
            result = subprocess.run(
                [
                    "lilypond",
                    "-dno-point-and-click",
                    f"--output={OUTPUT_DIR / base_filename}",
                    str(ly_filepath),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Check if files were created
            potential_pdf = OUTPUT_DIR / f"{base_filename}.pdf"
            potential_midi = OUTPUT_DIR / f"{base_filename}.midi"

            if potential_pdf.exists():
                pdf_path = f"{base_filename}.pdf"
            if potential_midi.exists():
                midi_path = f"{base_filename}.midi"

            if result.returncode != 0:
                lilypond_error = result.stderr

        except subprocess.TimeoutExpired:
            lilypond_error = "LilyPond timed out after 60 seconds"
        except FileNotFoundError:
            lilypond_error = "LilyPond not found. Please install LilyPond."

        return render_template(
            "result.html",
            success=True,
            lilypond_code=lilypond_code,
            pdf_path=pdf_path,
            midi_path=midi_path,
            ly_filename=f"{base_filename}.ly",
            lilypond_error=lilypond_error,
            key_name=key_name,
            mode=mode,
            meter=f"{meter_num}/{meter_den}",
            num_measures=num_measures,
        )

    except Exception as e:
        return render_template(
            "result.html",
            success=False,
            error=str(e),
        )


def generate_develop_mode():
    """Generate a melody by developing user-provided motif."""
    try:
        # Parse develop mode form data
        user_motif = request.form.get("user_motif", "").strip()
        num_measures = int(request.form.get("dev_num_measures", 8))
        variation_intensity = int(request.form.get("dev_variation_intensity", 2))
        meter_num = int(request.form.get("dev_meter_num", 4))
        meter_den = int(request.form.get("dev_meter_den", 4))
        key_name = request.form.get("dev_key", "auto")
        add_bass = request.form.get("dev_add_bass") == "on"
        title = request.form.get("dev_title", "Desarrollo de Idea")
        score_composer = request.form.get("dev_composer", "CompositorIA")

        if not user_motif:
            raise ValueError("No se proporcionó ningún motivo para desarrollar")

        # Map variation intensity to freedom level
        variation_freedom = variation_intensity

        # Create basic config (will be overridden by motif analysis if key="auto")
        detected_key = key_name if key_name != "auto" else "C"
        detected_mode = "major"

        config = GenerationConfig(
            tonal=TonalConfig(key_name=detected_key, mode=detected_mode),
            meter=MeterConfig(
                meter_tuple=(meter_num, meter_den),
                num_measures=num_measures,
            ),
            rhythm=RhythmConfig(
                complexity=2,
                use_rests=True,
                rest_probability=0.1,
            ),
            melody=MelodyConfig(
                impulse_type=ImpulseType.TETIC,
                climax_position=0.65,
                climax_intensity=1.3,
                max_interval=6,
                infraction_rate=0.05,
                use_tenoris=False,
            ),
            motif=MotifConfig(
                use_motivic_variations=True,
                variation_probability=0.5 if variation_intensity == 2 else (0.3 if variation_intensity == 1 else 0.7),
                variation_freedom=variation_freedom,
            ),
            markov=MarkovConfig(enabled=False),
        )

        # Create architect and develop the motif
        architect = MelodicArchitect(config=config)

        # Use develop_user_motif method
        staff, lilypond_code = architect.develop_user_motif(
            user_motif=user_motif,
            num_measures=num_measures,
            variation_freedom=variation_freedom,
            detect_key=(key_name == "auto"),
            add_bass=add_bass,
            title=title,
            composer=score_composer,
        )

        # Get detected key info for display
        display_key = architect.scale_manager.key_name
        display_mode = architect.scale_manager.mode

        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"develop_{display_key}_{display_mode}_{timestamp}"
        ly_filepath = OUTPUT_DIR / f"{base_filename}.ly"

        with open(ly_filepath, "w", encoding="utf-8") as f:
            f.write(lilypond_code)

        # Run LilyPond
        pdf_path = None
        midi_path = None
        lilypond_error = None

        try:
            result = subprocess.run(
                [
                    "lilypond",
                    "-dno-point-and-click",
                    f"--output={OUTPUT_DIR / base_filename}",
                    str(ly_filepath),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            potential_pdf = OUTPUT_DIR / f"{base_filename}.pdf"
            potential_midi = OUTPUT_DIR / f"{base_filename}.midi"

            if potential_pdf.exists():
                pdf_path = f"{base_filename}.pdf"
            if potential_midi.exists():
                midi_path = f"{base_filename}.midi"

            if result.returncode != 0:
                lilypond_error = result.stderr

        except subprocess.TimeoutExpired:
            lilypond_error = "LilyPond timed out after 60 seconds"
        except FileNotFoundError:
            lilypond_error = "LilyPond not found. Please install LilyPond."

        return render_template(
            "result.html",
            success=True,
            lilypond_code=lilypond_code,
            pdf_path=pdf_path,
            midi_path=midi_path,
            ly_filename=f"{base_filename}.ly",
            lilypond_error=lilypond_error,
            key_name=display_key,
            mode=display_mode,
            meter=f"{meter_num}/{meter_den}",
            num_measures=num_measures,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template(
            "result.html",
            success=False,
            error=str(e),
        )


@app.route("/output/<path:filename>")
def serve_output(filename):
    """Serve files from the output directory."""
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
