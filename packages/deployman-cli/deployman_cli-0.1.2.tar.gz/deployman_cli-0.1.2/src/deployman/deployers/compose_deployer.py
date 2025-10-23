from __future__ import annotations
from typing import Tuple, List
from rich.table import Table
import json
from rich.console import Console

from deployman.connectors.base import Connector
from deployman.models import Service
from deployman.services.service import ServicePathResolver
from deployman.storage import ConfigRepository

class ComposeServiceContainer:
    exit_code: int
    health: str
    id: str
    name: str
    state: str

    def __init__(self, exit_code: int, health: str, id: str, name: str, state: str) -> None:
        self.exit_code = exit_code
        self.health = health
        self.id = id
        self.name = name
        self.state = state


class ComposeDeployer:
    def __init__(self, repo: ConfigRepository | None = None, connection: Connector | None = None) -> None:
        self.repo = repo or ConfigRepository()
        self.connection = connection
        self.console = Console()

    def _compose_pull(self, service_name: str, connection: Connector, compose_path: str, env: dict[str, str]) -> Tuple[bool, str]:
        pull_cmd = f"docker compose -p {service_name} -f {compose_path} pull"
        self.console.log(f"Executing: {pull_cmd}")
        code, out, err = connection.exec(pull_cmd, env=env)
        if code != 0:
            return False, f"Compose pull failed: {err or out}"
        return True, "Compose pull succeeded"

    def _compose_create(self, service_name: str, connection: Connector, compose_path: str, no_start: bool, force: bool, env: dict[str, str]) -> Tuple[bool, str]:
        force_flag = "--force-recreate" if force else ""

        create_cmd = f"docker compose -p {service_name} -f {compose_path} create {force_flag} --remove-orphans"
        
        self.console.log(f"Executing: {create_cmd}")
        self.console.log(f"      env: {env}")

        code, out, err = connection.exec(create_cmd, env=env)
        if code != 0:
            return False, f"Compose create failed: {err or out}"
        return True, "Compose up succeeded"
    
    def _compose_start(self, service_name: str, connection: Connector, compose_path: str, env: dict[str, str]) -> Tuple[bool, str]:
        start_cmd = f"docker compose -p {service_name} -f {compose_path} start"
        self.console.log(f"Executing: {start_cmd}")
        code, out, err = connection.exec(start_cmd, env=env)
        if code != 0:
            return False, f"Compose start failed: {err or out}"
        return True, "Compose start succeeded"

    def _upload_file(self, local_path: str, remote_path: str, mode: int) -> None:
        self.console.log(f"Uploading: {local_path} -> {remote_path}")
        try:
            self.connection.put_file(local_path, remote_path, mode)
            return True
        except FileNotFoundError as e:
            self.console.log(f"Local file not found: {e}")
            return False

    def deploy(self, service: Service, no_start: bool = True, force_recreate: bool = False) -> Tuple[bool, str]:
        self.console.log(f"Deploying service '{service.name}' to target '{self.connection.t.name}'")

        _compose_local_path = ServicePathResolver.resolve_local_compose_file(service)
        _compose_remote_path = ServicePathResolver.resolve_remote_compose_file(service, self.connection)

        if not self._upload_file(_compose_local_path, _compose_remote_path, 0o644):
            return False, f"Local compose file not found: {_compose_local_path}"

        for file in service.compose.additional_files:
            _local_file = ServicePathResolver.resolve_local_rel_path(service, file.src)
            _remote_file = ServicePathResolver.resolve_remote_rel_config_path(service, self.connection.get_target(), file.src or file.dest)

            if not self._upload_file(_local_file, _remote_file, int(file.mode, 8)):
                return False, f"Local additional file not found: {file.src}"

        _env = {
            "deployman_service_data_dir": ServicePathResolver.resolve_remote_data_dir(service, self.connection.get_target()),
        }

        ok, msg = self._compose_pull(service.name, self.connection, _compose_remote_path, _env)
        if not ok:
            return False, msg

        ok, msg = self._compose_create(service.name, self.connection, _compose_remote_path, no_start, force_recreate, _env)
        if not ok:
            return False, msg
        
        if not no_start:
            ok, msg = self._compose_start(service.name, self.connection, _compose_remote_path, _env)
            if not ok:
                return False, msg

        return True, f"Service '{service.name}' deployed to {self.connection.t.name}"

    def remove(self, service: Service) -> Tuple[bool, str]:
        self.console.log(f"Removing service '{service.name}' from target '{self.connection.t.name}'")

        _compose_remote_path = ServicePathResolver.resolve_remote_compose_file(service, self.connection)

        _env = {
                "deployman_service_data_dir": ServicePathResolver.resolve_remote_data_dir(service, self.connection.get_target()),
        }

        down_cmd = f"docker compose -p {service.name} -f {_compose_remote_path} down --volumes --remove-orphans"
        self.console.log(f"Executing: {down_cmd}")
        code, out, err = self.connection.exec(down_cmd, env=_env)
        if code != 0:
            return False, f"Compose down failed: {err or out}"

        return True, f"Service '{service.name}' removed from {self.connection.t.name}"

    def list_compose_containers(self, service: Service) -> Tuple[bool, List[str] | str]:
        ps_cmd = f"docker compose -p {service.name} ps -q"
        code, out, _ = self.connection.exec(ps_cmd)
        if code != 0:
            return None

        return out.splitlines()

    def inspect_container(self, container_id: str) -> dict:
        inspect_cmd = f"docker inspect {container_id}"
        code, out, err = self.connection.exec(inspect_cmd)
        if code != 0:
            return None
        data = json.loads(out)
        if isinstance(data, list) and len(data) > 0:
            return data[0]

    def list_containers(self, service: Service) -> Tuple[bool, List[str] | str]:
        self.console.log(f"Listing containers for service '{service.name}' on target '{self.connection.t.name}'")

        containers_inspect = [
            self.inspect_container(container_id) for container_id in self.list_compose_containers(service)
        ]
        
        container_list = [
            ComposeServiceContainer(
                exit_code=container_inspect.get("State").get("ExitCode"),
                health=container_inspect.get("State", {}).get("Health", {}).get("Status", {}),
                id=container_inspect.get("Id"),
                name=container_inspect.get("Name").lstrip("/"),
                state=container_inspect.get("State").get("Status"),
            ) for container_inspect in containers_inspect
        ]
        
        return True, container_list
        
    def status(self, service: Service) -> Tuple[bool, List[ComposeServiceContainer] | str]:
        containers = self.list_containers(service)

        rich_table = Table(title=f"Containers for service '{service.name}'")
        rich_table.add_column("Name", style="cyan", no_wrap=True)
        rich_table.add_column("Service", style="magenta")
        rich_table.add_column("State", style="green")
        rich_table.add_column("Health", style="yellow")
        rich_table.add_column("Exit Code", style="red") 

        for c in containers:
            rich_table.add_row(c.name, c.service, c.state, c.health or "N/A", str(c.exit_code))

        return True, rich_table