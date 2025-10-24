import os
import sys
import tempfile
from datetime import datetime
from glob import glob
from urllib.parse import urljoin

import requests
import typer
from loguru import logger
from truenas_api_client import JSONRPCClient


class TrueNasError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def auth(client: JSONRPCClient, api_key: str | None = None):
    # Auth
    logger.info("Authenticating with TrueNAS API")
    session = client.call("auth.login_with_api_key", api_key)
    if not session:
        raise TrueNasError("Auth failed")
    logger.debug("Authentication successful")


def schedule_backup_job(
    client: JSONRPCClient,
    filename: str,
    secretseed: bool | None = None,
    root_authorized_keys: bool | None = None,
) -> str:
    try:
        # Download config
        options = {
            "secretseed": secretseed,
            "root_authorized_keys": root_authorized_keys,
        }
        logger.debug(f"Scheduling backup job for {filename} with options: {options}")
        result = client.call("core.download", "config.save", [options], filename)
        _, download_uri = result
        logger.info("Backup job scheduled, download URI obtained")
    except Exception as e:
        logger.error(f"Failed to schedule backup job: {e}")
        raise TrueNasError(f"Failed to initiate download: {e}") from e

    return download_uri


def download_backup(
    download_uri: str,
    filename: str,
    backup_dir: str,
    truenas_url: str,
    verify_ssl: bool,
    max_backups: int,
) -> dict[str, int | str]:
    try:
        os.makedirs(backup_dir, exist_ok=True)
        full_path = os.path.join(backup_dir, filename)
        download_url = urljoin(f"https://{truenas_url}", download_uri)

        # Fetch and save
        logger.info(f"Downloading backup from {download_url}")
        logger.debug(f"Saving to {full_path} (verify SSL: {verify_ssl})")
        response = requests.get(download_url, verify=verify_ssl)
        response.raise_for_status()
        with open(full_path, "wb") as f:
            f.write(response.content)
        logger.debug(f"Downloaded {len(response.content)} bytes")

        # Manage backup retention
        glob_pattern = os.path.join(backup_dir, "truenas-backup-*.tar.gz")
        backup_files = glob(glob_pattern)
        if len(backup_files) > max_backups:
            backup_files.sort(key=os.path.getmtime)
            for old_file in backup_files[:-max_backups]:
                logger.debug(f"Removing old backup: {old_file}")
                os.remove(old_file)

        logger.info(f"Backup saved successfully, kept {len(glob(glob_pattern))} backups")
        return {
            "filename": full_path,
            "size": len(response.content),
            "backups_kept": len(glob(glob_pattern)),
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Download request failed: {e}")
        raise TrueNasError(f"Download request failed: {e}") from e
    except Exception as e:
        logger.error(f"Failed to save file or manage backups: {e}")
        raise TrueNasError(f"Failed to save file or manage backups: {e}") from e


def perform_backup(
    truenas_url: str,
    api_key: str,
    verify_ssl: bool,
    max_backups: int,
    secretseed: bool,
    root_authorized_keys: bool,
    backup_dir: str,
) -> dict[str, int | str]:
    """Perform TrueNAS backup with optional CLI-overridable parameters."""
    # Get defaults from env if not provided
    logger.info("Starting TrueNAS backup process")
    logger.debug(f"Backup directory: {backup_dir}")
    logger.debug(f"Max backups to keep: {max_backups}")
    logger.debug(f"Include secretseed: {secretseed}, root authorized keys: {root_authorized_keys}")

    if not truenas_url:
        raise TrueNasError("TrueNAS URL required")
    if not api_key:
        raise TrueNasError("API key required")

    filename = f"truenas-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
    logger.debug(f"Generated filename: {filename}")

    with JSONRPCClient(
        uri=f"wss://{truenas_url}/api/current", verify_ssl=verify_ssl,
    ) as client:
        auth(client, api_key)
        download_uri = schedule_backup_job(
            client, filename, secretseed, root_authorized_keys,
        )
        return download_backup(
            download_uri, filename, backup_dir, truenas_url, verify_ssl, max_backups,
        )


app = typer.Typer(help="TrueNAS Backup CLI", invoke_without_command=True)


@app.command()
def run(
    url: str = typer.Option(os.getenv("TRUENAS_URL"), "--url", help="TrueNAS URL (overrides TRUENAS_URL)"),
    api_key: str = typer.Option(
        None, "--api-key", help="TrueNAS API key (overrides TRUENAS_API_KEY)",
    ),
    verify_ssl: bool = typer.Option(
        os.getenv("VERIFY_SSL", "false").lower() == "true",
        "--verify-ssl/--no-verify-ssl", help="Verify SSL (overrides VERIFY_SSL)",
    ),
    max_backups: int = typer.Option(
        int(os.getenv("MAX_BACKUPS", 5)),
        "--max-backups",
        help="Max number of backups to keep (overrides MAX_BACKUPS)",
    ),
    secretseed: bool = typer.Option(
        os.getenv("SECRETSEED", "false").lower() == "true",
        "--secretseed/--no-secretseed",
        help="Include secretseed in backup (overrides SECRETSEED)",
    ),
    root_authorized_keys: bool = typer.Option(
        os.getenv("SECRETSEED", "false").lower() == "true",
        "--root-authorized-keys/--no-root-authorized-keys",
        help="Include root authorized keys (overrides ROOT_AUTHORIZED_KEYS)",
    ),
    backup_dir: str = typer.Option(
        os.getenv("BACKUP_DIR") or tempfile.gettempdir(),
        "--backup-dir",
        help="Directory to save backups (default: system temp dir)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", help="Enable verbose (debug) logging",
    ),
):
    """Run the TrueNAS backup."""
    # Configure logging based on verbose flag
    logger.remove()  # remove default sink
    logger.add(
        sys.stderr,
        colorize=True,
        level="DEBUG" if verbose else "INFO",
    )

    try:
        result = perform_backup(
            truenas_url=url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            max_backups=max_backups,
            secretseed=secretseed,
            root_authorized_keys=root_authorized_keys,
            backup_dir=backup_dir,
        )
        logger.info(f"Backup completed: {result}")
    except TrueNasError as e:
        logger.error(f"Error: {e.message}") if verbose else logger.info(f"Error: {e.message}")
        raise typer.Exit(code=1) from e


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        # Default to run if no subcommand (for cron)
        ctx.invoke(
            run,
            url=None,
            api_key=None,
            verify_ssl=None,
            max_backups=None,
            secretseed=None,
            root_authorized_keys=None,
            backup_dir=None,
            verbose=False,
        )


if __name__ == "__main__":
    app()
