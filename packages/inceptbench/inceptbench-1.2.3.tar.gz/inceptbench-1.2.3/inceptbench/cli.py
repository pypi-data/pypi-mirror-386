"""CLI for Incept Eval"""
import click
import json
import sys
import os
from pathlib import Path
import requests

def get_api_key(api_key=None):
    """Get API key - now optional since we run locally"""
    if api_key:
        return api_key
    if os.getenv('INCEPT_API_KEY'):
        return os.getenv('INCEPT_API_KEY')
    config_file = Path.home() / '.incept' / 'config'
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f).get('api_key')
        except:
            pass
    # API key is now optional - we run locally
    return None

@click.group()
@click.version_option(version='1.0.7')
def cli():
    """Incept Eval - Evaluate educational questions via Incept API

    \b
    CLI tool for evaluating educational questions with comprehensive
    assessment including V3 scaffolding, answer verification, and
    EduBench task evaluation.

    \b
    Commands:
      evaluate    Evaluate questions from a JSON file
      benchmark   Process many questions in parallel (high throughput)
      example     Generate sample input JSON file
      help        Show detailed help and usage examples

    \b
    Quick Start:
      1. Configure your API key:
         $ inceptbench configure YOUR_API_KEY

      2. Generate a sample file:
         $ inceptbench example

      3. Evaluate questions:
         $ inceptbench evaluate qs.json --verbose

    \b
    Examples:
      # Basic evaluation (simplified scores)
      $ inceptbench evaluate questions.json

      # Full detailed evaluation results
      $ inceptbench evaluate questions.json --full

      # Save full results to file
      $ inceptbench evaluate questions.json --full -o results.json

      # Append multiple evaluations to one file
      $ inceptbench evaluate test1.json -a all_results.json
      $ inceptbench evaluate test2.json -a all_results.json

      # Use local API server
      $ inceptbench evaluate test.json --api-url http://localhost:8000

    \b
    For detailed help, run: inceptbench help
    """
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Save results to file (overwrites)')
@click.option('--append', '-a', type=click.Path(), help='Append results to file (creates if not exists)')
@click.option('--api-key', '-k', envvar='INCEPT_API_KEY', help='API key for authentication')
@click.option('--api-url', default='https://uae-poc.inceptapi.com', help='API endpoint URL')
@click.option('--timeout', '-t', type=int, default=600, help='Request timeout in seconds (default: 600)')
@click.option('--pretty', is_flag=True, default=True, help='Show only scores (default: enabled)')
@click.option('--verbose', '-v', is_flag=True, help='Show progress messages')
@click.option('--full', '-f', is_flag=True, help='Return full detailed evaluation results (default: simplified scores only)')
@click.option('--subject', '-s', type=click.Choice(['math', 'ela', 'science', 'social-studies', 'general'], case_sensitive=False), help='Subject area for automatic evaluator selection')
@click.option('--grade', '-g', help='Grade level (e.g., "K", "3", "6-8", "9-12")')
@click.option('--type', type=click.Choice(['mcq', 'fill-in', 'short-answer', 'essay', 'text-content', 'passage'], case_sensitive=False), help='Content type for automatic evaluator selection')
def evaluate(input_file, output, append, api_key, api_url, timeout, pretty, verbose, full, subject, grade, type):
    """Evaluate educational content with comprehensive assessment

    The evaluator automatically selects appropriate evaluation methods based on
    your content and optional parameters (subject, grade, type).

    Examples:
        # Basic evaluation
        inceptbench evaluate questions.json

        # Math questions with specific grade
        inceptbench evaluate questions.json --subject math --grade "6-8"

        # ELA reading comprehension
        inceptbench evaluate questions.json --subject ela --type mcq
    """
    try:
        api_key = get_api_key(api_key)
        if verbose:
            click.echo(f"📂 Loading: {input_file}")

        with open(input_file) as f:
            data = json.load(f)

        # Add verbose flag and routing parameters to the data
        data['verbose'] = full
        if subject:
            data['subject'] = subject
        if grade:
            data['grade'] = grade
        if type:
            data['type'] = type

        # Import here to avoid loading evaluator for non-evaluation commands
        from .client import InceptClient
        client = InceptClient(api_key, api_url, timeout=timeout)
        result = client.evaluate_dict(data)

        # Always output full results - pretty only controls formatting
        json_output = json.dumps(result, indent=2 if pretty else None, ensure_ascii=False)

        # Handle output options
        if output:
            # Overwrite mode
            with open(output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            if verbose:
                click.echo(f"✅ Saved to: {output}")
        elif append:
            # Append mode - load existing evaluations or create new list
            existing_data = []
            if Path(append).exists():
                try:
                    with open(append, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            # If file exists but isn't a list, wrap it
                            existing_data = [existing_data]
                except json.JSONDecodeError:
                    if verbose:
                        click.echo(f"⚠️  File exists but is invalid JSON, creating new file")
                    existing_data = []

            # Append new result
            existing_data.append(result)

            # Write back to file
            with open(append, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            if verbose:
                click.echo(f"✅ Appended to: {append} (total: {len(existing_data)} evaluations)")
        else:
            # Print to stdout
            click.echo(json_output)

    except requests.HTTPError as e:
        click.echo(f"❌ API Error: {e.response.status_code}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Save results to file')
@click.option('--workers', '-w', type=int, default=100, help='Number of parallel workers (default: 100)')
@click.option('--verbose', '-v', is_flag=True, help='Show progress messages')
@click.option('--subject', '-s', type=click.Choice(['math', 'ela', 'science', 'social-studies', 'general'], case_sensitive=False), help='Subject area for automatic evaluator selection')
@click.option('--grade', '-g', help='Grade level (e.g., "K", "3", "6-8", "9-12")')
@click.option('--type', type=click.Choice(['mcq', 'fill-in', 'short-answer', 'essay', 'text-content', 'passage'], case_sensitive=False), help='Content type for automatic evaluator selection')
def benchmark(input_file, output, workers, verbose, subject, grade, type):
    """Benchmark mode: Process many questions in parallel

    Evaluates all questions using parallel workers for maximum throughput.
    The evaluator automatically selects appropriate methods based on your content.

    Example:
        inceptbench benchmark questions.json --workers 100 --subject math -o results.json
    """
    try:
        if verbose:
            click.echo(f"📂 Loading: {input_file}")

        with open(input_file) as f:
            data = json.load(f)

        # Add routing parameters to the data
        if subject:
            data['subject'] = subject
        if grade:
            data['grade'] = grade
        if type:
            data['type'] = type

        # Import here to avoid loading evaluator for non-benchmark commands
        from .client import InceptClient
        client = InceptClient()

        # Use benchmark mode
        if verbose:
            click.echo(f"🚀 Benchmark mode: {len(data.get('generated_questions', []))} questions with {workers} workers")

        result = client.benchmark(data, max_workers=workers)

        # Format output
        json_output = json.dumps(result, indent=2, ensure_ascii=False)

        # Handle output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            if verbose:
                click.echo(f"✅ Saved to: {output}")
                click.echo(f"📊 Results: {result['successful']}/{result['total_questions']} successful")
                click.echo(f"⏱️  Time: {result['evaluation_time_seconds']:.2f}s")
                click.echo(f"📈 Avg Score: {result['avg_score']:.3f}")
                if result['failed_ids']:
                    click.echo(f"❌ Failed IDs: {', '.join(result['failed_ids'])}")
        else:
            click.echo(json_output)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('api_key')
def configure(api_key):
    """Save API key to config file"""
    try:
        config_dir = Path.home() / '.incept'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'config'

        with open(config_file, 'w') as f:
            json.dump({'api_key': api_key}, f)

        config_file.chmod(0o600)
        click.echo(f"✅ API key saved to {config_file}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def help():
    """Show detailed help and usage examples"""
    help_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                    INCEPT-EVAL CLI HELP                           ║
╚═══════════════════════════════════════════════════════════════════╝

OVERVIEW:
  Incept Eval is a CLI tool for evaluating educational questions using
  the Incept API. It supports comprehensive evaluation including:
  - V3 scaffolding/DI compliance scoring
  - Answer correctness verification
  - EduBench task evaluation (QA, EC, IP, AG)

INSTALLATION:
  pip install inceptbench

COMMANDS:

  1. configure - Save your API key
     Usage: inceptbench configure YOUR_API_KEY

     This saves your API key to ~/.incept/config for future use.

  2. example - Generate sample input file
     Usage: inceptbench example [OPTIONS]

     Options:
       -o, --output PATH    Save to file (default: qs.json)

     Examples:
       inceptbench example                    # Creates qs.json
       inceptbench example -o sample.json     # Creates sample.json

  3. evaluate - Evaluate questions from JSON file
     Usage: inceptbench evaluate INPUT_FILE [OPTIONS]

     Options:
       -o, --output PATH      Save results to file (overwrites)
       -a, --append PATH      Append results to file (creates if not exists)
       -k, --api-key KEY      API key (or use INCEPT_API_KEY env var)
       --api-url URL          API endpoint (default: https://uae-poc.inceptapi.com)
       --pretty               Show only scores (default: enabled)
       --no-pretty            Show full results including EduBench details
       -v, --verbose          Show progress messages
       -f, --full             Return full detailed evaluation (default: simplified scores)

     Examples:
       # Basic evaluation (simplified scores only)
       inceptbench evaluate test.json

       # Full detailed evaluation results
       inceptbench evaluate test.json --full

       # Save to file (overwrite)
       inceptbench evaluate test.json -o results.json

       # Append to file (creates if not exists)
       inceptbench evaluate test.json -a evaluations.json --verbose

       # Full detailed results with progress messages
       inceptbench evaluate test.json --full --verbose

       # Local API testing
       inceptbench evaluate test.json --api-url http://localhost:8000

API KEY CONFIGURATION (3 methods):

  1. Config file (recommended):
     inceptbench configure YOUR_API_KEY

  2. Environment variable:
     export INCEPT_API_KEY=your_api_key
     inceptbench evaluate test.json

  3. Command line flag:
     inceptbench evaluate test.json --api-key your_api_key

INPUT FILE FORMAT:

  The input JSON file must contain:
  - submodules_to_run: List of evaluation modules to enable
    ["ti_question_qa", "answer_verification", "math_content_evaluator", "reading_question_qc"]
  - generated_questions: Array of questions to evaluate with:
    - id: Unique question identifier
    - type: "mcq" or "fill-in"
    - question: Question text
    - answer: Correct answer
    - answer_explanation: Step-by-step explanation
    - answer_options: MCQ options (for MCQ type)
    - skill: Optional skill metadata

  Use 'inceptbench example' to see a complete example.

OUTPUT FORMAT:

  The response includes:
  - request_id: Unique evaluation identifier
  - evaluations: Per-question evaluation results:
    - ti_question_qa: Comprehensive quality scores (0-1 scale)
    - answer_verification: Answer correctness verification
    - external_edubench: EduBench task scores (0-10 scale)
    - final_score: Combined score from all modules (0-1 scale)
    - math_content_evaluator: Math content quality scores
    - reading_question_qc: Reading question quality scores
  - evaluation_time_seconds: Total evaluation time

QUICK START:

  # 1. Configure API key
  inceptbench configure YOUR_API_KEY

  # 2. Generate sample file
  inceptbench example

  # 3. Evaluate questions
  inceptbench evaluate qs.json --verbose

  # 4. Save results (overwrite)
  inceptbench evaluate test.json -o results.json

  # 5. Append multiple evaluations to one file
  inceptbench evaluate test1.json -a all_results.json
  inceptbench evaluate test2.json -a all_results.json
  inceptbench evaluate test3.json -a all_results.json

LOCAL TESTING:

  To test against a local API server:
  inceptbench evaluate test.json --api-url http://localhost:8000

For more information, visit: https://github.com/incept-ai/inceptbench
"""
    click.echo(help_text)

@cli.command()
@click.option('--output', '-o', type=click.Path(), default='qs.json', help='Save to file (default: qs.json)')
def example(output):
    """Generate sample input file

    Creates a complete example with Arabic math question demonstrating
    the simplified evaluation interface. The evaluator automatically
    selects appropriate methods based on your content.

    By default, saves to qs.json in the current directory.
    """
    example_data = {
        "subject": "math",
        "grade": "6",
        "generated_questions": [
            {
                "id": "q1",
                "type": "mcq",
                "question": "إذا كان ثمن 2 قلم هو 14 ريالًا، فما ثمن 5 أقلام بنفس المعدل؟",
                "answer": "35 ريالًا",
                "answer_explanation": "الخطوة 1: تحليل المسألة — لدينا ثمن 2 قلم وهو 14 ريالًا. نحتاج إلى معرفة ثمن 5 أقلام بنفس المعدل. يجب التفكير في العلاقة بين عدد الأقلام والسعر وكيفية تحويل عدد الأقلام بمعدل ثابت.\nالخطوة 2: تطوير الاستراتيجية — يمكننا أولًا إيجاد ثمن قلم واحد بقسمة 14 ÷ 2 = 7 ريال، ثم ضربه في 5 لإيجاد ثمن 5 أقلام: 7 × 5 = 35 ريالًا.\nالخطوة 3: التطبيق والتحقق — نتحقق من منطقية الإجابة بمقارنة السعر بعدد الأقلام. السعر يتناسب طرديًا مع العدد، وبالتالي 35 ريالًا هي الإجابة الصحيحة والمنطقية.",
                "answer_options": {
                    "A": "28 ريالًا",
                    "B": "70 ريالًا",
                    "C": "30 ريالًا",
                    "D": "35 ريالًا"
                },
                "skill": {
                    "title": "Grade 6 Mid-Year Comprehensive Assessment",
                    "grade": "6",
                    "subject": "mathematics",
                    "difficulty": "medium",
                    "description": "Apply proportional reasoning, rational number operations, algebraic thinking, geometric measurement, and statistical analysis to solve multi-step real-world problems",
                    "language": "ar"
                },
                "image_url": None,
                "additional_details": "🔹 **Question generation logic:**\nThis question targets proportional reasoning for Grade 6 students, testing their ability to apply ratios and unit rates to real-world problems. It follows a classic proportionality structure — starting with a known ratio (2 items for 14 riyals) and scaling it up to 5 items. The stepwise reasoning develops algebraic thinking and promotes estimation checks to confirm logical correctness.\n\n🔹 **Personalized insight examples:**\n- Choosing 28 ريالًا shows a misunderstanding by doubling instead of proportionally scaling.\n- Choosing 7 ريالًا indicates the learner found the unit rate but didn't scale it up to 5.\n- Choosing 14 ريالًا confuses the given 2-item cost with the required 5-item cost.\n\n🔹 **Instructional design & DI integration:**\nThe question aligns with *Percent, Ratio, and Probability* learning targets. In DI format 15.7, it models how equivalent fractions and proportional relationships can predict outcomes across different scales. This builds foundational understanding for probability and proportional reasoning. By using a simple, relatable context (price of pens), it connects mathematical ratios to practical real-world applications, supporting concept transfer and cognitive engagement."
            }
        ]
    }

    json_output = json.dumps(example_data, indent=2, ensure_ascii=False)

    with open(output, 'w', encoding='utf-8') as f:
        f.write(json_output)
    click.echo(f"✅ Sample file saved to: {output}")

if __name__ == '__main__':
    cli()
