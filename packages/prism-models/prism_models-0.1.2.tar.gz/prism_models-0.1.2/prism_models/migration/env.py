import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Add prism-models to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import models and configuration - after path setup
from prism_models.config import settings
from prism_models.base import Base

# Import all models to ensure they're registered
import prism_models.agent_profile
import prism_models.chat
import prism_models.content
import prism_models.feedback

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from environment
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.PG_DATABASE_URL_PRISM)

# Import all models to ensure they're registered with Base.metadata

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Other values from the config can be acquired as needed


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
        compare_type=True,  # Compare column types
        compare_server_default=True,  # Compare server defaults
        include_schemas=True,  # Include schema-specific tables
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Compare column types for better autogeneration
        compare_server_default=True,  # Compare server defaults
        include_schemas=True,  # Include schema-specific tables (chat schema)
        render_as_batch=False,  # PostgreSQL doesn't need batch mode
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode for async engines."""
    # Use async engine for PostgreSQL
    connectable = create_async_engine(
        settings.PG_DATABASE_URL_PRISM,
        poolclass=pool.NullPool,
        echo=settings.is_development,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    For async databases, we use run_async_migrations.
    For sync databases, we use the traditional approach.
    """
    database_url = config.get_main_option("sqlalchemy.url")

    if "asyncpg" in database_url or "aiosqlite" in database_url:
        # Async database - use async migrations
        asyncio.run(run_async_migrations())
    else:
        # Sync database - use traditional approach
        from sqlalchemy import engine_from_config

        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
