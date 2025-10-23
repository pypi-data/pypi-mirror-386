#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

"""
Downloads and imports shapefiles into OSM database.

This is a complete ripoff and drop-in replacement for original
get-external-data.py script with better logging and actual Last-Modified header
check.
"""

import json
import logging
import os
import subprocess  # noqa: S404
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from signal import SIGTERM, signal
from typing import Any
from zipfile import ZipFile

import psycopg
import yaml
from argcomplete import autocomplete
from argcomplete.completers import DirectoriesCompleter, FilesCompleter
from pydantic import ValidationError

from .data_getter import ExternalDataGetter
from .db import Table
from .models import ArchiveType, Config, DbParams, Opts

__prog__ = "get-external-data2"
__version__ = "1.0.1"
__status__ = "Development"
__author__ = "Alexander Pozlevich"
__email__ = "apozlevich@gmail.com"

logger = logging.getLogger(__name__)


def _handle_sigterm(*_) -> None:
    logger.warning("Terminated by signal, exiting cleanly")
    sys.exit(1)


def _parse_cli_args() -> Namespace:
    """
    Prepare argparse and parse CLI arguments.

    Returns:
        Namespace of arguments.
    """

    cli_args_parser = ArgumentParser(
        prog=__prog__,
        description=__doc__,
        epilog=f"Written by {__author__} <{__email__}>.",
        formatter_class=lambda prog: ArgumentDefaultsHelpFormatter(prog=prog, max_help_position=120),
    )
    cli_args_parser.add_argument("--version", action="version", version=f"{__prog__} v{__version__} ({__status__})")

    quiet_or_verbose = cli_args_parser.add_mutually_exclusive_group()
    quiet_or_verbose.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="be more verbose",
    )
    quiet_or_verbose.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="only report serious problems",
    )

    cli_args_parser.add_argument(
        "-c",
        "--config",
        default="external-data.yml",
        metavar="file",
        help="name of configuration file",
    ).completer = FilesCompleter(directories=False)  # pyright: ignore[reportAttributeAccessIssue]

    cli_args_parser.add_argument(
        "--dump-json-schema",
        action="store_true",
        help="output configuration file JSON schema and exit",
    )

    import_args = cli_args_parser.add_argument_group(title="importing options")
    force_or_no_update = import_args.add_mutually_exclusive_group()
    force_or_no_update.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="download and import new data, even if not required",
    )
    force_or_no_update.add_argument(
        "--no-update",
        action="store_true",
        help="don't download newer data than what is locally available (either in cache or table)",
    )
    import_args.add_argument(
        "--force-import",
        action="store_true",
        help="import data into table even if may not be needed",
    )

    caching_args = cli_args_parser.add_argument_group(title="caching options")
    caching_args.add_argument(
        "-C",
        "--cache",
        action="store_true",
        help="cache downloaded data. Useful if you'll have your database volume deleted in the future",
    )
    caching_args.add_argument(
        "--delete-cache",
        action="store_true",
        help="perform as usual, but delete cached data",
    )
    caching_args.add_argument(
        "-D",
        "--data",
        metavar="dir",
        help="override data download directory",
    ).completer = DirectoriesCompleter()  # pyright: ignore[reportAttributeAccessIssue]

    db_args = cli_args_parser.add_argument_group(title="database options")
    db_args.add_argument(
        "-d",
        "--database",
        "--dbname",
        metavar="name",
        help="override database name to connect to",
    )
    db_args.add_argument(
        "-H",
        "--host",
        "--hostname",
        metavar="hostname",
        help="override database server host or socket directory",
    )
    db_args.add_argument(
        "-P",
        "--port",
        type=int,
        metavar="port",
        help="override database server port",
    )
    db_args.add_argument(
        "-U",
        "--username",
        metavar="username",
        help="override database user name",
    )
    db_args.add_argument(
        "-w",
        "--password",
        metavar="password",
        help="override database password",
    )
    db_args.add_argument(
        "-R",
        "--renderuser",
        metavar="username",
        help="user to grant access for rendering",
    )

    autocomplete(argument_parser=cli_args_parser)
    return cli_args_parser.parse_args()


def _setup_logging(args: Namespace) -> None:
    """
    Prepare stdlib logging.

    Args:
        args: Namespace of argparse's args.
    """

    logging_level = logging.INFO

    if args.verbose:
        logging_level = logging.DEBUG

    elif args.quiet:
        logging_level = logging.WARNING

    logging.basicConfig(
        format="%(levelname)s [%(asctime)s.%(msecs)03d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging_level,
    )


def _read_config(filename: str) -> Config:
    """
    Read and parse configuration file.

    Args:
        filename: Path to configuration file.

    Returns:
        Configuration object.

    Raises:
        ValidationError: If the configuration file is malformed.
        OSError: If the file could not be opened or read.
    """  # noqa: DOC502

    try:
        config_text = Path(filename).read_text(encoding="utf-8")
        config_dict: dict[str, Any] = yaml.safe_load(config_text) or {}
        config = Config.model_validate(config_dict)

    except ValidationError:
        logger.exception("Failed to parse configuration file %s", filename)
        sys.exit(1)

    except OSError:
        logger.exception("Failed to load configuration file %s", filename)
        sys.exit(1)

    return config


def _ogr2ogr(db_params: DbParams, source: Path, target: str, ogropts: list[str] | None = None) -> None:
    """
    Call ogr2ogr for actual data import.

    Args:
        db_params: dataclass with PostgreSQL parameters.
        source: path of source shapefile.
        target: schema and table name to upload into.
        ogropts: optinal list of additional command-line arguments for ogr2ogr.
    """

    ogrpg = f"PG:dbname={db_params.database}"

    if db_params.port is not None:
        ogrpg += f" port={db_params.port}"

    if db_params.username is not None:
        ogrpg += f" user={db_params.username}"

    if db_params.host is not None:
        ogrpg += f" host={db_params.host}"

    if db_params.password is not None:
        ogrpg += f" password={db_params.password}"

    ogrcommand = [
        "ogr2ogr",
        "-f",
        "PostgreSQL",
        "-lco",
        "GEOMETRY_NAME=way",
        "-lco",
        "SPATIAL_INDEX=NONE",  # It's "NONE" since GDAL 3.7, not "FALSE".
        "-lco",
        "EXTRACT_SCHEMA_FROM_LAYER_NAME=YES",
        "-nln",
        target,
    ]

    if ogropts is not None:
        ogrcommand += ogropts

    ogrcommand += [ogrpg, source]
    env = {**os.environ, "PGCLIENTENCODING": "UTF8"}
    logger.info("Importing into database")
    logger.debug("Running %s", subprocess.list2cmdline(ogrcommand))

    try:
        result = subprocess.run(ogrcommand, check=True, capture_output=True, text=True, env=env)  # noqa: S603

    except subprocess.CalledProcessError as exc:
        logger.error("ogr2ogr returned %d", exc.returncode)  # noqa: TRY400
        logger.error("Commandline was %s", subprocess.list2cmdline(exc.cmd))  # noqa: TRY400
        logger.error("Output was:\n%s", exc.stdout)  # noqa: TRY400
        logger.error("Error was:\n%s", exc.stderr)  # noqa: TRY400

    else:
        logger.debug("ogr2ogr output:\n%s", result.stdout)

    logger.info("Import complete")


def _main(config: Config, data_dir: Path, db_params: DbParams, opts: Opts) -> None:
    """
    Execute main routine.

    Args:
        config: configuration object.
        data_dir: Path object of data directory.
        db_params: dataclass with db-related settings.
        opts: dataclass with options that may change execution flow.
    """

    with (
        psycopg.connect(
            dbname=db_params.database,
            host=db_params.host,
            port=db_params.port,
            user=db_params.username,
            password=db_params.password,
        ) as connection,
        ExternalDataGetter() as external_data_getter,
    ):
        for i, (name, source) in enumerate(config.sources.items(), start=1):
            logger.info("[%d/%d] Processing shapefile %s", i, len(config.sources), name)
            table = Table(
                name=name,
                connection=connection,
                temp_schema=config.settings.temp_schema,
                data_schema=config.settings.data_schema,
                metadata_table=config.settings.metadata_table,
            )
            external_data = external_data_getter.obtain(
                url=str(source.url),
                data_dir=data_dir,
                last_modified=table.last_modified,
                opts=opts,
            )

            if external_data is None:
                continue

            working_dir = data_dir / name
            rmtree(working_dir, ignore_errors=True)
            working_dir.mkdir(parents=True, exist_ok=True)

            # More supported archive types may be added later and this check
            # should be moved into some kind of mapping of extraction methods.

            if source.archive.format == ArchiveType.ZIP:
                logger.info("Decompressing")
                with ZipFile(BytesIO(external_data.content)) as archive:
                    for member in source.archive.files:
                        archive.extract(member, working_dir)

            _ogr2ogr(
                db_params=db_params,
                source=working_dir / source.file,
                target=f"{config.settings.temp_schema}.{name}",
                ogropts=source.ogropts,
            )

            logger.info("Running optimizations")
            table.index()

            if db_params.renderuser is not None:
                logger.info("Granting SELECT to %s", db_params.renderuser)
                table.grant_access(db_params.renderuser)

            table.replace(external_data.last_modified)

            try:
                rmtree(working_dir)

            except OSError:
                logger.exception("Failed to cleanup %s", working_dir)

        if opts.delete_cache:
            try:
                rmtree(data_dir)

            except OSError:
                logger.exception("Failed to delete cache %s", data_dir)


def _bootstrap() -> None:
    cli_args = _parse_cli_args()
    _setup_logging(args=cli_args)

    if cli_args.dump_json_schema:
        schema = Config.model_json_schema()
        schema["$meta"] = {"program": __prog__, "version": __version__}
        print(json.dumps(schema, indent=2))  # noqa: T201
        sys.exit(0)

    config = _read_config(filename=cli_args.config)
    data_path = cli_args.data or config.settings.data_dir
    try:
        data_dir = Path(data_path)
        data_dir.mkdir(parents=True, exist_ok=True)

    except OSError:
        logger.exception("Failed to initialize data directory %s", data_path)
        sys.exit(1)

    # If something is None, let psycopg and libpq deal with it.
    db_params = DbParams(
        database=cli_args.database or config.settings.database,
        host=cli_args.host or config.settings.host,
        port=cli_args.port or config.settings.port,
        username=cli_args.username or config.settings.username,
        password=cli_args.password or config.settings.password,
        renderuser=cli_args.renderuser or config.settings.renderuser,
    )

    opts = Opts(
        no_update=cli_args.no_update,
        force=cli_args.force,
        cache=cli_args.cache,
        delete_cache=cli_args.delete_cache,
        force_import=cli_args.force_import,
    )

    _main(config=config, data_dir=data_dir, db_params=db_params, opts=opts)


if __name__ == "__main__":
    signal(SIGTERM, _handle_sigterm)  # pyright: ignore[reportUnknownArgumentType]
    with suppress(KeyboardInterrupt):
        _bootstrap()
