from typing import Optional
import typer
from rich.table import Table
from rich import print

from kink import inject

from deployman.services.backup_service import BackupService
from deployman.services.deploy_service import DeployService


class CommandService:

    @inject
    def __init__(self, deploy_service: DeployService, backup_service: BackupService) -> None:
        self.deploy_service = deploy_service
        self.backup_service = backup_service

    def cmd_service_deploy(
        self,
        service_file: str = typer.Option(..., "--service-file", "-s", help="Path to service spec YAML"),
        target: str = typer.Option(None, "--target", help="Target name to deploy to"),
        no_start: bool = typer.Option(False, "--no-start", help="Don't start the service"),
        force_recreate: bool = typer.Option(False, "--force-recreate", help="Force recreate containers")
    ) -> None:
        """Deploy a compose-based service spec to a remote target."""
        result = self.deploy_service.deploy(service_file, target_name=target, no_start=no_start, force_recreate=force_recreate)
        print(result)

    def cmd_service_status(
        self,
        service_file: str = typer.Option(..., "--service-file", "-s", help="Path to service spec YAML"),
        target: str = typer.Option(None, "--target", help="Target name to check status on")
    ) -> None:
        """Check the status of a deployed service on the remote target."""
        success, result = self.deploy_service.status(service_file, target_name=target)
        if success:
            rich_table = Table(title=f"Containers")
            rich_table.add_column("Name", style="cyan", no_wrap=True)
            # rich_table.add_column("Service", style="magenta")
            rich_table.add_column("State", style="green")
            rich_table.add_column("Health", style="yellow")
            rich_table.add_column("Exit Code", style="red") 

        for c in result:
            rich_table.add_row(c.name, c.state, c.health or "N/A", str(c.exit_code))

        print(rich_table)

    def cmd_service_remove(
        self,
        service_file: str = typer.Option(..., "--service-file", "-s", help="Path to service spec YAML"),
    ) -> None:
        """Remove a deployed service from the remote target."""
        result = self.deploy_service.remove(service_file)
        print(result)

    def cmd_service_backup(
        self,
        service_file: str = typer.Option(..., "--service-file", "-s", help="Path to service spec YAML"),
        target: str = typer.Option(None, "--target", "-t", help="Target name to backup from"),
        local_path: Optional[str] = typer.Option(None, "--local-path", "-l", help="Local destination path"),
    ) -> None:
        """Backup service files from the remote host to the local machine."""
        result = self.backup_service.backup(service_file=service_file, target_name=target, local_path=local_path)
        print(result)

    def cmd_service_restore(
        self,
        service_file: str = typer.Option(..., "--service-file", "-s", help="Path to service spec YAML"),
        target: str = typer.Option(..., "--target", "-t", help="Target name to restore to"),
        local_path: Optional[str] = typer.Option(None, "--local-path", "-l", help="Local source path"),
    ) -> None:
        """Restore backup files from local machine to the remote host."""
        result = self.backup_service.restore(service_file=service_file, target_name=target, local_path=local_path)
        print(result)


def get_app() -> typer.Typer:
    command_service = CommandService()
    app = typer.Typer(help="Manage services")
    app.command("deploy")(command_service.cmd_service_deploy)
    app.command("status")(command_service.cmd_service_status)
    app.command("remove")(command_service.cmd_service_remove)
    app.command("backup")(command_service.cmd_service_backup)
    app.command("restore")(command_service.cmd_service_restore)
    return app
