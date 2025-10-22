# All code comments in English as requested
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, conint

##############################################################
# Shared strict base: forbid unknown fields everywhere
##############################################################


class StrictBaseModel(BaseModel):
    # Forbid extra keys globally for all derived models.
    model_config = ConfigDict(
        extra="forbid",  # disallow unknown/extra fields
        str_strip_whitespace=True,  # (optional) trim strings
        populate_by_name=True,  # allow population by field name/alias
    )


##############################################################
# Extract
##############################################################


class ExtractGenericOdbcConfig(StrictBaseModel):
    """ODBC-based extraction from a generic ODBC source."""

    odbc_connstr: str = Field(..., description="ODBC connection string for SQL Server")
    chunk_size: conint(gt=0) = 10_000
    timeout: conint(gt=0) = 300
    table_prefix: str = ""
    table_selector: Literal["all", "join_parser"] = "all"
    tables: List[str]


class ExtractInforcomConfig(StrictBaseModel):
    """ODBC-based extraction from INFORCOM (INFOR.* tables)."""

    odbc_connstr: str = Field(..., description="ODBC connection string for SQL Server")
    chunk_size: conint(gt=0) = 10_000
    timeout: conint(gt=0) = 300
    table_prefix: str = "INFOR."
    table_selector: Literal["all", "join_parser"] = "all"
    tables: List[str]


class ExtractSAPECCConfig(StrictBaseModel):
    """ODBC-based extraction from SAP ECC (SAP.* tables)."""

    address: str = Field(..., description="Host address of the SAP HANA server")
    port: conint(gt=0, lt=65536) = 30015
    user: str = Field(..., description="Username for SAP HANA connection")
    password: str = Field(..., description="Password for SAP HANA connection")
    autocommit: bool = True  # Only read access → autocommit enabled
    chunk_size: conint(gt=0) = 10_000
    table_selector: Literal["all", "join_parser"] = "all"
    tables: List[str]


class ExtractConfigMigMan(StrictBaseModel):
    active: bool = True
    load_to_nemo: bool = True
    delete_temp_files: bool = True
    nemo_project_prefix: str = "migman_extract_"
    adapter: Literal["genericodbc", "inforcom", "sapecc"] = "genericodbc"
    genericodbc: ExtractGenericOdbcConfig
    inforcom: ExtractInforcomConfig
    sapecc: ExtractSAPECCConfig


##############################################################
# Transform
##############################################################


class TransformJoinsConfig(StrictBaseModel):
    active: bool = True
    file: str


class TransformJoinConfig(StrictBaseModel):
    active: bool = True
    joins: Dict[str, TransformJoinsConfig] = Field(
        default_factory=dict,
        description="Mapping from adapter name to its join configuration",
    )


class TransformNonEmptyConfig(StrictBaseModel):
    active: bool = True


class TransformDuplicatesConfig(StrictBaseModel):
    active: bool = True
    threshold: conint(ge=0, le=100) = 90  # similarity threshold between 0 and 100
    primary_key: str
    fields: List[str] = Field(
        default_factory=list, description="Fields to consider for duplicate detection"
    )


class TransformDuplicateConfig(StrictBaseModel):
    active: bool = True
    duplicates: Dict[str, TransformDuplicatesConfig] = Field(
        default_factory=dict,
        description="Mapping from object name to its duplicate configuration",
    )


class TransformConfigMigMan(StrictBaseModel):
    active: bool = True
    load_to_nemo: bool = True
    delete_temp_files: bool = True
    dump_files: bool = True
    nemo_project_prefix: str = "migman_transform_"
    join: TransformJoinConfig
    nonempty: TransformNonEmptyConfig
    duplicate: TransformDuplicateConfig


##############################################################
# Load
##############################################################


class LoadConfigMigMan(StrictBaseModel):
    active: bool = True
    delete_temp_files: bool = True
    delete_projects_before_load: bool = False
    nemo_project_prefix: str = ""
    development_deficiency_mining_only: bool = False
    development_load_reports_only: bool = False


##############################################################
# Full Config
##############################################################


class MigManProjectConfig(StrictBaseModel):
    project_status_file: Optional[str] = None
    projects: List[str] = Field(
        default_factory=list,
        description="List of MigMan projects to process (alternatively, use property 'project_status_file')",
    )
    multi_projects_feature_assignments: List[str] = Field(
        default_factory=list,
        description="List of MigMan projects to include in the 'feature_assignments' multi-project",
    )
    multi_projects_texts: List[str] = Field(
        default_factory=list,
        description="List of MigMan projects to include in the 'texts' multi-project",
    )


class ConfigMigMan(StrictBaseModel):
    config_version: str = "0.0.1"
    etl_directory: str = "./etl/migman"
    ui_dark_model: bool = True
    setup: MigManProjectConfig
    extract: ExtractConfigMigMan
    transform: TransformConfigMigMan
    load: LoadConfigMigMan


CONFIG_MODEL = ConfigMigMan
