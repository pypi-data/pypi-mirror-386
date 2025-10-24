"""
Job runner for executing market data collection jobs.

This module provides the core job execution logic for both live and backfill
jobs using the new config system from market_data_core.
"""

import logging
from typing import Optional, Iterable
from pathlib import Path

from market_data_core import load_config, ProviderRegistry, Bar

logger = logging.getLogger(__name__)


class JobExecutionError(Exception):
    """Raised when job execution fails."""
    pass


def run_job(config_path: str, job_name: str, profile: Optional[str] = None) -> None:
    """
    Execute a market data collection job.
    
    Args:
        config_path: Path to the configuration file
        job_name: Name of the job to execute
        profile: Optional profile override (dev/staging/prod)
    
    Raises:
        JobExecutionError: If job execution fails
    """
    try:
        # Load configuration with profile overlay
        logger.info(f"Loading config from {config_path} with profile {profile or 'default'}")
        cfg = load_config(config_path, profile_override=profile)
        
        # Validate job exists
        if job_name not in cfg.jobs.root:
            raise JobExecutionError(f"Job '{job_name}' not found in configuration")
        
        job = cfg.jobs.root[job_name]
        logger.info(f"Executing job '{job_name}' in {job.mode} mode")
        
        # Get dataset configuration
        if job.dataset not in cfg.datasets.root:
            raise JobExecutionError(f"Dataset '{job.dataset}' not found for job '{job_name}'")
        
        dataset = cfg.datasets.root[job.dataset]
        logger.info(f"Using dataset '{job.dataset}' with provider '{dataset.provider}'")
        
        # Resolve provider
        provider_registry = ProviderRegistry(cfg.providers)
        provider = provider_registry.resolve(dataset.provider)
        logger.info(f"Resolved provider: {provider.name}")
        
        # Execute job based on mode
        if job.mode == "backfill":
            rows = _execute_backfill_job(provider, dataset, job)
        else:
            rows = _execute_live_job(provider, dataset, job)
        
        # Write results to storage
        _write_results(cfg, rows, job_name)
        
        logger.info(f"Job '{job_name}' completed successfully")
        
    except Exception as e:
        logger.error(f"Job '{job_name}' failed: {e}")
        raise JobExecutionError(f"Job execution failed: {e}") from e


def _execute_backfill_job(provider, dataset, job) -> Iterable[Bar]:
    """Execute a backfill job."""
    logger.info("Executing backfill job")
    
    if not job.backfill:
        raise JobExecutionError("Backfill job requires backfill specification")
    
    # Execute backfill through provider
    rows = provider.backfill(dataset, job)
    
    # Count rows for logging
    row_count = 0
    for row in rows:
        row_count += 1
        if row_count % 1000 == 0:
            logger.info(f"Processed {row_count} rows...")
    
    logger.info(f"Backfill completed with {row_count} rows")
    return rows


def _execute_live_job(provider, dataset, job) -> Iterable[Bar]:
    """Execute a live job."""
    logger.info("Executing live job")
    
    # Execute live fetch through provider
    rows = provider.fetch_live(dataset, job)
    
    # Count rows for logging
    row_count = 0
    for row in rows:
        row_count += 1
    
    logger.info(f"Live job completed with {row_count} rows")
    return rows


def _write_results(cfg, rows: Iterable[Bar], job_name: str) -> None:
    """Write job results to configured storage targets."""
    if not cfg.features.write_enabled:
        logger.info("Write disabled by feature flag, skipping storage")
        return
    
    # Write to primary storage
    if "primary" in cfg.storage.root:
        _write_to_primary_storage(cfg.storage.root["primary"], rows)
    
    # Write to lake export if enabled
    if cfg.features.export_enabled and "lake_export" in cfg.storage.root:
        _write_to_lake_export(cfg.storage.root["lake_export"], rows)


def _write_to_primary_storage(storage_config, rows: Iterable[Bar]) -> None:
    """Write bars to primary storage (TimescaleDB)."""
    try:
        # Import here to avoid circular imports
        from market_data_store.client import StoreClient
        
        logger.info("Writing to primary storage")
        client = StoreClient(storage_config.uri)
        client.write_bars(rows, batch_size=storage_config.write.batch_size)
        logger.info("Primary storage write completed")
        
    except ImportError:
        logger.warning("market_data_store not available, skipping primary storage write")
    except Exception as e:
        logger.error(f"Primary storage write failed: {e}")
        raise


def _write_to_lake_export(storage_config, rows: Iterable[Bar]) -> None:
    """Write bars to lake export (S3/Parquet)."""
    try:
        # Import here to avoid circular imports
        from market_data_store.client import LakeClient
        
        logger.info("Writing to lake export")
        client = LakeClient(storage_config)
        client.export(rows)
        logger.info("Lake export completed")
        
    except ImportError:
        logger.warning("market_data_store not available, skipping lake export")
    except Exception as e:
        logger.error(f"Lake export failed: {e}")
        raise
