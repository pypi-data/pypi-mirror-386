# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

"""Add click network groups to the cli command"""

import click

import tao_cli.common

from nvidia_tao_core.microservices.enum_constants import _get_network_architectures
from tao_cli.cli_actions.network_click_wrapper import create_click_group


@click.group()
@click.version_option(package_name="nvidia-tao-client")
@click.pass_context
def cli(ctx):
    """Create base tao click group"""
    pass


cli.add_command(tao_cli.common.login)
cli.add_command(tao_cli.common.get_gpu_types)

network_architectures = _get_network_architectures()
for network_name in network_architectures:
    click_group = create_click_group(
        network_name, f"Create {network_name} click group"
    )
    cli.add_command(click_group)

if __name__ == "__main__":
    cli()
