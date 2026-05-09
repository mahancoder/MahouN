"""
Data Preparation CLI
====================
Command-line interface for data preparation pipeline
"""

import argparse
import asyncio
import sys
from pathlib import Path
import json
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from .pipeline import AdvancedDataPipeline, PipelineStage
from .config import DataPrepConfig

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Advanced Data Preparation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python -m pipelines.data_prep_advanced.cli \\
    --input ./data/raw/ \\
    --output ./data/processed/

  # Run specific stages
  python -m pipelines.data_prep_advanced.cli \\
    --input ./data/raw/ \\
    --output ./data/processed/ \\
    --stages ingestion validation preprocessing

  # With custom config
  python -m pipelines.data_prep_advanced.cli \\
    --input ./data/raw/ \\
    --output ./data/processed/ \\
    --config ./configs/data_prep.yaml

  # Dry run
  python -m pipelines.data_prep_advanced.cli \\
    --input ./data/raw/ \\
    --output ./data/processed/ \\
    --dry-run
        """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input directory or file"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file (YAML)"
    )
    
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=[s.value for s in PipelineStage],
        help="Stages to run (default: all)"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel processing"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (don't execute)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--report",
        type=Path,
        help="Save report to file"
    )
    
    return parser


async def run_pipeline(args: argparse.Namespace):
    """Run the pipeline"""
    
    # Load config
    if args.config:
        config = DataPrepConfig.from_yaml(args.config)
    else:
        config = DataPrepConfig()
    
    # Parse stages
    stages = None
    if args.stages:
        stages = [PipelineStage(s) for s in args.stages]
    
    # Show configuration
    console.print(Panel.fit(
        f"[bold cyan]Data Preparation Pipeline[/bold cyan]\n\n"
        f"Input:  {args.input}\n"
        f"Output: {args.output}\n"
        f"Stages: {', '.join(s.value for s in (stages or list(PipelineStage)))}\n"
        f"Parallel: {args.parallel} (workers={args.workers})",
        title="Configuration"
    ))
    
    if args.dry_run:
        console.print("[yellow]Dry run mode - no execution[/yellow]")
        return
    
    # Create pipeline
    pipeline = AdvancedDataPipeline(
        config=config,
        enable_parallel=args.parallel,
        max_workers=args.workers
    )
    
    # Run with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running pipeline...", total=None)
        
        try:
            results = await pipeline.run_full_pipeline(
                input_path=args.input,
                output_path=args.output,
                stages=stages
            )
            
            progress.update(task, completed=True)
            
        except Exception as e:
            console.print(f"[red]Pipeline failed: {e}[/red]")
            if args.verbose:
                console.print_exception()
            sys.exit(1)
    
    # Show results
    display_results(results, pipeline)
    
    # Save report
    if args.report:
        save_report(pipeline, args.report)
        console.print(f"[green]Report saved to {args.report}[/green]")


def display_results(results, pipeline):
    """Display pipeline results"""
    
    # Summary table
    table = Table(title="Pipeline Results", show_header=True)
    table.add_column("Stage", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Input", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Duration", justify="right")
    
    for result in results:
        status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
        duration = f"{result.duration_seconds:.2f}s"
        
        table.add_row(
            result.stage.value,
            status,
            str(result.input_count),
            str(result.output_count),
            duration
        )
    
    console.print(table)
    
    # Summary
    summary = pipeline.get_summary()
    console.print(Panel.fit(
        f"[bold]Summary[/bold]\n\n"
        f"Total stages: {summary['total_stages']}\n"
        f"Successful: [green]{summary['successful_stages']}[/green]\n"
        f"Failed: [red]{summary['failed_stages']}[/red]\n"
        f"Total duration: {summary['total_duration_seconds']:.2f}s",
        title="Execution Summary"
    ))


def save_report(pipeline, report_path: Path):
    """Save execution report"""
    summary = pipeline.get_summary()
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Run async
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
