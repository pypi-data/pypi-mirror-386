"""
MigMan ETL Flow Module.

This module defines the Prefect workflow for the MigMan ETL process. It orchestrates
the extraction, transformation, and loading of data from MigMan systems into Nemo
using Prefect tasks and flows for robust pipeline execution.

The flow consists of three main phases:
1. Extract: Retrieve data from MigMan system
2. Transform: Process and clean the extracted data
3. Load: Insert the transformed data into Nemo

Each phase can be individually enabled/disabled through configuration settings.
"""

import logging
from pathlib import Path
from typing import Union, cast
from nemo_library import NemoLibrary
from prefect import flow, task, get_run_logger
from nemo_library_etl.adapter._utils.db_handler_local import ETLDuckDBHandler
from nemo_library_etl.adapter._utils.file_handler import ETLFileHandler
from nemo_library_etl.adapter.migman.config_models_migman import ConfigMigMan
from nemo_library_etl.adapter._utils.config import load_config
from nemo_library_etl.adapter.migman.extract import MigManExtract
from nemo_library_etl.adapter.migman.transform import MigManTransform
from nemo_library_etl.adapter.migman.load import MigManLoad

local_database: ETLDuckDBHandler | None = None


@flow(name="MigMan ETL Flow", log_prints=True)
def migman_flow(args) -> None:
    """
    Main Prefect flow for the MigMan ETL pipeline.

    This flow orchestrates the complete ETL process for MigMan data, including:
    - Loading pipeline configuration from JSON files
    - Conditionally executing extract, transform, and load phases based on configuration
    - Comprehensive logging and error handling throughout the process
    - Integration with Prefect for workflow orchestration, monitoring, and retry logic

    The flow follows a sequential execution pattern where each phase (extract, transform, load)
    is executed as a separate Prefect task. Each phase can be individually enabled or disabled
    through the pipeline configuration settings.

    Pipeline Configuration:
        The flow loads its configuration using the load_pipeline_config utility, which reads
        settings from JSON configuration files. The configuration includes:
        - Extract settings: table specifications and activation flags
        - Transform settings: business rules and data processing parameters
        - Load settings: target system configuration and batch parameters
        - Global settings: phase activation flags (active, active, active)

    Error Handling:
        Any exceptions raised during the ETL process will be logged and propagated by Prefect,
        enabling built-in retry mechanisms and failure notifications.

    Returns:
        None

    Raises:
        Exception: Any exception raised during the ETL process will be logged
                  and propagated by Prefect for proper error handling and monitoring.
    """
    logger = get_run_logger()
    logger.info("Starting MigMan ETL Flow")

    # load config
    nl = NemoLibrary(
        config_file=(args["config_ini"] if "config_ini" in args else None),
        environment=(args["environment"] if "environment" in args else None),
        tenant=(args["tenant"] if "tenant" in args else None),
        userid=(args["userid"] if "userid" in args else None),
        password=(args["password"] if "password" in args else None),
    )
    cfg: ConfigMigMan = cast(
        ConfigMigMan,
        load_config(
            adapter="MigMan",
            config_json_path=(
                Path(args["config_json"])
                if "config_json" in args and args["config_json"]
                else None
            ),
        ),
    )
    fh: ETLFileHandler = ETLFileHandler(nl=nl, cfg=cfg, logger=logger)

    global local_database
    with ETLDuckDBHandler(
        nl=nl,
        cfg=cfg,
        logger=logger,
        database=cfg.etl_directory + "/migman_etl.duckdb",
    ) as local_database:

        # run steps
        if cfg.extract.active:
            logger.info("Extracting objects from MigMan")
            extract(nl=nl, cfg=cfg, logger=logger, fh=fh)

        if cfg.transform.active:
            logger.info("Transforming MigMan objects")
            transform(nl=nl, cfg=cfg, logger=logger, fh=fh)

        if cfg.load.active:
            logger.info("Loading MigMan objects")
            load(nl=nl, cfg=cfg, logger=logger, fh=fh)

    logger.info("MigMan ETL Flow finished")


@task(name="Extract All Objects from MigMan")
def extract(
    nl: NemoLibrary,
    cfg: ConfigMigMan,
    logger: Union[logging.Logger, object],
    fh: ETLFileHandler,
) -> None:
    """
    Prefect task to extract data from MigMan system.

    This task handles the extraction phase of the ETL pipeline, retrieving
    data from the MigMan system based on the configuration settings.
    It manages table-specific extraction settings and respects activation flags.

    Args:
        cfg (PipelineMigMan): Pipeline configuration containing extraction settings,
                                                      including table configurations and activation flags.
        logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                               Can be a standard Python logger or Prefect logger.

    Returns:
        None

    Note:
        The actual extraction logic is delegated to the MigManExtract class.
    """
    logger.info("Extracting all MigMan objects")
    global local_database
    if not local_database:
        raise ValueError("local_database is not initialized")
    extractor = MigManExtract(
        nl=nl, cfg=cfg, logger=logger, fh=fh, local_database=local_database
    )
    extractor.extract()


@task(name="Transform Objects")
def transform(
    nl: NemoLibrary,
    cfg: ConfigMigMan,
    logger: Union[logging.Logger, object],
    fh: ETLFileHandler,
) -> None:
    """
    Prefect task to transform extracted MigMan data.

    This task handles the transformation phase of the ETL pipeline, processing
    and cleaning the extracted data to prepare it for loading into Nemo.
    It applies business rules, data validation, and formatting operations.

    Args:
        cfg (PipelineMigMan): Pipeline configuration containing transformation settings,
                                                      including business rules and data processing parameters.
        logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                               Can be a standard Python logger or Prefect logger.

    Returns:
        None

    Note:
        The actual transformation logic is delegated to the MigManTransform class.
    """
    logger.info("Transforming MigMan objects")
    global local_database
    if not local_database:
        raise ValueError("local_database is not initialized")
    transformer = MigManTransform(
        nl=nl, cfg=cfg, logger=logger, fh=fh, local_database=local_database
    )

    if not local_database or not local_database.con:
        raise ValueError("Database handler is not initialized")

    if not cfg.extract.adapter:
        raise ValueError("No adapter specified for transformation")

    # start with joins. After this step, we have all data in our data modell
    transform_joins(transformer)

    # mappings
    transformer.mappings(transformer)

    # handle duplicates
    transform_duplicates(transformer)

    # remove empty columns
    transform_nonempty(transformer)


@task(name="Transform: JOINS")
def transform_joins(transformer: MigManTransform) -> None:
    """
    Prefect task to perform join operations during the transformation phase.

    This task handles the join operations required to consolidate data
    from multiple sources into a unified format suitable for loading into Nemo.

    Args:
        transformer (MigManTransform): Instance of MigManTransform class to perform joins.

    Returns:
        None
    """
    transformer.joins()


@task(name="Transform: Mappings")
def transform_mappings(transformer: MigManTransform) -> None:
    """
    Prefect task to apply mappings during the transformation phase.

    This task handles the application of business rules and data mappings
    to transform the extracted data into the desired format for loading into Nemo.

    Args:
        transformer (MigManTransform): Instance of MigManTransform class to apply mappings.
    Returns:
        None
    """
    transformer.mappings()


@task(name="Transform: Duplicates")
def transform_duplicates(transformer: MigManTransform) -> None:
    """
    Prefect task to handle duplicate records during the transformation phase.

    This task identifies and resolves duplicate records in the extracted data,
    ensuring data integrity and consistency before loading into Nemo.

    Args:
        transformer (MigManTransform): Instance of MigManTransform class to handle duplicates.

    Returns:
        None
    """
    transformer.duplicates()


@task(name="Transform: Non-Empty Columns")
def transform_nonempty(transformer: MigManTransform) -> None:
    """
    Prefect task to remove empty columns during the transformation phase.

    This task identifies and removes columns that contain no data,
    optimizing the dataset for loading into Nemo.

    Args:
        transformer (MigManTransform): Instance of MigManTransform class to remove empty columns.
    """
    transformer.nonempty()


@task(name="Load Objects")
def load(
    nl: NemoLibrary,
    cfg: ConfigMigMan,
    logger: Union[logging.Logger, object],
    fh: ETLFileHandler,
) -> None:
    """
    Prefect task to load transformed data into target system.

    This task handles the loading phase of the ETL pipeline, inserting
    the transformed data into the target system with proper error handling
    and performance optimization.

    Args:
        cfg (PipelineMigMan): Pipeline configuration containing load settings,
                                                      including target system configuration and batch parameters.
        logger (Union[logging.Logger, object]): Logger instance for recording execution details.
                                               Can be a standard Python logger or Prefect logger.

    Returns:
        None

    Note:
        The actual loading logic is delegated to the MigManLoad class.
    """
    logger.info("Loading MigMan objects into target system")
    global local_database
    if not local_database:
        raise ValueError("local_database is not initialized")
    loader = MigManLoad(
        nl=nl, cfg=cfg, logger=logger, fh=fh, local_database=local_database
    )
    loader.load()
