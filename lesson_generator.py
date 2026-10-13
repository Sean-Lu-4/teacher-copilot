"""Command-line entry point. Importing this file never calls an API."""
from teacher_copilot.cli import main, entrypoint

if __name__ == '__main__':
    raise SystemExit(entrypoint())
