from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.config import settings

# Import all shared models from app.models
from app.models import *  # Import all shared models

# Import service-specific models for centralized migrations
# User Service models
try:
    # Add services/user-service directory to path for imports
    user_service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'user-service')
    if user_service_path not in sys.path:
        sys.path.insert(0, user_service_path)
    
    # Import user-service models (these use their own Base, but we need to import them for Alembic to see them)
    # Note: These models should ideally use app.database.Base for consistency
    from models import *  # User, OTPVerification
except ImportError as e:
    # Service models may not exist or may use app.models - that's okay
    pass

# Import kraken-service models if they exist
try:
    kraken_service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'kraken-service')
    if kraken_service_path not in sys.path:
        sys.path.insert(0, kraken_service_path)
    from models import *
except ImportError:
    # Kraken service may not have its own models (uses app.models) - that's okay
    pass

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# This includes metadata from all imported models (app.models + service models)
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

