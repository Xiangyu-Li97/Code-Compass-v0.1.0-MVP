"""Command-line interface for Code Compass."""

import sys
import time
import click
from pathlib import Path
from ai_code_compass.map_generator import MapGenerator
from ai_code_compass import __version__


@click.group()
@click.version_option(version=__version__, prog_name="code-compass")
def cli():
    """Code Compass - Fast code map generator for AI coding assistants."""
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--force', is_flag=True, help='Force re-index all files')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def index(path: str, force: bool, verbose: bool):
    """Index a project's code."""
    project_path = Path(path).resolve()
    
    click.echo(f"🔍 Indexing project: {project_path}")
    
    if force:
        click.echo("⚡ Force mode: re-indexing all files")
    
    try:
        generator = MapGenerator(project_path)
        
        start_time = time.time()
        stats = generator.index(force=force)
        elapsed = time.time() - start_time
        
        # Display results
        click.echo(f"\n✅ Indexing complete in {elapsed:.2f}s")
        click.echo(f"\n📊 Statistics:")
        click.echo(f"   Total files: {stats['total_files']}")
        click.echo(f"   Parsed: {stats['parsed_files']}")
        click.echo(f"   Cached (unchanged): {stats['cached_files']}")
        click.echo(f"   Failed: {stats['failed_files']}")
        click.echo(f"   Symbols: {stats['total_symbols']:,}")
        click.echo(f"   Imports: {stats['total_imports']:,}")
        
        if stats['total_files'] > 0:
            speed = stats['total_files'] / elapsed
            click.echo(f"   Speed: {speed:.1f} files/s")
        
        if verbose and stats['failed_files'] > 0:
            click.echo(f"\n⚠️  {stats['failed_files']} files failed to parse")
        
        generator.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Project path')
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--top', type=float, default=0.2, help='Top percentage of files (0.0-1.0)')
@click.option('--max-symbols', type=int, default=50, help='Max symbols per file')
@click.option('--output', '-o', type=click.Path(), help='Output file (default: stdout)')
def map(path: str, format: str, top: float, max_symbols: int, output: str):
    """Generate a code map."""
    project_path = Path(path).resolve()
    
    try:
        generator = MapGenerator(project_path)
        
        # Check if project is indexed
        stats = generator.get_stats()
        if stats['total_files'] == 0:
            click.echo("⚠️  No files indexed. Run 'code-compass index' first.", err=True)
            sys.exit(1)
        
        click.echo(f"🗺️  Generating map (top {top*100:.0f}%, format={format})...")
        
        start_time = time.time()
        repo_map = generator.generate_map(
            top_percent=top,
            max_symbols_per_file=max_symbols,
            format=format
        )
        elapsed = time.time() - start_time
        
        # Output
        if output:
            output_path = Path(output)
            output_path.write_text(repo_map)
            click.echo(f"✅ Map saved to {output_path} ({elapsed:.2f}s)")
        else:
            click.echo(repo_map)
            click.echo(f"\n✅ Generated in {elapsed:.2f}s", err=True)
        
        generator.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--path', type=click.Path(exists=True), default='.', help='Project path')
@click.option('--fuzzy', is_flag=True, help='Fuzzy search')
@click.option('--show-signature', '-s', is_flag=True, help='Show full signature')
def find(name: str, path: str, fuzzy: bool, show_signature: bool):
    """Find symbol definitions."""
    project_path = Path(path).resolve()
    
    try:
        generator = MapGenerator(project_path)
        
        click.echo(f"🔎 Finding symbol: {name}")
        if fuzzy:
            click.echo("   (fuzzy search enabled)")
        
        results = generator.find_symbol(name, fuzzy=fuzzy)
        
        if not results:
            click.echo(f"❌ No symbols found matching '{name}'")
            sys.exit(1)
        
        click.echo(f"\n✅ Found {len(results)} result(s):\n")
        
        for file_info, symbol_name in results:
            # Find the symbol
            symbol = next((s for s in file_info.symbols if s.name == symbol_name), None)
            if symbol:
                click.echo(f"📄 {file_info.path}")
                click.echo(f"   {symbol.type.value}: {symbol.name}")
                if show_signature:
                    click.echo(f"   {symbol.signature}")
                click.echo()
        
        generator.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Project path')
def stats(path: str):
    """Show indexing statistics."""
    project_path = Path(path).resolve()
    
    try:
        generator = MapGenerator(project_path)
        
        stats = generator.get_stats()
        
        click.echo(f"📊 Project statistics for {project_path}:\n")
        click.echo(f"   Total files: {stats['total_files']}")
        click.echo(f"   Total symbols: {stats['total_symbols']:,}")
        click.echo(f"   Cache directory: {generator.cache_dir}")
        
        if stats['total_files'] == 0:
            click.echo(f"\n⚠️  No files indexed. Run 'code-compass index' first.")
        
        generator.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Project path')
@click.confirmation_option(prompt='Are you sure you want to clear the cache?')
def clear(path: str):
    """Clear the index cache."""
    project_path = Path(path).resolve()
    
    try:
        generator = MapGenerator(project_path)
        generator.clear_cache()
        click.echo(f"✅ Cache cleared for {project_path}")
        generator.close()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
