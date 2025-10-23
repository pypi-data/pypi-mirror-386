import logging
from logging.config import fileConfig

from alembic import context
from fastapi_rtk import Setting, metadatas, smart_run_sync
from fastapi_rtk.const import DEFAULT_METADATA_KEY, FASTAPI_RTK_TABLES
from fastapi_rtk.db import DatabaseSessionManager
from sqlalchemy import Connection, MetaData

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# add your model's MetaData objects here
# for 'autogenerate' support.  These must be set
# up to hold just those tables targeting a
# particular database. table.tometadata() may be
# helpful here in case a "copy" of
# a MetaData is needed.
# from myapp import mymodel
# target_metadata = {
#       'URL1':mymodel.metadata1,
#       'engine2':mymodel.metadata2
# }
target_metadata = dict[str, MetaData]()

MAIN_DATABASE = Setting.SQLALCHEMY_DATABASE_URI
if not MAIN_DATABASE:
    raise Exception("SQLALCHEMY_DATABASE_URI not set in config")
target_metadata[DEFAULT_METADATA_KEY] = metadatas[DEFAULT_METADATA_KEY]

BINDS = Setting.SQLALCHEMY_BINDS or {}
for name in BINDS.keys():
    if name == DEFAULT_METADATA_KEY:
        raise Exception(
            f"SQLALCHEMY_BINDS cannot have a key named '{DEFAULT_METADATA_KEY}'"
        )
    target_metadata[name] = metadatas[name]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# this callback is used to prevent an auto-migration from being generated
# when there are no changes to the schema
# reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
def process_revision_directives(context, revision, directives):
    if "autogenerate" in config.cmd_opts:
        script = directives[0]
        if len(script.upgrade_ops_list) >= len(BINDS.keys()) + 1:
            empty = True
            for upgrade_ops in script.upgrade_ops_list:
                if not upgrade_ops.is_empty():
                    empty = False
            if empty:
                directives[:] = []
                logger.info("No changes in schema detected.")


# ignore object that are in the FASTAPI_RTK_TABLES
def include_object(object, name, type_, reflected, compare_to):
    if name in FASTAPI_RTK_TABLES:
        return False

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # for the --sql use case, run migrations for each URL into
    # individual files.

    for name, metadata in target_metadata.items():
        logger.info("Migrating database %s" % name)
        file_ = "%s.sql" % name
        logger.info("Writing output to %s" % file_)
        with open(file_, "w") as buffer:
            context.configure(
                url=name,
                output_buffer=buffer,
                target_metadata=metadata,
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
            )
            with context.begin_transaction():
                context.run_migrations()

    # engines = {}
    # for name in re.split(r",\s*", db_names):
    #     engines[name] = rec = {}
    #     rec["url"] = context.config.get_section_option(name, "sqlalchemy.url")

    # for name, rec in engines.items():
    #     logger.info("Migrating database %s" % name)
    #     file_ = "%s.sql" % name
    #     logger.info("Writing output to %s" % file_)
    #     with open(file_, "w") as buffer:
    #         context.configure(
    #             url=rec["url"],
    #             output_buffer=buffer,
    #             target_metadata=target_metadata.get(name),
    #             literal_binds=True,
    #             dialect_opts={"paramstyle": "named"},
    #         )
    #         with context.begin_transaction():
    #             context.run_migrations(engine_name=name)


def do_run_migrations(
    connection: Connection,
    upgrade_token: str,
    downgrade_token: str,
    target_metadata: MetaData,
    engine_name: str,
) -> None:
    context.configure(
        connection=connection,
        upgrade_token=upgrade_token,
        downgrade_token=downgrade_token,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations(engine_name=engine_name)


async def run_async_migrations() -> None:
    """
    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    db = DatabaseSessionManager()
    db.init_db(MAIN_DATABASE, BINDS)

    # for the direct-to-DB use case, start a transaction on all
    # engines, then run all migrations, then commit all transactions.

    for name, metadata in target_metadata.items():
        logger.info("Migrating database %s" % name)
        async with db.connect(name) as connection:
            if isinstance(connection, Connection):
                do_run_migrations(
                    connection, f"{name}_upgrades", f"{name}_downgrades", metadata, name
                )
            else:
                await connection.run_sync(
                    do_run_migrations,
                    f"{name}_upgrades",
                    f"{name}_downgrades",
                    metadata,
                    name,
                )

    await db.close()

    # engines = {}
    # for name in re.split(r",\s*", db_names):
    #     engines[name] = rec = {}
    #     rec["engine"] = engine_from_config(
    #         context.config.get_section(name, {}),
    #         prefix="sqlalchemy.",
    #         poolclass=pool.NullPool,
    #     )

    # for name, rec in engines.items():
    #     engine = rec["engine"]
    #     rec["connection"] = conn = engine.connect()

    #     if USE_TWOPHASE:
    #         rec["transaction"] = conn.begin_twophase()
    #     else:
    #         rec["transaction"] = conn.begin()

    # try:
    #     for name, rec in engines.items():
    #         logger.info("Migrating database %s" % name)
    #         context.configure(
    #             connection=rec["connection"],
    #             upgrade_token="%s_upgrades" % name,
    #             downgrade_token="%s_downgrades" % name,
    #             target_metadata=target_metadata.get(name),
    #         )
    #         context.run_migrations(engine_name=name)

    #     if USE_TWOPHASE:
    #         for rec in engines.values():
    #             rec["transaction"].prepare()

    #     for rec in engines.values():
    #         rec["transaction"].commit()
    # except:
    #     for rec in engines.values():
    #         rec["transaction"].rollback()
    #     raise
    # finally:
    #     for rec in engines.values():
    #         rec["connection"].close()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    smart_run_sync(run_async_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
