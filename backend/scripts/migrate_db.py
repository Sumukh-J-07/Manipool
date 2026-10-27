"""Repeatable database migration runner for ManiPool."""
import os
import sys
from alembic.config import Config
from alembic import command

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def run_migrations():
    ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    alembic_cfg = Config(ini_path)
    print(f"Applying database migrations using config: {ini_path}")
    command.upgrade(alembic_cfg, "head")
    print("Database migrations applied successfully.")


if __name__ == "__main__":
    run_migrations()
