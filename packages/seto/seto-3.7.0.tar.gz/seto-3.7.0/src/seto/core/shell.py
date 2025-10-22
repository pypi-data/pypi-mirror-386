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
import os
import socket
import sys
from dataclasses import dataclass
from functools import lru_cache

from .dns import resolve_hostname
from .volume import Volume


@dataclass(kw_only=True)
class Setting:
  hostname: str
  username: str | None
  password: str | None
  local: bool = False
  ip: str

  def __eq__(self, other: 'Setting') -> bool:
    return self.hostname == other.hostname

  def __str__(self) -> str:
    if self.username:
      return f'{self.username}@{self.hostname}'

    return f'root@{self.hostname}'

  @staticmethod
  def from_connection_string(connection_string: str) -> 'Setting':
    client_user: str | None = None
    node_host: str = connection_string

    if '@' in connection_string:
      client_user, node_host = tuple(connection_string.split('@')[0:2])

    if not node_host:
      raise ValueError('Unable to determine hostname from connection string')

    node_host = node_host.lower()
    is_local = node_host == 'localhost' or node_host == socket.gethostname()

    if not is_local and not client_user:
      raise ValueError('Unable to determine username from connection string')

    username, password = tuple((client_user.split(':') + [None])[0:2]) if client_user else (None, None)
    node_ip = resolve_hostname(node_host)

    return Setting(
      hostname=node_host,
      username=username,
      password=password,
      local=is_local,
      ip=node_ip,
    )


class File:
  def __init__(self, shell: 'Shell', filename: str) -> None:
    self.shell = shell
    self.filename = filename
    self.content = shell.run(f'cat {self.filename}', sudo=True, quiet=True, stdout=False)

  def append(self, entry: str, *, key: str | None = None) -> bool:
    cleaned_entry = entry.strip()
    entry_key = key or cleaned_entry

    if entry_key not in self.content:
      add_entry_cmd = f'echo "{cleaned_entry}" >> {self.filename}'
      self.shell.run(add_entry_cmd, sudo=True, quiet=True)
      self.content += f'\n{cleaned_entry}'

      return True

    return False

  def chown(self, owner: str, group: str | None = None):
    if group:
      self.shell.run(f'chown {owner}:{group} {self.filename}', sudo=True, quiet=True)
    else:
      self.shell.run(f'chown {owner} {self.filename}', sudo=True, quiet=True)

  def chmod(self, mode: str | int):
    if 'letsencrypt' in self.filename:
      mode = 600

    self.shell.run(f'chmod {mode} {self.filename}', sudo=True, quiet=True)


class Shell:
  def __init__(self, setting: Setting, key_file_path: str | None = None) -> None:
    self.setting = setting
    self.key_file_path = key_file_path
    self.pub_key_file_path = f'{key_file_path}.pub' if key_file_path else None

  @property
  def hostname(self) -> str:
    return self.setting.hostname

  @property
  def username(self) -> str | None:
    return self.setting.username

  @property
  def prompt(self) -> str:
    return f'{self.setting.username}@{self.setting.hostname}:~$' if self.setting.username else f'{self.setting.hostname}:~$'

  @property
  @lru_cache
  def ssh_pub_key(self) -> str | None:
    if self.pub_key_file_path:
      with open(self.pub_key_file_path, encoding='utf-8') as key_file:
        return key_file.read()
    return None

  def connect(self):
    raise NotImplementedError()

  def check_user_exists(self, username: str) -> bool:
    ouput = self.run(f'getent passwd {username}', sudo=True, stdout=False, quiet=True)

    return username in ouput

  def print(self, message: str) -> None:
    print(f'{self.prompt} {message}')

  def install(self, package_name: str, *, user: str = 'nobody', group: str = 'nogroup') -> bool:
    """
    Install a package on remote Debian/Ubuntu or Fedora/RHEL system.
    """

    # Detect package manager
    pkg_manager = None

    if 'apt-get' in self.run('command -v apt-get', quiet=True, stdout=False):
      pkg_manager = 'apt'
    elif 'dnf' in self.run('command -v dnf', quiet=True, stdout=False):
      pkg_manager = 'dnf'
    elif 'yum' in self.run('command -v yum', quiet=True, stdout=False):
      pkg_manager = 'yum'

    if not pkg_manager:
      raise RuntimeError('Unsupported remote OS: no known package manager found')

    # Check if package is already installed
    check_cmd = (
      f"dpkg -l | grep -w {package_name}"
      if pkg_manager == 'apt'
      else f"rpm -qa | grep -w {package_name}"
    )
    result = self.run(check_cmd, sudo=True, quiet=True, stdout=False)

    if package_name not in result:
      print(f'Installing {package_name} on {self.setting.hostname}...')

      if pkg_manager == 'apt':
        self.run(
          f"DEBIAN_FRONTEND=noninteractive apt-get install -y --quiet {package_name}",
          sudo=True,
          quiet=True,
        )
      elif pkg_manager == 'dnf':
        self.run(f"dnf install -y {package_name}", sudo=True, quiet=True)
      elif pkg_manager == 'yum':
        self.run(f"yum install -y {package_name}", sudo=True, quiet=True)

      return True

    print(f'{package_name} is already installed on {self.setting.hostname}')

    return False

  def mkdir(self, path: str, *, user='nobody', group='nogroup', mode: str | int = 'g+w') -> None:
    try:
      self.run(f'ls {path}', sudo=True, quiet=True, stderr=True)
    except Exception:
      if 'letsencrypt' in path:
        mode = 600

      self.run(f'mkdir -p {path}', sudo=True, quiet=True)
      self.run(f'chown -R {user}:{group} {path}', sudo=True, quiet=True)
      self.run(f'chmod -R {mode} {path}', sudo=True, quiet=True)

  def run(
    self,
    command: str,
    *,
    sudo=False,
    stdout=True,
    stderr=False,
    quiet=False,
    input: str | None = None,
  ) -> str:
    raise NotImplementedError()

  def file(self, filename: str) -> File:
    return File(self, filename)

  def _copy(self, *, local_path: str, remote_path: str) -> None:
    if os.path.isfile(local_path):
      try:
        self.copy_file(local_path=local_path, remote_path=remote_path)
      except Exception as error:
        print(error)
        sys.exit(2)
    elif os.path.isdir(local_path):
      for root, _dirs, files in os.walk(local_path):
        remote_root = os.path.join(remote_path, os.path.relpath(root, local_path))
        self.mkdir(remote_root)

        for file in files:
          local_file_path = os.path.join(root, file)
          remote_file_path = os.path.join(remote_root, file)

          self._copy(
            local_path=local_file_path,
            remote_path=remote_file_path,
          )
    else:
      print('WARN:', local_path, remote_path)

  def copy_volume(self, volume: Volume, dest: str) -> None:
    target = os.path.join(dest, volume.target)

    if volume.source:
      self._copy(local_path=volume.source, remote_path=target)
    else:
      self.mkdir(target)

  def copy_file(self, *, local_path: str, remote_path: str) -> None:
    raise NotImplementedError()

  def close(self) -> None:
    raise NotImplementedError()
