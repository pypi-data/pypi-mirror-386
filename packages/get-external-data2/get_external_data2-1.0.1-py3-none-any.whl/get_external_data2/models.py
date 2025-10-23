"""Pydantic configuration file model."""

from dataclasses import dataclass
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


@dataclass
class DbParams:
    """Just a wrapper to pass less arguments."""

    database: str = "gis"
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    renderuser: str | None = None


@dataclass
class Opts:
    """Just a wrapper to pass less arguments."""

    no_update: bool
    force: bool
    cache: bool
    delete_cache: bool
    force_import: bool


class ImportType(StrEnum):
    """Supprted import file types."""

    SHAPEFILE = "shp"


class ArchiveType(StrEnum):
    """Supported archive file types."""

    ZIP = "zip"


class ConfigSettings(BaseModel):
    """Settings section of configuration file."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    temp_schema: str = Field(default="loading", description="Temporary schema name")
    data_schema: str = Field(alias="schema", default="public", description="Data schema name")
    data_dir: str = Field(default="data", description="Download data directory")
    database: str = Field(default="gis", description="Database name")
    host: str = Field(default="/var/run/postgresql", description="Database host or socket directory")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    username: str = Field(default="gis", description="Database connection user name")
    password: str | None = Field(default=None, description="Database connection password")
    renderuser: str | None = Field(default=None, description="User to grant access for rendering")
    metadata_table: str = Field(default="external_data", description="Metadata table name")


class SourceArchive(BaseModel):
    """Archive part of source configuration."""

    model_config = ConfigDict(extra="forbid")

    format: ArchiveType = Field(default=ArchiveType.ZIP, description="Archive type")
    files: list[str] = Field(description="List of files in archive")


class Source(BaseModel):
    """Singular source."""

    model_config = ConfigDict(extra="forbid")

    type: ImportType = Field(default=ImportType.SHAPEFILE, description="Import file type")
    url: AnyHttpUrl = Field(description="URL of file to download")
    file: str = Field(description="Path to file in archive")
    ogropts: list[str] = Field(default_factory=list, description="Additional ogr2ogr arguments")
    archive: SourceArchive = Field(description="Archive description")


class Config(BaseModel):
    """Configuration file."""

    model_config = ConfigDict(extra="forbid")

    settings: ConfigSettings = Field(description="Script configuration")
    sources: dict[str, Source] = Field(description="Sources definition")
