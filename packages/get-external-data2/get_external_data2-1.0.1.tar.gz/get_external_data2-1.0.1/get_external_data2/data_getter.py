"""Main logic of downloading shapefiles."""

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import format_datetime, parsedate_to_datetime
from io import BytesIO
from logging import getLogger
from pathlib import Path
from typing import Any, Self
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from .models import Opts

PROGRESS_CHUNK_SIZE = 8192

logger = getLogger(__name__)


@dataclass
class ExternalData:
    """Represents downloaded or cached file."""

    content: bytes
    last_modified: datetime


class ExternalDataGetter:
    """Performs Last-Modify checks and provides actual archive."""

    USER_AGENT = "get-external-data.py/osm-carto"

    def __init__(self) -> None:
        """Perform Last-Modify checks and provides actual archive."""

        self.session = requests.session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def __enter__(self) -> Self:
        """
        Work as context manager.

        Returns:
            Self instance.
        """

        return self

    def __exit__(self, *_: object, **__: Any) -> None:
        """Exit from context manager."""

        self.session.close()

    def _is_download_required(self, url: str, last_modified: datetime | None = None) -> bool:  # noqa: PLR0911
        """
        Check if remote file is newer.

        Args:
            url: URL of remote file.
            last_modified: known value from database.

        Returns:
            True if remote file is newer.
        """

        # If we don't know our Last-Modified, obviously we need to download
        if last_modified is None:
            return True

        # Good servers supports HEAD and honor If-Modified-Since.
        headers = {"If-Modified-Since": format_datetime(last_modified)}
        try:
            with self.session.head(url=url, headers=headers, allow_redirects=True, timeout=(5, 30)) as response:
                logger.debug(
                    "HEAD request finished with %d, Last-Modified is %s",
                    response.status_code,
                    response.headers.get("Last-Modified"),
                )

                # If we receive 304 Not Modified -- we do not download.
                if response.status_code == requests.codes.not_modified:
                    return False

                # No 304, but our Last-Modified is newer or equal — skip download.
                try:
                    if "Last-Modified" in response.headers and last_modified >= parsedate_to_datetime(response.headers["Last-Modified"]):
                        return False

                except (ValueError, TypeError):
                    logger.exception("Failed to parse Last-Modified from HEAD request: %s", response.headers.get("Last-Modified"))
                    return False

        except requests.RequestException:
            logger.exception("Unable to HEAD, proceeding to GET request")

        # HEAD check failed, but we can do GET request and parse headers.
        try:
            with self.session.get(url=url, headers=headers, allow_redirects=True, timeout=(5, 30), stream=True) as response:
                logger.debug(
                    "GET request finished with %d, Last-Modified is %s",
                    response.status_code,
                    response.headers.get("Last-Modified"),
                )

                # We still can get 304 response.
                if response.status_code == requests.codes.not_modified:
                    return False

                # Check Last-Modified one more time. This should return False if our state is actual.
                try:
                    return not (
                        "Last-Modified" in response.headers and last_modified <= parsedate_to_datetime(response.headers["Last-Modified"])
                    )

                except (ValueError, TypeError):
                    logger.exception("Failed to parse Last-Modified from GET request: %s", response.headers.get("Last-Modified"))
                    return False

                # ...and True if any of checks failed (default fallback).

        except requests.RequestException:
            logger.exception("Failed to do GET request, skipping file")
            return False

    def obtain(self, url: str, data_dir: Path, opts: Opts, last_modified: datetime | None = None) -> ExternalData | None:  # noqa: C901, PLR0911, PLR0912, PLR0915
        """
        Check Last-Modified and obtain shapefile.

        Args:
            url: URL to check if remote file is newer.
            data_dir: path to cache directory.
            opts: dataclass which controls process.
            last_modified: known value from database.

        Returns:
            None if no action is required or newer shapefile as object.

        Raises:
            RuntimeError: if was unable to determine which file is actual.
        """

        # If we are in --no-update mode and there is something in DB, just return.
        if opts.no_update and last_modified:
            logger.info("Skipping update since --no-update flag is present")
            return None

        logger.debug("Last-Modified value from database is %s", last_modified)

        # Read cached file.
        filename = data_dir / Path(urlparse(url).path).name
        last_modified_file = filename.with_name(filename.name + ".lastmod")

        cached_file_last_modified = None
        if filename.exists() and last_modified_file.exists():
            try:
                cached_file_last_modified = parsedate_to_datetime(last_modified_file.read_text())

            except (ValueError, TypeError):
                logger.exception("Failed to parse Last-Modified from .lastmod file: %s", last_modified_file.read_text())
                return None

            logger.debug("Cached file Last-Modified value: %s", cached_file_last_modified)

        # Check what is more recent: DB or cached file.
        if last_modified is not None and cached_file_last_modified is not None:
            check_last_modified = max(last_modified, cached_file_last_modified)

        elif last_modified is not None:
            check_last_modified = last_modified

        elif cached_file_last_modified is not None:
            check_last_modified = cached_file_last_modified

        else:
            check_last_modified = None

        # Now check if remote file is newer.
        download_required = self._is_download_required(url=url, last_modified=check_last_modified)
        logger.info("Download required: %s", download_required)

        if (
            not download_required
            and last_modified is not None
            and cached_file_last_modified is not None
            and last_modified >= cached_file_last_modified
        ):
            logger.info("Database is in actual state")
            return None

        result = None

        # If cached file is newest, return it. This could break when .lastmod
        # file is missing. Let's just don't think about it.
        if not download_required and cached_file_last_modified is not None:  # noqa: PLR1702
            logger.info("Local file is actual, using it")
            result = ExternalData(
                content=filename.read_bytes(),
                last_modified=cached_file_last_modified,
            )

        # If download if required, actually download the file.
        elif download_required:
            try:
                with self.session.get(url=url, allow_redirects=True, timeout=(5, 30), stream=True) as response:
                    response.raise_for_status()

                    if response.status_code == requests.codes.ok:
                        try:
                            latest_modified = parsedate_to_datetime(response.headers.get("Last-Modified", None)) or datetime.now(tz=UTC)

                        except (ValueError, TypeError):
                            logger.exception("Failed to parse Last-Modified from actual data: %s", response.headers.get("Last-Modified"))
                            return None

                        if not cached_file_last_modified and not latest_modified:
                            msg = "Unable to determine both cache and remote Last-Modified"
                            raise RuntimeError(msg)

                        total = int(response.headers.get("Content-Length", 0)) or None
                        buffer = BytesIO()

                        with tqdm(total=total, unit="B", unit_scale=True, unit_divisor=1024, desc="Downloading") as bar:
                            for chunk in response.iter_content(chunk_size=PROGRESS_CHUNK_SIZE):
                                buffer.write(chunk)
                                bar.update(len(chunk))

                        result = ExternalData(
                            content=buffer.getvalue(),
                            last_modified=latest_modified,
                        )

                        if opts.cache and result:
                            filename.write_bytes(result.content)
                            last_modified_file.write_text(format_datetime(result.last_modified))

                    else:
                        logger.error("Got unexpected response code %d", response.status_code)
                        logger.error("File was not downloaded")
                        return None

            except requests.RequestException:
                logger.exception("Failed to fetch file, skipping")
                return None

        return result
