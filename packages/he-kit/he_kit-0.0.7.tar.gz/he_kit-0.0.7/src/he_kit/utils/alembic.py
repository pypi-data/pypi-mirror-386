from alembic.config import Config

from .project import find_project_root, get_settings


def get_alembic_config() -> Config:
    """Load Alembic config from project root and inject DB_URL, script
    location, and log level.

    """
    root = find_project_root()

    ini_path = root / "alembic.ini"
    migrations_dir = root / "migrations"

    if not ini_path.exists():
        raise FileNotFoundError(f"No alembic.ini found in {root}")

    settings = get_settings(force_reload=True)

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.DB_URL)
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.set_main_option("logger_alembic.level", settings.LOG_LEVEL)
    cfg.config_file_name = str(ini_path)

    return cfg
