import os
import importlib.util
import math
import operator
from rich.progress import Progress

def clear():
    os.system("cls" if os.name == 'nt' else "clear")

def nod(numbers):
    return reduce(operator.gcd, numbers)

def nok(numbers):
    return reduce(lambda a, b: abs(a * b) // operator.gcd(a, b), numbers)

def average(scores):
    if not scores:
        return 0
    return sum(scores) / len(scores)

def importlibs(libs):
    with Progress() as progress:
        task = progress.add_task("[green]Loading libraries...", total=len(libs))
        for lib in libs:
            spec = importlib.util.find_spec(lib)
            if spec is None:
                os.system(f"pip install --quiet {lib}")
            progress.update(task, advance=1)