import typer
import json
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Detect fake or hallucinated code using uvmgr's validation system.")

# Import the demonstration logic
from demo_fake_code_detection import FakeCodeDetector

def _load_json_input(input_path: Optional[Path], input_str: Optional[str]):
    if input_path:
        with open(input_path, 'r') as f:
            return json.load(f)
    elif input_str:
        return json.loads(input_str)
    else:
        raise typer.BadParameter("You must provide either --input-file or --input-str.")

@app.command()
def detect(
    input_file: Optional[Path] = typer.Option(None, "--input-file", help="Path to JSON file with code sample to validate."),
    input_str: Optional[str] = typer.Option(None, "--input-str", help="Raw JSON string with code sample to validate."),
    context: str = typer.Option("code generation", help="Context description for the code sample."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON."),
):
    """Detect fake or hallucinated code in a code sample (JSON)."""
    code_sample = _load_json_input(input_file, input_str)
    detector = FakeCodeDetector()
    result = detector.analyze_code_sample(code_sample, context)
    if json_output:
        typer.echo(json.dumps({
            "is_valid": result.is_valid,
            "confidence": result.confidence,
            "issues": result.issues,
            "metadata": result.metadata,
            "validation_level": str(result.validation_level),
        }, indent=2))
    else:
        # The detector already prints a formatted result
        pass 