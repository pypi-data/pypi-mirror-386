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
import argparse
import os
import socket
import sys

from paramiko.ssh_exception import AuthenticationException

from .commands.config import execute_config_command
from .commands.deploy import execute_deploy_command
from .commands.down import execute_down_command
from .commands.mount import execute_mount_volumes_command
from .commands.setup import execute_setup_command
from .commands.setup import print_ssh_copy_id_commands
from .commands.umount import execute_umount_volumes_command
from .commands.volumes import execute_create_volumes_command
from .core.package import APP_NAME
from .core.package import APP_DESCRIPTION
from .core.package import APP_VERSION
from .core.shell import Setting
from .drivers.nfs import NFSDriver
from .shells.local import LocalShell
from .shells.remote import RemoteShell

DriverType = str
ShellConnectionString = str


driver_shemes = ['nfs://']
driver_examples = [f'{sheme}username:password@hostname' for sheme in driver_shemes]
DRIVER_EXAMPLES_STR = ' or '.join(driver_examples)


def manager_type(value: str) -> tuple[DriverType, ShellConnectionString]:
  if not any(value.startswith(scheme) for scheme in driver_shemes):
    raise argparse.ArgumentTypeError(
      f'{value} is not a valid manager ({DRIVER_EXAMPLES_STR})',
    )

  driver_type, connection_string = value.split('://', 1)

  return driver_type, connection_string


def replica_type(value: str) -> list[Setting]:
  connection_strings = value.split(' ')

  try:
    return [Setting.from_connection_string(item.strip()) for item in connection_strings]
  except socket.gaierror as error:
    raise argparse.ArgumentTypeError(f'{value} - {error}') from error
  except Exception as exception:
    raise argparse.ArgumentTypeError(
      f'{value} is not a replica value (username:password@hostname). {exception}'
    ) from exception


def nodes_type(value: str) -> list[Setting]:
  connection_strings = value.split(' ')

  try:
    return [Setting.from_connection_string(item.strip()) for item in connection_strings]
  except socket.gaierror as error:
    raise argparse.ArgumentTypeError(f'{value} - {error}') from error
  except Exception as exception:
    raise argparse.ArgumentTypeError(
      f'{value} is not a nodes value (username:password@hostname)'
    ) from exception


def run() -> None:
  parser = argparse.ArgumentParser(APP_NAME, description=APP_DESCRIPTION)
  subparsers = parser.add_subparsers()

  parser.add_argument('--project', required=True, help='Project name')
  parser.add_argument('--stack', help='Stack name')

  # add version argument
  parser.add_argument(
    '-v', '--version',
    action='version',
    version=f'{APP_NAME} {APP_VERSION}',
    help='Show the version number and exit',
  )

  parser.add_argument(
    '--manager',
    type=manager_type,
    required=True,
    help=f'Storage manager URI to use. Can be {DRIVER_EXAMPLES_STR}',
  )

  parser.add_argument(
    '--key',
    default=os.path.expanduser('~/.ssh/id_rsa'),
    help='Path to the SSH private key file',
  )

  parser.add_argument(
    '--debug',
    action='store_true',
    help='Enable debug mode',
  )

  #
  # Setup command
  setup_parser = subparsers.add_parser('setup', description='Setup manager and replica nodes')
  setup_parser.set_defaults(func=execute_setup_command)

  setup_parser.add_argument(
    '--replica',
    type=replica_type,
    nargs='+',
    required=True,
    help='Replica nodes to setup',
  )

  setup_parser.add_argument(
    '--clients',
    type=nodes_type,
    nargs='+',
    required=True,
    help='Client nodes to setup',
  )

  setup_parser.add_argument(
    '--force',
    action='store_true',
    help='Force setup tasks',
  )

  #
  # Create Volumes command
  create_volumes_parser = subparsers.add_parser(
    'create-volumes', description='Create and sync shared volumes'
  )
  create_volumes_parser.set_defaults(func=execute_create_volumes_command)
  create_volumes_parser.add_argument(
    '--replica',
    type=replica_type,
    nargs='+',
    required=True,
    help='Nodes where volumes will be created',
  )

  create_volumes_parser.add_argument(
    '--force',
    action='store_true',
    help='Force volumes data sync',
  )

  #
  # Mount Volumes command
  mount_volumes_parser = subparsers.add_parser('mount-volumes', description='Mount shared volumes')
  mount_volumes_parser.set_defaults(func=execute_mount_volumes_command)
  mount_volumes_parser.add_argument(
    '--clients',
    type=nodes_type,
    nargs='+',
    required=True,
    help='Client nodes on which volumes will be mounted',
  )

  #
  # Unmount Volumes command
  umount_volumes_parser = subparsers.add_parser(
    'unmount-volumes', description='Unmount shared volumes'
  )
  umount_volumes_parser.set_defaults(func=execute_umount_volumes_command)
  umount_volumes_parser.add_argument(
    '--clients',
    type=nodes_type,
    nargs='+',
    required=True,
    help='Client nodes on which volumes will be unmounted',
  )

  #
  # Config command
  config_parser = subparsers.add_parser(
    'config', description='Parse, resolve and render compose file in canonical format'
  )
  config_parser.set_defaults(func=execute_config_command)

  config_parser.add_argument(
    '--compose',
    action='store_true',
    help='Resolve for Docker Compose',
  )

  #
  # Deploy command
  deploy_parser = subparsers.add_parser(
    'deploy', description='Deploy a new stack or update an existing stack'
  )
  deploy_parser.set_defaults(func=execute_deploy_command)
  deploy_parser.add_argument(
    '--image-prefix', default='', help='Image namespace prefix to added to internal images'
  )

  #
  # Down command
  down_parser = subparsers.add_parser('down', description='Stop and remove containers, networks')
  down_parser.set_defaults(func=execute_down_command)

  #
  # Parsing
  try:
    args = parser.parse_args()
  except (Exception, argparse.ArgumentError) as exception:
    print(exception)
    sys.exit(40)

  driver_name, connection_string = args.manager
  setting = Setting.from_connection_string(connection_string)
  create_shell = LocalShell if setting.local else RemoteShell
  create_driver = NFSDriver
  shell = create_shell(setting, args.key)
  driver = create_driver(args.stack, project=args.project, shell=shell, debug=args.debug)

  shell.connect()

  # Call the function associated with the selected subcommand
  if hasattr(args, 'func'):
    if not hasattr(args, 'image_prefix'):
      setattr(args, 'image_prefix', '')

    if args.debug:
      args.func(args, driver)
    else:
      try:
        args.func(args, driver)
      except AuthenticationException as exception:
        print(f'\nError: {exception}')
        print_ssh_copy_id_commands(args)
        sys.exit(41)
      except Exception as exception:
        print(exception)
        sys.exit(50)
  else:
    parser.print_help()

  sys.exit(0)
