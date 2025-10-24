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
@click.version_option(version='1.3.0')
def cli():
    """Incept Eval - Evaluate educational questions via Incept API

    \b
    CLI tool for evaluating educational questions with comprehensive
    assessment including DI compliance, answer verification, and
    specialized evaluators for math, reading, and image content.

    \b
    Commands:
      evaluate    Evaluate questions from a JSON file
      benchmark   Process many questions in parallel (high throughput)
      example     Generate sample input JSON file
      help        Show detailed help and usage examples

    \b
    Quick Start:
      1. Generate a sample file:
         $ inceptbench example

      2. Evaluate questions (automatic routing):
         $ inceptbench evaluate qs.json --subject math --grade 6

      3. Evaluate with image content:
         $ inceptbench evaluate qs.json --subject math --type mcq --verbose

    \b
    Examples:
      # Automatic evaluator selection based on content
      $ inceptbench evaluate questions.json --subject math --grade "6-8"

      # Full detailed evaluation results
      $ inceptbench evaluate questions.json --full --verbose

      # Save full results to file
      $ inceptbench evaluate questions.json --full -o results.json

      # Evaluate reading comprehension
      $ inceptbench evaluate questions.json --subject ela --type mcq

      # Benchmark mode for high throughput
      $ inceptbench benchmark questions.json --workers 100 -o results.json

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
║                      Version 1.3.0                                ║
╚═══════════════════════════════════════════════════════════════════╝

OVERVIEW:
  InceptBench is a comprehensive evaluation framework for educational
  content. It features automatic evaluator routing based on content type,
  subject, and grade level with specialized evaluators for:
  - Reading Question QC (ALWAYS included - universal quality assessment)
  - Text & Instructional Content Quality
  - Math Content Evaluation
  - Answer Correctness Verification
  - Image Quality Assessment (DI principles)
  - Math Image Judge (visual problem evaluation)

INSTALLATION:
  pip install inceptbench

COMMANDS:

  1. example - Generate sample input file
     Usage: inceptbench example [OPTIONS]

     Options:
       -o, --output PATH    Save to file (default: qs.json)

     Examples:
       inceptbench example                    # Creates qs.json
       inceptbench example -o sample.json     # Creates sample.json

  2. evaluate - Evaluate questions from JSON file
     Usage: inceptbench evaluate INPUT_FILE [OPTIONS]

     Options:
       -o, --output PATH      Save results to file (overwrites)
       -a, --append PATH      Append results to file (creates if not exists)
       -s, --subject TEXT     Subject area: math, ela, science, social-studies, general
       -g, --grade TEXT       Grade level: K, 3, 6-8, 9-12, etc.
       --type TEXT            Content type: mcq, fill-in, short-answer, essay, text-content, passage
       -v, --verbose          Show progress messages
       -f, --full             Return full detailed evaluation (default: simplified scores)

     Examples:
       # Automatic routing for math content
       inceptbench evaluate questions.json --subject math --grade 6

       # Reading comprehension evaluation
       inceptbench evaluate questions.json --subject ela --type mcq

       # Full detailed evaluation with all scores
       inceptbench evaluate questions.json --full --verbose

       # Save results to file
       inceptbench evaluate questions.json -o results.json

       # Evaluate image-based questions
       inceptbench evaluate questions.json --subject math --grade "6-8" --full

  3. benchmark - High-throughput parallel evaluation
     Usage: inceptbench benchmark INPUT_FILE [OPTIONS]

     Options:
       -o, --output PATH      Save results to file
       -w, --workers INT      Number of parallel workers (default: 100)
       -s, --subject TEXT     Subject area for routing
       -g, --grade TEXT       Grade level for routing
       --type TEXT            Content type for routing
       -v, --verbose          Show progress messages

     Example:
       inceptbench benchmark questions.json --workers 100 --subject math -o results.json

AUTOMATIC EVALUATOR ROUTING:

  InceptBench v1.3.0 features automatic evaluator selection based on:
  - Subject area (math, ela, science, etc.)
  - Grade level (K-12 range)
  - Content type (mcq, essay, text-content, etc.)

  Available evaluators:
  • reading_question_qc     - ALWAYS included for all content
  • ti_question_qa          - Question quality assessment
  • answer_verification     - Answer correctness checking
  • math_content_evaluator  - Math-specific content evaluation
  • text_content_evaluator  - Text/instructional content quality
  • math_image_judge_evaluator - Math visual problem evaluation
  • image_quality_di_evaluator - DI-compliant image quality

  Reading QC is universal: runs on ALL content (questions AND text) to
  ensure comprehensive quality coverage across all submissions.

INPUT FILE FORMAT:

  Minimal format with automatic routing:
  {
    "subject": "math",           // Optional: for automatic routing
    "grade": "6",                // Optional: for automatic routing
    "generated_questions": [
      {
        "id": "q1",
        "type": "mcq",
        "question": "Question text here",
        "answer": "Correct answer",
        "answer_explanation": "Step-by-step explanation",
        "answer_options": {
          "A": "Option 1",
          "B": "Option 2",
          "C": "Option 3",
          "D": "Option 4"
        },
        "image_url": "https://...",  // Optional: for image evaluation
        "skill": {                    // Optional metadata
          "title": "Skill name",
          "grade": "6",
          "subject": "mathematics"
        }
      }
    ]
  }

  Use 'inceptbench example' to generate a complete sample file.

OUTPUT FORMAT:

  The response includes:
  - inceptbench_version: Version used for evaluation (1.3.0)
  - request_id: Unique evaluation identifier
  - evaluations: Per-question/content results with:
    - reading_question_qc: Universal quality scores (always present)
    - ti_question_qa: Question quality scores (0-1 scale)
    - answer_verification: Correctness with reasoning
    - math_content_evaluator: Math content quality
    - text_content_evaluator: Text content quality
    - math_image_judge_evaluator: Math visual evaluation
    - image_quality_di_evaluator: DI image quality scores
    - score: Combined final score (0-1 scale)
  - evaluation_time_seconds: Total evaluation time

QUICK START:

  # 1. Generate sample file
  inceptbench example

  # 2. Evaluate with automatic routing
  inceptbench evaluate qs.json --subject math --grade 6 --verbose

  # 3. Get full detailed results
  inceptbench evaluate qs.json --full -o results.json

  # 4. Benchmark mode for large datasets
  inceptbench benchmark qs.json --workers 100 -o results.json

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
