# Copyright 2024-2025 Sébastien Demanou. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import glob
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import Literal
from typing import TypedDict

import yaml

from .driver import Driver
from .permissions import parse_permission_mode
from .volume import Volume

ResolveMode = Literal['compose', 'swarm']
Service = dict[str, Any]


class TopLevelConfig(TypedDict):
  file: str


class ServiceConfig(TypedDict):
  source: str
  target: str
  mode: int


def parse_stack_values(entry: dict | list) -> None:
  if isinstance(entry, dict):
    for key, value in entry.items():
      if isinstance(value, bool):
        entry[key] = 'true' if value else 'false'


def parse_volume_entry(entry: str, default_mode='rw') -> tuple[str, str, str]:
  source, target, mode = (entry.split(':') + [default_mode])[0:3]

  return source, target, mode


def parse_local_volumes(
  stack: str, *, service_name: str, service: Service, image_prefix: str
) -> None:
  local_volumes = []

  if 'volumes-image' in service:
    service_volumes_image = service.get('volumes-image', [])

    del service['volumes-image']

    for volume_entry in service_volumes_image:
      if isinstance(volume_entry, str):
        source, target, _ = parse_volume_entry(volume_entry)
        local_volumes.append((source, target))

  if len(local_volumes) > 0:
    _, image_version = tuple((service['image'].split(':') + ['latest'])[0:2])

    image_name = f'{stack}-{service_name}'.replace('_', '-')
    service_dockerfile_name = f'{image_name}.dockerfile'
    service_dockerfile_file = Path('images') / service_dockerfile_name
    service_dockerfile_definition = (
      [
        f'FROM {service["image"]}',
      ]
      + [f'COPY {source} {target}' for source, target in local_volumes]
      + ['']
    )
    service_dockerfile = '\n'.join(service_dockerfile_definition)
    service_dockerfile = resolve_env_vars(service_dockerfile)

    service['image'] = f'{image_prefix}{image_name}:{image_version}'
    service['build'] = {
      'context': '.',
      'dockerfile': str(service_dockerfile_file),
    }

    # Ensure parent directory exists before writing
    service_dockerfile_file.parent.mkdir(parents=True, exist_ok=True)

    with service_dockerfile_file.open('w', encoding='utf-8') as dockerfile:
      dockerfile.write(service_dockerfile)


def parse_volumes(
  driver: Driver,
  service_name: str,
  service: Service,
  *,
  compose_volumes: dict,
  volumes: list[Volume],
) -> None:
  if 'volumes-nfs' in service:
    service_volumes = service.get('volumes', [])
    service_volumes_nfs = service.get('volumes-nfs', [])
    service['volumes'] = service_volumes

    del service['volumes-nfs']

    for volume_entry in service_volumes_nfs:
      source, target, volume_mode = parse_volume_entry(volume_entry)
      target_folder = target

      if volume_entry.startswith('~/') or volume_entry.startswith('./'):
        device_source = os.path.expanduser(source)

        if os.path.isfile(device_source):
          target_folder = os.path.dirname(target)

        volume_name = source[2:].replace('/', '-').replace('.', '')
      else:
        device_source = None
        volume_name = source

        if volume_name in compose_volumes:
          del compose_volumes[volume_name]

      if volume_mode == 'norename':
        volume_mode = 'rw'
      elif service_name not in volume_name:
        volume_name = f'{service_name}-{volume_name}'

      if device_source and os.path.isfile(device_source):
        filename = os.path.basename(target)
        target = os.path.join(volume_name, filename)
      else:
        target = volume_name

      volume = Volume(
        name=volume_name.replace('-', '_'),
        source=device_source,
        target=target,
        mount_folder=volume_name,
      )

      compose_volumes[volume.name] = driver.resolve_compose_volume(volume)

      service_volumes.append(f'{volume.name}:{target_folder}:{volume_mode}')
      volumes.append(volume)


def resolve_compose_file(
  driver: Driver,
  *,
  compose_data: dict,
  inject: bool = False,
  mode: list[ResolveMode] | None = None,
  image_prefix: str,
) -> tuple[dict, list]:
  mode_value = mode or ['swarm']
  updated_compose_data = compose_data.copy()
  compose_services = updated_compose_data.get('services', {})
  compose_volumes = updated_compose_data.get('volumes', {})
  compose_configs: dict[str, TopLevelConfig] = updated_compose_data.get('configs', {})
  volumes: list[Volume] = []

  for service_name, service in compose_services.items():
    parse_service_configs(
      service_name=service_name,
      service=service,
      configs=compose_configs,
      inject=inject,
    )

    service_environment = service.get('environment', {})
    service_deploy = service.get('deploy', {})
    service_deploy_labels = service_deploy.get('labels', {})
    service_labels = service.get('labels', {})

    service_deploy_labels.update(service_labels)
    parse_stack_values(service_deploy_labels)
    parse_local_volumes(
      driver.stack_id, service_name=service_name, service=service, image_prefix=image_prefix
    )

    parse_volumes(
      driver=driver,
      service_name=service_name,
      service=service,
      compose_volumes=compose_volumes,
      volumes=volumes,
    )

    if 'compose' in mode_value:
      if 'labels' in service_deploy:
        del service_deploy['labels']

      service['labels'] = service_deploy_labels

    if 'swarm' in mode_value:
      parse_stack_values(service_environment)

      if 'hostname' not in service:
        service['hostname'] = '{{.Node.Hostname}}'

      if 'labels' in service:
        del service['labels']

      service['deploy'] = service_deploy
      service_deploy['labels'] = service_deploy_labels

    if 'command' in service and service['command'] is None:
      del service['command']

  updated_compose_data['configs'] = compose_configs
  updated_compose_data['volumes'] = compose_volumes

  return updated_compose_data, volumes


def parse_service_configs(
  service_name: str,
  service: Service,
  *,
  configs: dict[str, TopLevelConfig],
  inject: bool = False,
) -> None:
  new_volumes: list[str] = []
  service_volumes: list[str] = service.get('volumes', [])
  service_configs: list[ServiceConfig] = service.get('configs', [])

  for volume in service_volumes:
    if ':' in volume:
      source, target, mode = parse_volume_entry(volume, 'r')

      if source.startswith('./') or source.startswith('../'):
        if os.path.isfile(source):
          config_name = re.sub(
            r'_{2,}',
            '_',
            f'{service_name}_{source.replace("/", "_").replace(".", "_")}'.replace('-', '_'),
          )

          if inject:
            with open(source, encoding='utf-8') as config:
              configs[config_name] = {  # type: ignore
                'content': config.read(),
              }
          else:
            configs[config_name] = {
              'file': source,
            }

          service_configs.append(
            {
              'source': config_name,
              'target': target,
              'mode': parse_permission_mode(mode),
            }
          )

          continue

    new_volumes.append(volume)

  if len(new_volumes) != len(service_volumes):
    service['configs'] = service_configs
    service['volumes'] = new_volumes


def load_env_file(env_file_path: str) -> None:
  """Load environment variables from a .env file into os.environ."""
  if os.path.exists(env_file_path):
    with open(env_file_path, encoding='utf-8') as file:
      for line in file:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
          key, value = line.split('=', 1)
          # Remove quotes if present
          value = value.strip('"\'')
          os.environ[key.strip()] = value


def resolve_env_vars(content: str) -> str:
  output = subprocess.run(
    ['envsubst'],
    input=content,
    text=True,
    capture_output=True,
    check=True,
  )
  return output.stdout


def parse_compose_file(compose_file: str, resolve_vars=False) -> tuple[dict, str]:
  compose_file = os.path.realpath(compose_file)

  # Auto-load corresponding .env file if it exists
  compose_path = Path(compose_file)
  env_file_path = compose_path.parent / f'{compose_path.stem}.env'
  load_env_file(str(env_file_path))

  with open(compose_file, encoding='utf-8') as file:
    compose_content = file.read()

  if resolve_vars:
    compose_content = resolve_env_vars(compose_content)

  compose_data = yaml.safe_load(compose_content)
  return compose_data, compose_file  # type: ignore


def parse_services(
  driver: Driver,
  stack: str,
  *,
  execute: Callable[[dict, list], None] | None = None,
  mode: list[ResolveMode] | None = None,
  inject: bool = False,
  image_prefix: str,
) -> tuple[list, list]:
  services_files = glob.glob(os.path.join(stack, '*.yaml'))
  output_resolved_compose_data = []
  output_volumes = []

  for service_file in services_files:
    resolve_vars = isinstance(mode, list) and 'compose' in mode
    compose_data, _ = parse_compose_file(service_file, resolve_vars)
    x_mode = compose_data.get('x-mode', 'swarm')

    if x_mode not in ['compose', 'swarm']:
      print('x-mode must be either "compose" or "warm"')
      sys.exit(42)

    if mode:
      if 'compose' in mode and 'compose' != x_mode:
        continue

      if 'swarm' in mode and 'swarm' != x_mode:
        continue

    # resolve compose local volumes
    resolved_compose_data, volumes = resolve_compose_file(
      driver=driver,
      compose_data=compose_data,
      inject=inject,
      mode=[x_mode],
      image_prefix=image_prefix,
    )

    output_resolved_compose_data.append(resolved_compose_data)
    output_volumes.append(volumes)

    if execute:
      execute(resolved_compose_data, volumes)

  return output_resolved_compose_data, output_volumes
