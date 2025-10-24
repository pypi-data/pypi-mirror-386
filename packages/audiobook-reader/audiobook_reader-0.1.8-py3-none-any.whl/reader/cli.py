"""Main CLI interface for the reader application."""
import click
from pathlib import Path
from typing import List, Optional
import sys
import warnings
import yaml
import tempfile
import atexit
import shutil

# Suppress known warnings from dependencies
warnings.filterwarnings("ignore", 
                       message=".*This search incorrectly ignores the root element.*",
                       category=FutureWarning,
                       module="ebooklib.*")

from .config import ConfigManager
from .parsers.epub_parser import EPUBParser
from .parsers.pdf_parser import PDFParser
from .parsers.text_parser import PlainTextParser
from .interfaces.text_parser import TextParser

# TTS engines
try:
    from .engines.kokoro_engine import KokoroEngine
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

# Analysis and processing components
from .analysis.dialogue_detector import DialogueDetector
from .voices.character_mapper import CharacterVoiceMapper
from .chapters.chapter_manager import ChapterManager
from .batch.neural_processor import NeuralProcessor
from .batch.batch_processor import create_batch_processor
from .processors.ffmpeg_processor import get_audio_processor
from .voices.voice_previewer import get_voice_previewer
from .utils.setup import validate_environment, check_ffmpeg


class ReaderApp:
    """Main application class."""

    def __init__(self, init_tts=False):
        """Initialize the reader application."""
        # Early FFmpeg warning (non-blocking)
        if not shutil.which("ffmpeg"):
            print("⚠️  FFmpeg not detected (required for audio conversion)")
            print("💡 Install: brew install ffmpeg (macOS) | winget install ffmpeg (Windows) | sudo apt install ffmpeg (Linux)\n")

        # Use system-standard config location (works in CLI, GUI, and app bundles)
        config_path = Path.home() / ".config/audiobook-reader/settings.yaml"
        self.config_manager = ConfigManager(config_path)

        # Use system temp for working files (session-specific workspace)
        self.temp_workspace = Path(tempfile.mkdtemp(prefix="audiobook-reader-"))
        self.text_dir = self.temp_workspace / "text"
        self.audio_dir = self.temp_workspace / "audio"
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        # Use standard system locations for persistent data
        self.models_dir = Path.home() / ".cache/audiobook-reader/models"
        self.config_dir = Path.home() / ".config/audiobook-reader"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Register cleanup on exit
        atexit.register(self._cleanup_temp_workspace)

        # Update config manager to use new locations
        self.config_manager.config.text_dir = str(self.text_dir)
        self.config_manager.config.audio_dir = str(self.audio_dir)
        self.config_manager.config.config_dir = str(self.config_dir)

        self.tts_engine = None
        if init_tts:
            self.tts_engine = self._initialize_tts_engine()

        # Initialize parsers
        self.parsers: List[TextParser] = [
            EPUBParser(),
            PDFParser(),
            PlainTextParser()
        ]

        # Analysis and processing components
        try:
            self.character_mapper = CharacterVoiceMapper(self.config_dir)
            self.dialogue_detector = DialogueDetector()
            self.chapter_manager = ChapterManager()
            self.audio_processor = get_audio_processor()
            self.voice_previewer = get_voice_previewer()
        except Exception as e:
            print(f"⚠️  Warning: Some advanced features not available: {e}")

    def _cleanup_temp_workspace(self):
        """Clean up temporary workspace on exit."""
        try:
            if hasattr(self, 'temp_workspace') and self.temp_workspace.exists():
                shutil.rmtree(self.temp_workspace, ignore_errors=True)
        except Exception:
            pass  # Ignore cleanup errors
    
    def get_tts_engine(self):
        """Get TTS engine, initializing if needed."""
        if self.tts_engine is None:
            self.tts_engine = self._initialize_tts_engine()
        return self.tts_engine
    
    def _initialize_tts_engine(self):
        """Initialize Kokoro TTS engine."""
        # Check FFmpeg first
        ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
        if not ffmpeg_ok:
            print(ffmpeg_msg)
            raise RuntimeError("FFmpeg is required for audio conversion")

        if not KOKORO_AVAILABLE:
            print("❌ Error: Kokoro engine not available.")
            print("📥 Install: pip install audiobook-reader")
            print("📖 See: docs/KOKORO_SETUP.md")
            raise RuntimeError("Kokoro engine not available")

        try:
            return KokoroEngine()
        except Exception as e:
            # Show helpful error and exit
            error_str = str(e)
            if "Failed to download" in error_str or "Kokoro models not found" in error_str:
                print("❌ Error: Kokoro models not available.")
                print()
                print("💡 Try: reader download-models")
                print("   Or check your internet connection")
                print()
                raise RuntimeError("Kokoro models required") from e
            elif "ModuleNotFoundError" in error_str or "ImportError" in error_str:
                print("❌ Error: Missing dependencies.")
                print()
                print("Reinstall reader with:")
                print("  pip install --force-reinstall audiobook-reader")
                print()
                raise RuntimeError("Missing dependencies") from e
            else:
                print(f"❌ Error initializing Kokoro engine: {e}")
                print()
                print("💡 Troubleshooting:")
                print("  - Run with debug: reader convert --debug --file yourfile.txt")
                print("  - Check issues: https://github.com/dcrsn/reader/issues")
                print()
                raise
    
    def _apply_temporary_overrides(self, overrides: dict):
        """Apply temporary CLI parameter overrides without saving to config file."""
        # Apply processing level override
        if 'processing_level' in overrides:
            level = overrides['processing_level']
            # Temporarily modify the config objects in memory
            config = self.config_manager.config
            config.processing.level = level
            
            # Auto-configure features based on level (in memory only)
            if level == "phase1":
                config.processing.character_voices = False
                config.processing.dialogue_detection = False
            elif level == "phase2":
                config.processing.character_voices = False
                config.processing.dialogue_detection = False
            elif level == "phase3":
                config.processing.character_voices = False
                config.processing.dialogue_detection = True
        
        # Apply engine override
        if 'engine' in overrides:
            engine = overrides['engine']
            # Temporarily modify the config object in memory
            self.config_manager.config.tts.engine = engine
        
        # Reinitialize TTS engine if needed
        if 'engine' in overrides:
            self.tts_engine = self._initialize_tts_engine()
    
    def get_parser_for_file(self, file_path: Path) -> Optional[TextParser]:
        """Get appropriate parser for file."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def find_text_files(self) -> List[Path]:
        """Find all supported text files in text directory."""
        # Use temp workspace text directory
        text_dir = self.text_dir
        supported_files = []

        # Check if directory exists and has files
        if text_dir.exists():
            for file_path in text_dir.iterdir():
                if file_path.is_file() and self.get_parser_for_file(file_path):
                    supported_files.append(file_path)

        return supported_files
    
    def convert_file(
        self,
        file_path: Path,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        format: Optional[str] = None,
        character_voices: Optional[bool] = None,
        chapter_detection: Optional[bool] = None,
        dialogue_detection: Optional[bool] = None,
        batch_mode: bool = False,
        checkpoint_interval: int = 50,
        turbo_mode: bool = False,
        debug: bool = False,
        progress_style: str = "timeseries",
        character_config: Optional[Path] = None,
        output_dir: Optional[str] = None
    ) -> Path:
        """Convert a single file to audiobook."""
        # Get parser
        parser = self.get_parser_for_file(file_path)
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        # Parse content
        click.echo(f"Parsing {file_path.name}...")
        parsed_content = parser.parse(file_path)
        
        # Get configuration
        tts_config = self.config_manager.get_tts_config()
        audio_config = self.config_manager.get_audio_config()
        processing_config = self.config_manager.get_processing_config()
        
        if debug:
            print(f"🔍 DEBUG: Loaded config values:")
            print(f"   TTS: engine={tts_config.engine}, voice={tts_config.voice}, speed={tts_config.speed}")
            print(f"   Audio: format={audio_config.format}")
            print(f"   Processing: level={processing_config.level}, characters={processing_config.character_voices}")
            print(f"   Chunk size: {processing_config.chunk_size}")
        
        # Override with command-line arguments
        if voice:
            if debug: print(f"🔍 DEBUG: Overriding voice: {tts_config.voice} -> {voice}")
            tts_config.voice = voice
        if speed:
            if debug: print(f"🔍 DEBUG: Overriding speed: {tts_config.speed} -> {speed}")
            tts_config.speed = speed
        if format:
            if debug: print(f"🔍 DEBUG: Overriding format: {audio_config.format} -> {format}")
            audio_config.format = format
        if character_voices is not None:
            if debug: print(f"🔍 DEBUG: Overriding characters: {processing_config.character_voices} -> {character_voices}")
            processing_config.character_voices = character_voices
        if chapter_detection is not None:
            if debug: print(f"🔍 DEBUG: Overriding chapters: {processing_config.auto_detect_chapters} -> {chapter_detection}")
            processing_config.auto_detect_chapters = chapter_detection
        if dialogue_detection is not None:
            if debug: print(f"🔍 DEBUG: Overriding dialogue: {processing_config.dialogue_detection} -> {dialogue_detection}")
            processing_config.dialogue_detection = dialogue_detection

        if debug:
            print(f"🔍 DEBUG: Final config after overrides:")
            print(f"   TTS: engine={tts_config.engine}, voice={tts_config.voice}, speed={tts_config.speed}")
            print(f"   Audio: format={audio_config.format}")
            print(f"   Processing: level={processing_config.level}, characters={processing_config.character_voices}")
        
        # Character voice loading and analysis (only when explicitly enabled with --characters)
        if self.character_mapper and processing_config.character_voices:
            # Determine which config file to use
            if character_config and character_config.exists():
                # Use explicitly provided config file
                config_to_load = character_config
            else:
                # Auto-detect: use filename.characters.yaml next to source file
                config_to_load = file_path.with_suffix('.characters.yaml')

            # Load existing config if it exists
            if config_to_load.exists():
                count = self.character_mapper.load_from_file(config_to_load)
                click.echo(f"Loaded {count} character mappings from {config_to_load.name}")

            click.echo("Analyzing characters and dialogue...")
            voice_analysis = self.character_mapper.analyze_text_for_voices(parsed_content.content)

            if voice_analysis['new_characters']:
                click.echo(f"Found new characters: {', '.join(voice_analysis['new_characters'])}")

                # Auto-save character assignments to per-file config
                per_file_config = file_path.with_suffix('.characters.yaml')
                count = self.character_mapper.save_to_file(per_file_config)
                click.echo(f"✓ Saved {count} character mappings to {per_file_config.name}")

            if voice_analysis['detected_characters']:
                click.echo(f"Character voices: {voice_analysis['voice_assignments']}")
        
        # Generate audio with Neural Engine processing
        click.echo(f"Generating audio for '{parsed_content.title}'...")

        # Create temp output path in workspace (will be moved to final location after completion)
        output_path = self._create_output_path(parsed_content.title, tts_config, audio_config, processing_config)

        # Determine final output directory
        if output_dir:
            # CLI override
            if output_dir == "downloads":
                final_output_dir = Path.home() / "Downloads"
            elif output_dir == "same":
                final_output_dir = file_path.parent
            else:
                final_output_dir = Path(output_dir)
        else:
            # Use config
            final_output_dir = self.config_manager.get_output_dir(file_path)

        # Create Neural Engine processor with optimized settings
        # Pass character mapper and dialogue detector if character voices enabled
        processor = NeuralProcessor(
            output_path=output_path,
            checkpoint_interval=checkpoint_interval,
            progress_style=progress_style,
            character_mapper=self.character_mapper if processing_config.character_voices else None,
            dialogue_detector=self.dialogue_detector if processing_config.character_voices else None,
            debug=debug,
            final_output_dir=final_output_dir
        )

        # Split content into optimized chunks aligned with Kokoro's processing
        if tts_config.engine == "kokoro" and KOKORO_AVAILABLE:
            # Use 400-char chunks to match Kokoro's optimal size (no re-chunking)
            kokoro_engine = self.get_tts_engine()
            text_chunks = kokoro_engine._chunk_text_intelligently(parsed_content.content, max_length=400)
        else:
            # Use basic chunking for non-Kokoro engines (if any added later)
            chunk_size = min(400, processing_config.chunk_size)
            text_chunks = [parsed_content.content[i:i+chunk_size]
                          for i in range(0, len(parsed_content.content), chunk_size)]

        # Get voice blend configuration
        voice_blend = {}
        if tts_config.voice:
            voice_blend = {tts_config.voice: 1.0}
        else:
            # Default voice
            if tts_config.engine == "kokoro":
                voice_blend = {"am_michael": 1.0}
            else:
                voice_blend = {"default": 1.0}

        # Processing configuration for checkpoints
        proc_config = {
            'engine': tts_config.engine,
            'voice': tts_config.voice,
            'speed': tts_config.speed,
            'processing_level': processing_config.level,
            'format': audio_config.format
        }

        # Process chunks with Neural Engine
        final_output = processor.process_chunks(
            file_path=file_path,
            text_chunks=text_chunks,
            tts_engine=self.get_tts_engine(),
            voice_blend=voice_blend,
            speed=tts_config.speed,
            processing_config=proc_config
        )

        return final_output
    
    def _get_expected_output_path(self, file_path: Path, voice=None, speed=None, format=None,
                                characters=None, chapters=None, dialogue=None,
                                processing_level=None, turbo_mode=False) -> Path:
        """Get expected output path for a file with given settings."""
        # Get parser and parse just the title
        parser = self.get_parser_for_file(file_path)
        if not parser:
            raise ValueError(f"No parser available for file: {file_path}")
        
        parsed_content = parser.parse(file_path)
        
        # Get configurations with overrides
        tts_config = self.config_manager.get_tts_config()
        audio_config = self.config_manager.get_audio_config()
        processing_config = self.config_manager.get_processing_config()
        
        # Apply overrides
        if voice:
            tts_config.voice = voice
        if speed:
            tts_config.speed = speed
        if format:
            audio_config.format = format
        if characters is not None:
            processing_config.character_voices = characters
        if chapters is not None:
            processing_config.auto_detect_chapters = chapters
        if dialogue is not None:
            processing_config.dialogue_detection = dialogue
        if processing_level:
            processing_config.level = processing_level
        
        # Generate the same output path that would be created
        return self._create_output_path(parsed_content.title, tts_config, audio_config, processing_config)
    def _create_output_path(self, title, tts_config, audio_config, processing_config):
        """Create standardized output path for temp audio files in workspace."""
        # Use temp workspace audio directory
        audio_dir = self.audio_dir

        # Build descriptive filename
        engine = tts_config.engine
        voice = tts_config.voice or "default"

        # Build filename parts
        filename_parts = [title, engine, voice]

        # Only add speed if non-default (not 1.0)
        if tts_config.speed != 1.0:
            speed_str = f"speed{tts_config.speed}".replace(".", "p")
            filename_parts.append(speed_str)

        # Add feature flags (only if enabled)
        if processing_config.character_voices:
            filename_parts.append("characters")

        output_filename = f"{'_'.join(filename_parts)}.{audio_config.format}"
        return audio_dir / output_filename


# CLI Commands
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Reader: Convert text files to audiobooks."""
    pass


@cli.command()
@click.option('--voice', '-v', help='Voice to use for synthesis (e.g., am_michael, af_sarah)')
@click.option('--speed', '-s', type=float, help='Speech speed multiplier - 1.0 is normal, 1.2 is 20% faster (e.g., 1.2)')
@click.option('--format', '-f', type=click.Choice(['wav', 'mp3', 'm4a', 'm4b']), help='Output audio format (default: mp3)')
@click.option('--file', '-F', type=click.Path(exists=True), help='Convert specific file (required)')
@click.option('--characters/--no-characters', default=None, help='Enable/disable character voice mapping for dialogue')
@click.option('--character-config', type=click.Path(exists=True), help='Path to character voice config YAML file (e.g., mybook.characters.yaml)')
@click.option('--chapters/--no-chapters', default=None, help='Enable/disable chapter detection and metadata in audiobook')
@click.option('--dialogue/--no-dialogue', default=None, help='Enable/disable dialogue detection with emotion analysis')
@click.option('--processing-level', type=click.Choice(['phase1', 'phase2', 'phase3']), help='Set processing level: phase1 (basic), phase2 (emotion), phase3 (full features)')
@click.option('--batch-mode', is_flag=True, help='Enable checkpoint recovery - resume interrupted conversions')
@click.option('--checkpoint-interval', type=int, default=50, help='Save progress every N chunks for recovery (default: 50)')
@click.option('--turbo-mode', is_flag=True, default=False, help='Maximum speed - uses 95% CPU, minimal delays')
@click.option('--debug', is_flag=True, default=False, help='Show detailed debug output including Neural Engine status')
@click.option('--progress-style', type=click.Choice(['simple', 'tqdm', 'rich', 'timeseries']), default='timeseries', help='Progress display: simple (text), tqdm (bars), rich (fancy), timeseries (charts)')
@click.option('--output-dir', help='Output directory: "downloads" (~/Downloads), "same" (next to source), or explicit path')
def convert(voice, speed, format, file, characters, character_config, chapters, dialogue, processing_level, batch_mode, checkpoint_interval, turbo_mode, debug, progress_style, output_dir):
    """Convert text file to audiobook.

    All options are temporary overrides and won't be saved to config.
    Use 'reader config' to permanently save settings."""
    app = ReaderApp()
    
    # Apply temporary overrides without modifying config file
    temp_overrides = {}
    
    if processing_level:
        temp_overrides['processing_level'] = processing_level

    # Apply overrides and reinitialize if needed
    if temp_overrides:
        app._apply_temporary_overrides(temp_overrides)
    
    if file:
        # Convert specific file
        file_path = Path(file)
        # Apply turbo mode settings
        if turbo_mode:
            click.echo("🚀 Turbo mode enabled: Maximum performance settings active")
        
        try:
            if debug:
                click.echo(f"🔍 DEBUG: CLI parameters passed to convert_file:")
                click.echo(f"   voice={voice}, speed={speed}, format={format}")
                click.echo(f"   characters={characters}, character_config={character_config}, chapters={chapters}, dialogue={dialogue}")
                click.echo(f"   batch_mode={batch_mode}, turbo_mode={turbo_mode}, progress_style={progress_style}")

            output_path = app.convert_file(
                file_path, voice, speed, format, characters, chapters, dialogue,
                batch_mode=batch_mode, checkpoint_interval=checkpoint_interval,
                turbo_mode=turbo_mode, debug=debug, progress_style=progress_style,
                character_config=Path(character_config) if character_config else None,
                output_dir=output_dir
            )
            click.echo(f"✓ Conversion complete: {output_path}")
        except Exception as e:
            click.echo(f"✗ Error converting {file_path}: {e}", err=True)
            sys.exit(1)
    else:
        # No file specified - show usage
        click.echo("Error: --file option is required")
        click.echo("Usage: reader convert --file mybook.epub")
        click.echo("Supported formats: .epub, .pdf, .txt, .md, .rst")
        sys.exit(1)


@cli.command()
@click.option('--language', help='Filter by language (e.g., en-us, en-uk)')
@click.option('--gender', type=click.Choice(['male', 'female']), help='Filter by gender')
def voices(language, gender):
    """List available Kokoro TTS voices."""
    app = ReaderApp()

    if not KOKORO_AVAILABLE:
        click.echo("❌ Kokoro engine not available.")
        click.echo("📥 Install: See docs/KOKORO_SETUP.md")
        return

    click.echo("\nKOKORO Voices:")
    click.echo("=" * 15)

    # Use KokoroEngine voices
    from .engines.kokoro_engine import KokoroEngine
    kokoro_voices = KokoroEngine.VOICES

    # Get all available voices
    filtered_voices = [voice_id for voice_id in kokoro_voices]

    # Apply filters if specified
    if language:
        filtered_voices = [v for v in filtered_voices
                         if kokoro_voices[v]['lang'] == language]
    if gender:
        filtered_voices = [v for v in filtered_voices
                         if kokoro_voices[v]['gender'] == gender.lower()]

    # Display voices
    for voice in filtered_voices:
        voice_info = kokoro_voices[voice]
        click.echo(f"  - {voice}")
        click.echo(f"    Name: {voice_info['name']}")
        click.echo(f"    Gender: {voice_info['gender']}")
        click.echo(f"    Language: {voice_info['lang']}")


@cli.group()
def characters():
    """Manage character voice mappings."""
    pass


@characters.command()
@click.argument('name')
@click.argument('voice_id')
@click.option('--gender', default='unknown', help='Character gender')
@click.option('--description', default='', help='Character description')
def add(name, voice_id, gender, description):
    """Add a character voice mapping."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Character mapping not available. Install Phase 2 dependencies.")
        return
    
    app.character_mapper.add_character(name, voice_id, gender, description)
    click.echo(f"✓ Added character '{name}' with voice '{voice_id}'")


@characters.command()
@click.argument('name')
def remove(name):
    """Remove a character voice mapping."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Character mapping not available. Install Phase 2 dependencies.")
        return
    
    if app.character_mapper.remove_character(name):
        click.echo(f"✓ Removed character '{name}'")
    else:
        click.echo(f"✗ Character '{name}' not found")


@characters.command()
def list():
    """List all character voice mappings."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Character mapping not available.")
        return

    characters_list = app.character_mapper.list_characters()
    if not characters_list:
        click.echo("No characters configured.")
        return

    click.echo("Character Voice Mappings:")
    for char_name in characters_list:
        char_voice = app.character_mapper.get_character_voice(char_name)
        if char_voice:
            click.echo(f"  {char_name}: {char_voice.voice_id} ({char_voice.gender})")


@characters.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output config file (default: <file>_characters.yaml)')
@click.option('--auto-assign', is_flag=True, help='Automatically assign gender-appropriate voices')
def detect(file_path, output, auto_assign):
    """Detect characters in a text file and create character config template."""
    app = ReaderApp()
    if not app.character_mapper or not app.dialogue_detector:
        click.echo("Character detection not available.")
        return

    input_file = Path(file_path)

    # Parse the file
    parser = app.get_parser_for_file(input_file)
    if not parser:
        click.echo(f"✗ No parser available for {input_file.suffix}")
        return

    click.echo(f"📖 Analyzing {input_file.name}...")
    parsed_content = parser.parse(input_file)

    # Detect characters
    detected_chars = app.character_mapper.detect_characters_in_text(parsed_content.content)

    if not detected_chars:
        click.echo("No characters detected in the text.")
        return

    click.echo(f"Found {len(detected_chars)} characters: {', '.join(detected_chars)}")

    # Determine output file
    if output:
        output_file = Path(output)
    else:
        output_file = input_file.with_suffix('.characters.yaml')

    # Create character config template
    char_list = []
    if auto_assign:
        # Auto-assign gender-appropriate voices
        click.echo("Auto-assigning voices...")
        assignments = app.character_mapper.auto_assign_voices(detected_chars)
        for char_name in sorted(detected_chars):
            char_voice = app.character_mapper.get_character_voice(char_name)
            if char_voice:
                char_list.append({
                    'name': char_name,
                    'voice': char_voice.voice_id,
                    'gender': char_voice.gender
                })
                click.echo(f"  {char_name}: {char_voice.voice_id} ({char_voice.gender})")
    else:
        # Create template for manual editing
        for char_name in sorted(detected_chars):
            char_list.append({
                'name': char_name,
                'voice': 'CHANGE_ME',  # User must fill in
                'gender': 'unknown'  # User must fill in
            })

    # Write config file
    config_data = {'characters': char_list}
    with open(output_file, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)

    click.echo(f"✓ Character config saved to: {output_file}")
    if not auto_assign:
        click.echo(f"   Edit the file to assign voices, then use: reader convert --characters --character-config {output_file.name}")


@cli.group()
def blend():
    """Manage voice blending."""
    pass


@blend.command()
@click.argument('name')
@click.argument('voice_spec')  # e.g., "af_sarah:60,af_nicole:40"
@click.option('--description', default='', help='Blend description')
def create(name, voice_spec, description):
    """Create a voice blend. Format: voice1:weight1,voice2:weight2"""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Voice blending not available. Install Phase 2 dependencies.")
        return
    
    try:
        # Parse voice specification
        voice_weights = {}
        for part in voice_spec.split(','):
            voice, weight = part.split(':')
            voice_weights[voice.strip()] = float(weight.strip()) / 100.0
        
        blend_spec = app.character_mapper.create_voice_blend(name, voice_weights, description)
        click.echo(f"✓ Created voice blend '{name}': {blend_spec}")
        
    except Exception as e:
        click.echo(f"✗ Error creating blend: {e}", err=True)


@blend.command()
def list():
    """List all voice blends."""
    app = ReaderApp()
    if not app.character_mapper:
        click.echo("Voice blending not available. Install Phase 2 dependencies.")
        return
    
    blends = app.character_mapper.list_voice_blends()
    if not blends:
        click.echo("No voice blends configured.")
        return
    
    click.echo("Voice Blends:")
    for blend_name in blends:
        blend = app.character_mapper.get_voice_blend(blend_name)
        if blend:
            click.echo(f"  {blend_name}: {blend.voices}")
            if blend.description:
                click.echo(f"    {blend.description}")


@cli.command()
@click.option('--monitor', is_flag=True, help='Monitor current conversion progress')
def progress(monitor):
    """Monitor conversion progress in real-time."""
    from .batch.batch_processor import RobustProcessor
    processor = RobustProcessor()
    
    if monitor:
        import time
        try:
            while True:
                summary = processor.get_system_status()
                checkpoints = processor.list_all_checkpoints()
                
                click.clear()
                click.echo("📊 Real-time Progress Monitor")
                click.echo("=" * 40)
                
                if checkpoints:
                    for cp in checkpoints[:3]:  # Show top 3
                        file_name = Path(cp['file']).name
                        click.echo(f"📄 {file_name}")
                        click.echo(f"   Progress: {cp['progress']} ({cp['percent']:.1f}%)")
                        
                        # Progress bar
                        bar_length = 30
                        filled = int(cp['percent'] / 100 * bar_length)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        click.echo(f"   [{bar}] {cp['percent']:.1f}%")
                        click.echo()
                
                click.echo(f"💾 System: {summary['disk_usage_mb']:.1f}MB disk usage")
                click.echo("Press Ctrl+C to stop monitoring")
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            click.echo("\n👋 Monitoring stopped.")
    else:
        # One-time status check
        summary = processor.get_system_status()
        checkpoints = processor.list_all_checkpoints()
        
        if checkpoints:
            click.echo("📊 Current Progress:")
            for cp in checkpoints:
                file_name = Path(cp['file']).name
                click.echo(f"📄 {file_name}: {cp['percent']:.1f}% complete")
        else:
            click.echo("No active conversions found.")


@cli.command()
@click.option('--list', 'list_checkpoints', is_flag=True, help='List all checkpoints')
@click.option('--cleanup', type=click.Path(exists=True), help='Clean up checkpoint for specific file')
@click.option('--status', type=click.Path(exists=True), help='Show processing status for specific file')
@click.option('--summary', is_flag=True, help='Show checkpoint system summary')
def checkpoints(list_checkpoints, cleanup, status, summary):
    """Manage batch processing checkpoints."""
    from .batch.batch_processor import RobustProcessor
    processor = RobustProcessor()
    
    if list_checkpoints:
        checkpoints = processor.list_all_checkpoints()
        if not checkpoints:
            click.echo("No checkpoints found.")
            return
        
        click.echo("📂 Available Checkpoints:")
        for cp in checkpoints:
            age = f"{cp['age_hours']:.1f}h ago" if cp['age_hours'] < 24 else f"{cp['age_hours']/24:.1f}d ago"
            click.echo(f"  📄 {Path(cp['file']).name}")
            click.echo(f"      Progress: {cp['progress']} ({cp['percent']:.1f}%)")
            click.echo(f"      Age: {age}")
            click.echo()
    
    elif cleanup:
        file_path = Path(cleanup)
        if processor.cleanup_checkpoint(file_path):
            click.echo(f"✅ Checkpoint cleaned up for {file_path.name}")
        else:
            click.echo(f"❌ Failed to cleanup checkpoint for {file_path.name}")
    
    elif status:
        file_path = Path(status)
        status_info = processor.get_processing_status(file_path)
        
        if not status_info['has_checkpoint']:
            click.echo(f"📄 {file_path.name}: No checkpoint found")
        else:
            progress = status_info['progress']
            age = f"{status_info['age_hours']:.1f}h ago" if status_info['age_hours'] < 24 else f"{status_info['age_hours']/24:.1f}d ago"
            
            click.echo(f"📄 {file_path.name}")
            click.echo(f"   Status: {status_info['status']}")
            click.echo(f"   Progress: {progress['completed']}/{progress['total']} ({progress['percent']:.1f}%)")
            click.echo(f"   Last update: {age}")
    
    elif summary:
        summary_info = processor.get_system_status()
        click.echo("📊 Checkpoint System Summary:")
        click.echo(f"   Active checkpoints: {summary_info['active_checkpoints']}")
        click.echo(f"   Total segments: {summary_info['total_segments']}")
        click.echo(f"   Disk usage: {summary_info['disk_usage_mb']:.1f} MB")
        click.echo(f"   Checkpoint directory: {summary_info['checkpoint_dir']}")
        
        if summary_info['recent_checkpoints']:
            click.echo("\n📂 Recent Checkpoints:")
            for cp in summary_info['recent_checkpoints']:
                click.echo(f"   📄 {Path(cp['file']).name} ({cp['percent']:.1f}%)")
    
    else:
        click.echo("Use --help to see checkpoint management options.")


@cli.command()
@click.option('--voice', help='Set default voice (saved to config)')
@click.option('--speed', type=float, help='Set default speed (saved to config)')
@click.option('--format', type=click.Choice(['wav', 'mp3', 'm4a', 'm4b']), help='Set default audio format (saved to config)')
@click.option('--characters/--no-characters', help='Enable/disable character voices by default (saved to config)')
@click.option('--processing-level', type=click.Choice(['phase1', 'phase2', 'phase3']), help='Set default processing level (saved to config)')
def config(voice, speed, format, characters, processing_level):
    """Configure default settings (permanently saved to config file)."""
    app = ReaderApp()
    
    # TTS configuration updates
    tts_updates = {}
    if voice:
        tts_updates['voice'] = voice
    if speed:
        tts_updates['speed'] = speed

    if tts_updates:
        app.config_manager.update_tts_config(**tts_updates)
        click.echo("TTS configuration updated.")
    
    # Audio configuration updates
    if format:
        app.config_manager.update_audio_config(format=format)
        click.echo("Audio configuration updated.")
    
    # Processing level update
    if processing_level:
        app.config_manager.set_processing_level(processing_level)
        click.echo(f"Processing level set to {processing_level}.")
    
    # Processing configuration updates
    processing_updates = {}
    if characters is not None:
        processing_updates['character_voices'] = characters

    if processing_updates:
        app.config_manager.update_processing_config(**processing_updates)
        click.echo("Processing configuration updated.")

    if not any([voice, speed, format, engine, characters is not None, processing_level]):
        # Display current config
        tts_config = app.config_manager.get_tts_config()
        audio_config = app.config_manager.get_audio_config()
        processing_config = app.config_manager.get_processing_config()
        
        click.echo("Current configuration:")
        click.echo(f"  Processing level: {processing_config.level}")
        click.echo(f"  Engine: {tts_config.engine}")
        click.echo(f"  Voice: {tts_config.voice or 'default'}")
        click.echo(f"  Speed: {tts_config.speed}")
        click.echo(f"  Volume: {tts_config.volume}")
        click.echo(f"  Audio format: {audio_config.format}")
        click.echo(f"  Character voices: {processing_config.character_voices}")
        click.echo(f"  Dialogue detection: {processing_config.dialogue_detection}")


@cli.command()
def info():
    """Show application information and quick start guide."""
    app = ReaderApp()

    # Get relevant directories
    models_dir = app.models_dir
    config_dir = app.config_dir
    output_dir = app.config_manager.get_output_dir()

    # Header
    click.echo(f"📖 Reader: Text-to-Audiobook CLI (Neural Engine Optimized)")
    click.echo("=" * 50)

    # System info
    click.echo(f"\n📂 File Locations:")
    click.echo(f"  Models: {models_dir}")
    click.echo(f"  Config: {config_dir}")
    click.echo(f"  Output: {output_dir}")
    click.echo(f"  Temp workspace: /tmp/audiobook-reader-* (session-based)")

    # Quick start
    click.echo("\n🚀 Quick Start:")
    click.echo("1. Convert any text file: reader convert --file mybook.epub")
    click.echo("2. Find audiobook in configured output directory")
    click.echo("3. Choose output: --output-dir downloads|same|/custom/path")
    
    # Basic commands
    click.echo("\n💻 Basic Commands:")
    click.echo("  reader convert --file book.epub           # Convert file")
    click.echo("  reader convert --file book.epub --voice am_michael  # Use specific voice")
    click.echo("  reader convert --file book.epub --characters  # Enable character voices")
    click.echo("  reader voices                             # List available voices")
    click.echo("  reader config                             # View/set preferences")

    click.echo("\n🎭 Advanced Commands:")
    click.echo("  reader characters add NAME VOICE # Map character to voice")
    click.echo("  reader characters list     # Show character mappings")
    click.echo("  reader blend create NAME SPEC # Create voice blend")
    click.echo("  reader blend list           # Show voice blends")
    click.echo("  reader preview VOICE        # Preview voice samples")
    click.echo("  reader chapters extract FILE # Extract chapter structure")
    click.echo("  reader batch add FILES      # Add files to batch queue")
    click.echo("  reader batch process        # Process batch queue")
    
    # Configuration
    tts_config = app.config_manager.get_tts_config()
    audio_config = app.config_manager.get_audio_config()
    
    click.echo("\n⚙️ Current Settings:")
    click.echo(f"  Voice: {tts_config.voice or 'default'}")
    click.echo(f"  Speed: {tts_config.speed}x")
    click.echo(f"  Format: {audio_config.format.upper()}")
    
    # Documentation
    click.echo("\n📚 Documentation:")
    click.echo("  README.md        - Project overview and quick start")
    click.echo("  docs/USAGE.md    - Complete command reference")
    click.echo("  docs/EXAMPLES.md - Real-world examples and workflows")

    click.echo("\n🎯 Features:")
    click.echo("  ✅ Neural TTS (Kokoro) with 54 voices across 9 languages")
    click.echo("  ✅ Apple Neural Engine acceleration (M1/M2/M3)")
    click.echo("  ✅ Professional audio formats (MP3, M4A, M4B)")
    click.echo("  ✅ Emotion detection and dialogue analysis")
    click.echo("  ✅ Character voice mapping and blending")
    click.echo("  ✅ Chapter extraction and metadata")
    click.echo("  ✅ Batch processing with checkpoints")
    click.echo("  ✅ Real-time progress visualization")
    click.echo("  ✅ 5 input formats (EPUB, PDF, TXT, MD, RST)")
    
    # Tips
    click.echo("\n💡 Tips:")
    click.echo("  • Convert any file directly: reader convert --file book.epub")
    click.echo("  • Set default output: reader config --output-dir /audiobooks")
    click.echo("  • Models auto-download to cache on first use (~310MB)")


@cli.command('download')
@click.argument('target', default='models')
@click.option('--local', is_flag=True, help='Download to local models/ folder instead of cache')
@click.option('--force', is_flag=True, help='Force re-download even if models exist')
def download_models(target, local, force):
    """Download Kokoro TTS models (~310MB)."""
    from .utils.model_downloader import download_models as do_download, get_cache_dir
    from pathlib import Path

    if target != 'models':
        click.echo(f"Unknown target: {target}. Use 'reader download models'")
        return

    target_dir = Path.cwd() / "models" if local else None
    cache = (target_dir or get_cache_dir()) / "kokoro"

    if not force:
        model = cache / "kokoro-v1.0.onnx"
        voices = cache / "voices-v1.0.bin"
        if model.exists() and voices.exists():
            click.echo(f"✅ Models already installed at: {cache}")
            click.echo(f"   Use --force to re-download")
            return

    click.echo(f"📥 Downloading Kokoro TTS models...")
    click.echo(f"   Location: {cache}")

    if do_download(verbose=True, target_dir=target_dir):
        click.echo("\n✅ Models ready! You can now use Kokoro TTS.")
    else:
        click.echo("\n❌ Download failed. Check your internet connection.")
        raise click.Abort()


# Phase 3 commands
@cli.command()
@click.argument('voice')
@click.option('--text', help='Custom preview text')
@click.option('--output-dir', type=click.Path(), help='Directory to save preview files')
def preview(voice, text, output_dir):
    """Generate voice preview samples."""
    app = ReaderApp(init_tts=False)  # TTS initialized by voice_previewer
    if not app.voice_previewer:
        click.echo("Voice previewer not available.")
        return
    
    try:
        output_path = Path(output_dir) if output_dir else None
        preview_file = app.voice_previewer.generate_voice_preview(
            engine_name='kokoro',
            voice=voice,
            preview_text=text,
            output_dir=output_path
        )

        click.echo(f"✓ Voice preview generated: {preview_file}")
        click.echo("Play the file to hear how this voice sounds.")

    except Exception as e:
        click.echo(f"✗ Error generating preview: {e}", err=True)


@cli.group()
def chapters():
    """Manage chapter extraction and metadata."""
    pass


@chapters.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for chapter metadata')
@click.option('--format', type=click.Choice(['json', 'text']), default='json', help='Output format')
def extract(file_path, output, format):
    """Extract chapter structure from a book file."""
    app = ReaderApp(init_tts=False)  # No TTS needed for chapter extraction
    if not app.chapter_manager:
        click.echo("Chapter manager not available.")
        return
    
    input_file = Path(file_path)
    
    try:
        # Extract chapters based on file type
        if input_file.suffix.lower() == '.epub':
            chapters = app.chapter_manager.extract_chapters_from_epub(input_file)
        elif input_file.suffix.lower() == '.pdf':
            chapters = app.chapter_manager.extract_chapters_from_pdf(input_file)
        else:
            # Read as text and extract
            with open(input_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            chapters = app.chapter_manager.extract_chapters_from_text(text_content)
        
        if not chapters:
            click.echo("No chapters found in the file.")
            return
        
        click.echo(f"Found {len(chapters)} chapters:")
        for i, chapter in enumerate(chapters, 1):
            duration_str = f"{chapter.duration:.1f}s" if chapter.duration else "N/A"
            click.echo(f"  {i}. {chapter.title} ({chapter.word_count} words, ~{duration_str})")
        
        # Save to output file if specified
        if output:
            output_path = Path(output)
            if format == 'json':
                app.chapter_manager.save_chapters_metadata(chapters, output_path)
            else:
                # Save as text report
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Chapter Structure for: {input_file.name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    stats = app.chapter_manager.get_chapter_statistics(chapters)
                    f.write(f"Total chapters: {stats['total_chapters']}\n")
                    f.write(f"Total duration: {stats['total_duration_formatted']}\n")
                    f.write(f"Total words: {stats['total_words']}\n\n")
                    
                    for i, chapter in enumerate(chapters, 1):
                        f.write(f"Chapter {i}: {chapter.title}\n")
                        f.write(f"  Words: {chapter.word_count}\n")
                        if chapter.duration:
                            f.write(f"  Duration: {chapter.duration:.1f}s\n")
                        f.write(f"  Start time: {chapter.start_time:.1f}s\n\n")
            
            click.echo(f"✓ Chapter metadata saved to: {output_path}")
        
    except Exception as e:
        click.echo(f"✗ Error extracting chapters: {e}", err=True)


@cli.group()
def batch():
    """Manage batch processing of multiple files."""
    pass


@batch.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--directory', '-d', type=click.Path(exists=True), help='Add all files from directory')
@click.option('--recursive', '-r', is_flag=True, help='Search directory recursively')
@click.option('--output-dir', type=click.Path(), help='Output directory for converted files')
def add(files, directory, recursive, output_dir):
    """Add files to batch processing queue."""
    app = ReaderApp(init_tts=False)  # Batch processor handles TTS internally
    batch_processor = create_batch_processor(app.config_manager)
    
    job_ids = []
    
    # Add individual files
    for file_path in files:
        input_file = Path(file_path)
        output_file = None
        if output_dir:
            output_file = Path(output_dir) / input_file.with_suffix('.wav').name
        
        job_id = batch_processor.add_job(input_file, output_file)
        job_ids.append(job_id)
        click.echo(f"✓ Added: {input_file.name} (Job ID: {job_id})")
    
    # Add directory
    if directory:
        dir_job_ids = batch_processor.add_directory(
            Path(directory),
            Path(output_dir) if output_dir else None,
            recursive=recursive
        )
        job_ids.extend(dir_job_ids)
        click.echo(f"✓ Added {len(dir_job_ids)} files from directory")
    
    if job_ids:
        click.echo(f"Total jobs in queue: {len(batch_processor.jobs)}")
    else:
        click.echo("No files added to batch queue.")


@batch.command()
@click.option('--max-workers', type=int, default=2, help='Maximum number of concurrent workers')
@click.option('--save-progress', is_flag=True, help='Save progress to file')
def process(max_workers, save_progress):
    """Process all jobs in the batch queue."""
    app = ReaderApp()
    batch_processor = create_batch_processor(app.config_manager, max_workers)
    
    if not batch_processor.jobs:
        click.echo("No jobs in batch queue. Use 'reader batch add' to add files.")
        return
    
    def progress_callback(job):
        status_symbol = "✓" if job.status.value == "completed" else "✗" if job.status.value == "failed" else "⏳"
        click.echo(f"{status_symbol} {job.input_file.name} - {job.status.value}")
    
    batch_processor.set_progress_callback(progress_callback)
    
    click.echo(f"Processing {len(batch_processor.jobs)} jobs with {max_workers} workers...")
    
    try:
        result = batch_processor.process_batch(save_progress=save_progress)
        
        click.echo(f"\nBatch processing complete!")
        click.echo(f"  Total jobs: {result.total_jobs}")
        click.echo(f"  Completed: {result.completed_jobs}")
        click.echo(f"  Failed: {result.failed_jobs}")
        click.echo(f"  Success rate: {result.success_rate:.1f}%")
        click.echo(f"  Total time: {result.total_duration:.1f}s")
        
        if result.failed_jobs > 0:
            click.echo("\nFailed jobs:")
            for job in result.results:
                if job.status.value == "failed":
                    click.echo(f"  ✗ {job.input_file.name}: {job.error_message}")
    
    except KeyboardInterrupt:
        click.echo("\nBatch processing cancelled by user.")
        batch_processor.cancel_batch()
    except Exception as e:
        click.echo(f"✗ Batch processing error: {e}", err=True)


@batch.command()
def status():
    """Show current batch queue status."""
    app = ReaderApp()
    batch_processor = create_batch_processor(app.config_manager)
    
    summary = batch_processor.get_batch_summary()
    
    click.echo("Batch Queue Status:")
    click.echo(f"  Total jobs: {summary['total_jobs']}")
    click.echo(f"  Running: {summary['is_running']}")
    
    if summary['total_jobs'] > 0:
        click.echo("  Job status breakdown:")
        for status, count in summary['status_counts'].items():
            if count > 0:
                click.echo(f"    {status}: {count}")


@batch.command()
def clear():
    """Clear all jobs from the batch queue."""
    app = ReaderApp()
    batch_processor = create_batch_processor(app.config_manager)
    
    if batch_processor.is_running:
        click.echo("Cannot clear queue while batch is running.")
        return
    
    job_count = len(batch_processor.jobs)
    batch_processor.clear_jobs()
    click.echo(f"✓ Cleared {job_count} jobs from batch queue.")


if __name__ == "__main__":
    cli()