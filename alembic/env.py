import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config # Важно: асинхронный импорт
from alembic import context

# Импорт URL и моделей
from app.database import DATABASE_URL
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in target_metadata.tables
    if type_ == "index" and name and (name.startswith("idx_tiger") or name.startswith("tiger")):
        return False
    return True

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object
    )
    with context.begin_transaction():
        context.run_migrations()

# Вспомогательная функция для запуска миграций в синхронном стиле внутри асинхронного потока
def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        include_object=include_object
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    # Используем асинхронный движок
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # run_sync выполняет синхронную функцию do_run_migrations
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запуск асинхронной функции через asyncio.run
    asyncio.run(run_migrations_online())


# from logging.config import fileConfig

# from sqlalchemy import engine_from_config, pool

# from alembic import context

# # Import database URL and models
# from app.database import DATABASE_URL
# from app.models import Base

# # this is the Alembic Config object, which provides
# # access to the values within the .ini file in use.
# config = context.config

# # Override sqlalchemy.url with our DATABASE_URL from environment
# config.set_main_option("sqlalchemy.url", DATABASE_URL)

# # Interpret the config file for Python logging.
# # This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # add your model's MetaData object here
# # for 'autogenerate' support
# target_metadata = Base.metadata

# # other values from the config, defined by the needs of env.py,
# # can be acquired:
# # my_important_option = config.get_main_option("my_important_option")
# # ... etc.

# def include_object(object, name, type_, reflected, compare_to):
#     # Если это таблица, проверяем, описана ли она в наших моделях
#     if type_ == "table":
#         return name in target_metadata.tables

#     # Для индексов: игнорируем системные индексы PostGIS (обычно начинаются с idx_tiger или tiger)
#     if type_ == "index" and name and (name.startswith("idx_tiger") or name.startswith("tiger")):
#         return False

#     return True

# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode.

#     This configures the context with just a URL
#     and not an Engine, though an Engine is acceptable
#     here as well.  By skipping the Engine creation
#     we don't even need a DBAPI to be available.

#     Calls to context.execute() here emit the given string to the
#     script output.

#     """
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#         include_object=include_object
#     )


#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode.

#     In this scenario we need to create an Engine
#     and associate a connection with the context.

#     """
#     connectable = engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection,
#             target_metadata=target_metadata,
#             include_object=include_object
#             )

#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()
