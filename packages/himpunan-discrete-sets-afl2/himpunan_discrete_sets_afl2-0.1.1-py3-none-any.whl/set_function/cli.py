"""Console script for set_function."""

import typer
from rich.console import Console
from rich.table import Table
from typing import List

from set_function.set_function import Himpunan

app = typer.Typer(help="Set Function CLI - Mathematical Set Operations")
console = Console()


def parse_set(set_str: str) -> Himpunan:
    """Parse a string representation of a set into a Himpunan object."""
    try:
        # Remove braces and split by comma
        elements_str = set_str.strip("{}").split(",")
        elements = []
        for elem in elements_str:
            elem = elem.strip()
            if elem:
                # Try to convert to int, then float, otherwise keep as string
                try:
                    elements.append(int(elem))
                except ValueError:
                    try:
                        elements.append(float(elem))
                    except ValueError:
                        # Remove quotes if present
                        elements.append(elem.strip("\"'"))
        return Himpunan(elements)
    except Exception as e:
        console.print(f"[red]Error parsing set '{set_str}': {e}[/red]")
        raise typer.Exit(1)


@app.command()
def union(
    set1: str = typer.Argument(..., help="First set in format {1,2,3}"),
    set2: str = typer.Argument(..., help="Second set in format {4,5,6}")
):
    """Calculate the union of two sets."""
    h1 = parse_set(set1)
    h2 = parse_set(set2)
    result = h1 + h2
    
    console.print(f"[cyan]Set 1:[/cyan] {h1}")
    console.print(f"[cyan]Set 2:[/cyan] {h2}")
    console.print(f"[green]Union (Set1 ∪ Set2):[/green] {result}")


@app.command()
def intersection(
    set1: str = typer.Argument(..., help="First set in format {1,2,3}"),
    set2: str = typer.Argument(..., help="Second set in format {4,5,6}")
):
    """Calculate the intersection of two sets."""
    h1 = parse_set(set1)
    h2 = parse_set(set2)
    result = h1 / h2
    
    console.print(f"[cyan]Set 1:[/cyan] {h1}")
    console.print(f"[cyan]Set 2:[/cyan] {h2}")
    console.print(f"[green]Intersection (Set1 ∩ Set2):[/green] {result}")


@app.command()
def difference(
    set1: str = typer.Argument(..., help="First set in format {1,2,3}"),
    set2: str = typer.Argument(..., help="Second set in format {4,5,6}")
):
    """Calculate the difference of two sets."""
    h1 = parse_set(set1)
    h2 = parse_set(set2)
    result = h1 - h2
    
    console.print(f"[cyan]Set 1:[/cyan] {h1}")
    console.print(f"[cyan]Set 2:[/cyan] {h2}")
    console.print(f"[green]Difference (Set1 \\ Set2):[/green] {result}")


@app.command()
def symmetric_difference(
    set1: str = typer.Argument(..., help="First set in format {1,2,3}"),
    set2: str = typer.Argument(..., help="Second set in format {4,5,6}")
):
    """Calculate the symmetric difference of two sets."""
    h1 = parse_set(set1)
    h2 = parse_set(set2)
    result = h1 * h2
    
    console.print(f"[cyan]Set 1:[/cyan] {h1}")
    console.print(f"[cyan]Set 2:[/cyan] {h2}")
    console.print(f"[green]Symmetric Difference (Set1 △ Set2):[/green] {result}")


@app.command()
def cartesian(
    set1: str = typer.Argument(..., help="First set in format {1,2,3}"),
    set2: str = typer.Argument(..., help="Second set in format {a,b,c}")
):
    """Calculate the cartesian product of two sets."""
    h1 = parse_set(set1)
    h2 = parse_set(set2)
    result = h1 ** h2
    
    console.print(f"[cyan]Set 1:[/cyan] {h1}")
    console.print(f"[cyan]Set 2:[/cyan] {h2}")
    console.print(f"[green]Cartesian Product (Set1 × Set2):[/green] {result}")


@app.command()
def complement(
    subset: str = typer.Argument(..., help="Subset in format {1,2,3}"),
    universal: str = typer.Argument(..., help="Universal set in format {1,2,3,4,5,6}")
):
    """Calculate the complement of a set."""
    h_subset = parse_set(subset)
    h_universal = parse_set(universal)
    result = h_subset.komplement(h_universal)
    
    console.print(f"[cyan]Subset:[/cyan] {h_subset}")
    console.print(f"[cyan]Universal Set:[/cyan] {h_universal}")
    console.print(f"[green]Complement:[/green] {result}")


@app.command()
def powerset(
    set_input: str = typer.Argument(..., help="Set in format {1,2,3}")
):
    """Calculate the power set of a set."""
    h = parse_set(set_input)
    result = abs(h)
    
    console.print(f"[cyan]Set:[/cyan] {h}")
    console.print(f"[green]Power Set (2^{len(h)} = {len(result)} subsets):[/green]")
    
    # Display power set elements in a nice format
    subsets = list(result.elems)
    for i, subset in enumerate(sorted(subsets, key=lambda x: len(x.elems))):
        console.print(f"  {i+1:2d}. {subset}")


@app.command()
def relations(
    set1: str = typer.Argument(..., help="First set in format {1,2,3}"),
    set2: str = typer.Argument(..., help="Second set in format {4,5,6}")
):
    """Show all relationships between two sets."""
    h1 = parse_set(set1)
    h2 = parse_set(set2)
    
    table = Table(title="Set Relationships")
    table.add_column("Relationship", style="cyan")
    table.add_column("Result", style="green")
    table.add_column("Symbol", style="yellow")
    
    table.add_row("Set 1 equals Set 2", str(h1 == h2), "Set1 = Set2")
    table.add_row("Set 1 subset of Set 2", str(h1 <= h2), "Set1 ⊆ Set2")
    table.add_row("Set 1 proper subset of Set 2", str(h1 < h2), "Set1 ⊂ Set2")
    table.add_row("Set 1 superset of Set 2", str(h1 >= h2), "Set1 ⊇ Set2")
    table.add_row("Set 1 proper superset of Set 2", str(h1 > h2), "Set1 ⊃ Set2")
    
    console.print(f"[cyan]Set 1:[/cyan] {h1}")
    console.print(f"[cyan]Set 2:[/cyan] {h2}")
    console.print(table)


@app.command()
def demo():
    """Run a demonstration of set operations."""
    console.print("[bold cyan]Set Function Demo[/bold cyan]\n")
    
    # Create sample sets
    h1 = Himpunan([1, 2, 3, 4])
    h2 = Himpunan([3, 4, 5, 6])
    universal = Himpunan([1, 2, 3, 4, 5, 6, 7, 8, 9])
    
    console.print(f"[cyan]Set A:[/cyan] {h1}")
    console.print(f"[cyan]Set B:[/cyan] {h2}")
    console.print(f"[cyan]Universal Set:[/cyan] {universal}\n")
    
    operations = [
        ("Union", h1 + h2, "A ∪ B"),
        ("Intersection", h1 / h2, "A ∩ B"),
        ("Difference", h1 - h2, "A \\ B"),
        ("Symmetric Difference", h1 * h2, "A △ B"),
        ("Complement of A", h1.komplement(universal), "A'"),
    ]
    
    for name, result, symbol in operations:
        console.print(f"[green]{name} ({symbol}):[/green] {result}")
    
    console.print(f"\n[green]Power Set of A (2^{len(h1)} = {len(abs(h1))} subsets)[/green]")
    power_set = abs(h1)
    for i, subset in enumerate(sorted(power_set.elems, key=lambda x: len(x.elems))):
        console.print(f"  {i+1}. {subset}")


if __name__ == "__main__":
    app()
