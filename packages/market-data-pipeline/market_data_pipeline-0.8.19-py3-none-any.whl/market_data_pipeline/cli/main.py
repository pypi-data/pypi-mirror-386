from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

from market_data_pipeline.runtime.unified_runtime import UnifiedRuntime
from market_data_pipeline.settings.runtime_unified import (
    RuntimeModeEnum,
    UnifiedRuntimeSettings,
)
from market_data_pipeline.jobs.runner import run_job, JobExecutionError


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mdp",
        description="Market Data Pipeline CLI (Unified Runtime)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # Legacy unified runtime command
    run = sub.add_parser("run", help="Run a pipeline/runtime job.")
    run.add_argument("--mode", choices=[m.value for m in RuntimeModeEnum], required=False)
    run.add_argument("--config", type=str, required=True, help="Path to YAML/JSON config")
    run.add_argument("--job", type=str, default="default", help="Job name (for DAG)")

    # New job execution command
    job_run = sub.add_parser("job", help="Execute a market data collection job using new config system.")
    job_run.add_argument("--config", type=str, required=True, help="Path to configuration file")
    job_run.add_argument("--job", type=str, required=True, help="Job name to execute")
    job_run.add_argument("--profile", type=str, help="Profile override (dev/staging/prod)")

    # Config validation command
    validate = sub.add_parser("validate", help="Validate configuration file.")
    validate.add_argument("--config", type=str, required=True, help="Path to configuration file")
    validate.add_argument("--profile", type=str, help="Profile to validate")

    # Stubs to extend later
    sub.add_parser("list", help="List known jobs (stub)")
    status = sub.add_parser("status", help="Get job status (stub)")
    status.add_argument("--job", type=str, default="default")

    return p.parse_args(argv)


async def _run_cmd(args: argparse.Namespace) -> int:
    if args.command == "list":
        print("Jobs: [example] (stub)")
        return 0

    if args.command == "status":
        print(f"Status for job '{args.job}': RUNNING (stub)")
        return 0

    if args.command == "validate":
        return _validate_config(args)

    if args.command == "job":
        return _execute_job(args)

    if args.command == "run":
        settings = UnifiedRuntimeSettings.from_file(args.config)
        if args.mode:
            # override config mode from CLI if provided
            settings = settings.model_copy(update={"mode": RuntimeModeEnum(args.mode)})

        logger.info(f"Starting UnifiedRuntime in mode={settings.mode.value}")
        async with UnifiedRuntime(settings) as rt:
            # Classic: will delegate to existing service/runner
            # DAG:     will delegate to DagRuntime (builder/registry used internally)
            await rt.run(name=getattr(args, "job", "default"))
        logger.info("UnifiedRuntime finished.")
        return 0

    return 1


def _validate_config(args: argparse.Namespace) -> int:
    """Validate configuration file."""
    try:
        from market_data_core import load_config
        
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        
        logger.info(f"Validating configuration: {config_path}")
        cfg = load_config(str(config_path), profile_override=args.profile)
        
        logger.info(f"✅ Configuration valid!")
        logger.info(f"   Profile: {cfg.profile}")
        logger.info(f"   Providers: {len(cfg.providers.root)}")
        logger.info(f"   Datasets: {len(cfg.datasets.root)}")
        logger.info(f"   Jobs: {len(cfg.jobs.root)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return 1


def _execute_job(args: argparse.Namespace) -> int:
    """Execute a market data collection job."""
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1
        
        logger.info(f"Executing job '{args.job}' with config '{config_path}'")
        if args.profile:
            logger.info(f"Using profile: {args.profile}")
        
        run_job(str(config_path), args.job, args.profile)
        logger.info("✅ Job completed successfully")
        return 0
        
    except JobExecutionError as e:
        logger.error(f"❌ Job execution failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    try:
        exit_code = asyncio.run(_run_cmd(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as exc:
        logger.exception(f"mdp failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

