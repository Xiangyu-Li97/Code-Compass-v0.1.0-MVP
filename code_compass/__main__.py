"""Allow running code_compass as a module: python -m code_compass"""

from .cli import cli

if __name__ == '__main__':
    cli()
