<a id="types-boto3-medialive"></a>

# types-boto3-medialive

[![PyPI - types-boto3-medialive](https://img.shields.io/pypi/v/types-boto3-medialive.svg?color=blue)](https://pypi.org/project/types-boto3-medialive/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/types-boto3-medialive.svg?color=blue)](https://pypi.org/project/types-boto3-medialive/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/types_boto3_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/types-boto3-medialive)](https://pypistats.org/packages/types-boto3-medialive)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 MediaLive 1.40.57](https://pypi.org/project/boto3/)
compatible with [VSCode](https://code.visualstudio.com/),
[PyCharm](https://www.jetbrains.com/pycharm/),
[Emacs](https://www.gnu.org/software/emacs/),
[Sublime Text](https://www.sublimetext.com/),
[mypy](https://github.com/python/mypy),
[pyright](https://github.com/microsoft/pyright) and other tools.

Generated with
[mypy-boto3-builder 8.11.0](https://github.com/youtype/mypy_boto3_builder).

More information can be found on
[types-boto3](https://pypi.org/project/types-boto3/) page and in
[types-boto3-medialive docs](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [types-boto3-medialive](#types-boto3-medialive)
  - [How to install](#how-to-install)
    - [Generate locally (recommended)](<#generate-locally-(recommended)>)
    - [VSCode extension](#vscode-extension)
    - [From PyPI with pip](#from-pypi-with-pip)
  - [How to uninstall](#how-to-uninstall)
  - [Usage](#usage)
    - [VSCode](#vscode)
    - [PyCharm](#pycharm)
    - [Emacs](#emacs)
    - [Sublime Text](#sublime-text)
    - [Other IDEs](#other-ides)
    - [mypy](#mypy)
    - [pyright](#pyright)
    - [Pylint compatibility](#pylint-compatibility)
  - [Explicit type annotations](#explicit-type-annotations)
    - [Client annotations](#client-annotations)
    - [Paginators annotations](#paginators-annotations)
    - [Waiters annotations](#waiters-annotations)
    - [Literals](#literals)
    - [Type definitions](#type-definitions)
  - [How it works](#how-it-works)
  - [What's new](#what's-new)
    - [Implemented features](#implemented-features)
    - [Latest changes](#latest-changes)
  - [Versioning](#versioning)
  - [Thank you](#thank-you)
  - [Documentation](#documentation)
  - [Support and contributing](#support-and-contributing)

<a id="how-to-install"></a>

## How to install

<a id="generate-locally-(recommended)"></a>

### Generate locally (recommended)

You can generate type annotations for `boto3` package locally with
`mypy-boto3-builder`. Use
[uv](https://docs.astral.sh/uv/getting-started/installation/) for build
isolation.

1. Run mypy-boto3-builder in your package root directory:
   `uvx --with 'boto3==1.40.57' mypy-boto3-builder`
2. Select `boto3` AWS SDK.
3. Add `MediaLive` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `MediaLive`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `types-boto3` for `MediaLive` service.

```bash
# install with boto3 type annotations
python -m pip install 'types-boto3[medialive]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'types-boto3-lite[medialive]'

# standalone installation
python -m pip install types-boto3-medialive
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y types-boto3-medialive
```

<a id="usage"></a>

## Usage

<a id="vscode"></a>

### VSCode

- Install
  [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- Install
  [Pylance extension](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- Set `Pylance` as your Python Language Server
- Install `types-boto3[medialive]` in your environment:

```bash
python -m pip install 'types-boto3[medialive]'
```

Both type checking and code completion should now work. No explicit type
annotations required, write your `boto3` code as usual.

<a id="pycharm"></a>

### PyCharm

> ⚠️ Due to slow PyCharm performance on `Literal` overloads (issue
> [PY-40997](https://youtrack.jetbrains.com/issue/PY-40997)), it is recommended
> to use [types-boto3-lite](https://pypi.org/project/types-boto3-lite/) until
> the issue is resolved.

> ⚠️ If you experience slow performance and high CPU usage, try to disable
> `PyCharm` type checker and use [mypy](https://github.com/python/mypy) or
> [pyright](https://github.com/microsoft/pyright) instead.

> ⚠️ To continue using `PyCharm` type checker, you can try to replace
> `types-boto3` with
> [types-boto3-lite](https://pypi.org/project/types-boto3-lite/):

```bash
pip uninstall types-boto3
pip install types-boto3-lite
```

Install `types-boto3[medialive]` in your environment:

```bash
python -m pip install 'types-boto3[medialive]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `types-boto3` with services you use in your environment:

```bash
python -m pip install 'types-boto3[medialive]'
```

- Install [use-package](https://github.com/jwiegley/use-package),
  [lsp](https://github.com/emacs-lsp/lsp-mode/),
  [company](https://github.com/company-mode/company-mode) and
  [flycheck](https://github.com/flycheck/flycheck) packages
- Install [lsp-pyright](https://github.com/emacs-lsp/lsp-pyright) package

```elisp
(use-package lsp-pyright
  :ensure t
  :hook (python-mode . (lambda ()
                          (require 'lsp-pyright)
                          (lsp)))  ; or lsp-deferred
  :init (when (executable-find "python3")
          (setq lsp-pyright-python-executable-cmd "python3"))
  )
```

- Make sure emacs uses the environment where you have installed `types-boto3`

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="sublime-text"></a>

### Sublime Text

- Install `types-boto3[medialive]` with services you use in your environment:

```bash
python -m pip install 'types-boto3[medialive]'
```

- Install [LSP-pyright](https://github.com/sublimelsp/LSP-pyright) package

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="other-ides"></a>

### Other IDEs

Not tested, but as long as your IDE supports `mypy` or `pyright`, everything
should work.

<a id="mypy"></a>

### mypy

- Install `mypy`: `python -m pip install mypy`
- Install `types-boto3[medialive]` in your environment:

```bash
python -m pip install 'types-boto3[medialive]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `types-boto3[medialive]` in your environment:

```bash
python -m pip install 'types-boto3[medialive]'
```

Optionally, you can install `types-boto3` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`types-boto3-medialive` dependency in production. However, there is an issue in
`pylint` that it complains about undefined variables. To fix it, set all types
to `object` in non-`TYPE_CHECKING` mode.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_boto3_ec2 import EC2Client, EC2ServiceResource
    from types_boto3_ec2.waiters import BundleTaskCompleteWaiter
    from types_boto3_ec2.paginators import DescribeVolumesPaginator
else:
    EC2Client = object
    EC2ServiceResource = object
    BundleTaskCompleteWaiter = object
    DescribeVolumesPaginator = object

...
```

<a id="explicit-type-annotations"></a>

## Explicit type annotations

<a id="client-annotations"></a>

### Client annotations

`MediaLiveClient` provides annotations for `boto3.client("medialive")`.

```python
from boto3.session import Session

from types_boto3_medialive import MediaLiveClient

client: MediaLiveClient = Session().client("medialive")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`types_boto3_medialive.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from types_boto3_medialive import MediaLiveClient
from types_boto3_medialive.paginator import (
    DescribeSchedulePaginator,
    ListAlertsPaginator,
    ListChannelPlacementGroupsPaginator,
    ListChannelsPaginator,
    ListCloudWatchAlarmTemplateGroupsPaginator,
    ListCloudWatchAlarmTemplatesPaginator,
    ListClusterAlertsPaginator,
    ListClustersPaginator,
    ListEventBridgeRuleTemplateGroupsPaginator,
    ListEventBridgeRuleTemplatesPaginator,
    ListInputDeviceTransfersPaginator,
    ListInputDevicesPaginator,
    ListInputSecurityGroupsPaginator,
    ListInputsPaginator,
    ListMultiplexAlertsPaginator,
    ListMultiplexProgramsPaginator,
    ListMultiplexesPaginator,
    ListNetworksPaginator,
    ListNodesPaginator,
    ListOfferingsPaginator,
    ListReservationsPaginator,
    ListSdiSourcesPaginator,
    ListSignalMapsPaginator,
)

client: MediaLiveClient = Session().client("medialive")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
describe_schedule_paginator: DescribeSchedulePaginator = client.get_paginator("describe_schedule")
list_alerts_paginator: ListAlertsPaginator = client.get_paginator("list_alerts")
list_channel_placement_groups_paginator: ListChannelPlacementGroupsPaginator = client.get_paginator(
    "list_channel_placement_groups"
)
list_channels_paginator: ListChannelsPaginator = client.get_paginator("list_channels")
list_cloud_watch_alarm_template_groups_paginator: ListCloudWatchAlarmTemplateGroupsPaginator = (
    client.get_paginator("list_cloud_watch_alarm_template_groups")
)
list_cloud_watch_alarm_templates_paginator: ListCloudWatchAlarmTemplatesPaginator = (
    client.get_paginator("list_cloud_watch_alarm_templates")
)
list_cluster_alerts_paginator: ListClusterAlertsPaginator = client.get_paginator(
    "list_cluster_alerts"
)
list_clusters_paginator: ListClustersPaginator = client.get_paginator("list_clusters")
list_event_bridge_rule_template_groups_paginator: ListEventBridgeRuleTemplateGroupsPaginator = (
    client.get_paginator("list_event_bridge_rule_template_groups")
)
list_event_bridge_rule_templates_paginator: ListEventBridgeRuleTemplatesPaginator = (
    client.get_paginator("list_event_bridge_rule_templates")
)
list_input_device_transfers_paginator: ListInputDeviceTransfersPaginator = client.get_paginator(
    "list_input_device_transfers"
)
list_input_devices_paginator: ListInputDevicesPaginator = client.get_paginator("list_input_devices")
list_input_security_groups_paginator: ListInputSecurityGroupsPaginator = client.get_paginator(
    "list_input_security_groups"
)
list_inputs_paginator: ListInputsPaginator = client.get_paginator("list_inputs")
list_multiplex_alerts_paginator: ListMultiplexAlertsPaginator = client.get_paginator(
    "list_multiplex_alerts"
)
list_multiplex_programs_paginator: ListMultiplexProgramsPaginator = client.get_paginator(
    "list_multiplex_programs"
)
list_multiplexes_paginator: ListMultiplexesPaginator = client.get_paginator("list_multiplexes")
list_networks_paginator: ListNetworksPaginator = client.get_paginator("list_networks")
list_nodes_paginator: ListNodesPaginator = client.get_paginator("list_nodes")
list_offerings_paginator: ListOfferingsPaginator = client.get_paginator("list_offerings")
list_reservations_paginator: ListReservationsPaginator = client.get_paginator("list_reservations")
list_sdi_sources_paginator: ListSdiSourcesPaginator = client.get_paginator("list_sdi_sources")
list_signal_maps_paginator: ListSignalMapsPaginator = client.get_paginator("list_signal_maps")
```

<a id="waiters-annotations"></a>

### Waiters annotations

`types_boto3_medialive.waiter` module contains type annotations for all
waiters.

```python
from boto3.session import Session

from types_boto3_medialive import MediaLiveClient
from types_boto3_medialive.waiter import (
    ChannelCreatedWaiter,
    ChannelDeletedWaiter,
    ChannelPlacementGroupAssignedWaiter,
    ChannelPlacementGroupDeletedWaiter,
    ChannelPlacementGroupUnassignedWaiter,
    ChannelRunningWaiter,
    ChannelStoppedWaiter,
    ClusterCreatedWaiter,
    ClusterDeletedWaiter,
    InputAttachedWaiter,
    InputDeletedWaiter,
    InputDetachedWaiter,
    MultiplexCreatedWaiter,
    MultiplexDeletedWaiter,
    MultiplexRunningWaiter,
    MultiplexStoppedWaiter,
    NodeDeregisteredWaiter,
    NodeRegisteredWaiter,
    SignalMapCreatedWaiter,
    SignalMapMonitorDeletedWaiter,
    SignalMapMonitorDeployedWaiter,
    SignalMapUpdatedWaiter,
)

client: MediaLiveClient = Session().client("medialive")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
channel_created_waiter: ChannelCreatedWaiter = client.get_waiter("channel_created")
channel_deleted_waiter: ChannelDeletedWaiter = client.get_waiter("channel_deleted")
channel_placement_group_assigned_waiter: ChannelPlacementGroupAssignedWaiter = client.get_waiter(
    "channel_placement_group_assigned"
)
channel_placement_group_deleted_waiter: ChannelPlacementGroupDeletedWaiter = client.get_waiter(
    "channel_placement_group_deleted"
)
channel_placement_group_unassigned_waiter: ChannelPlacementGroupUnassignedWaiter = (
    client.get_waiter("channel_placement_group_unassigned")
)
channel_running_waiter: ChannelRunningWaiter = client.get_waiter("channel_running")
channel_stopped_waiter: ChannelStoppedWaiter = client.get_waiter("channel_stopped")
cluster_created_waiter: ClusterCreatedWaiter = client.get_waiter("cluster_created")
cluster_deleted_waiter: ClusterDeletedWaiter = client.get_waiter("cluster_deleted")
input_attached_waiter: InputAttachedWaiter = client.get_waiter("input_attached")
input_deleted_waiter: InputDeletedWaiter = client.get_waiter("input_deleted")
input_detached_waiter: InputDetachedWaiter = client.get_waiter("input_detached")
multiplex_created_waiter: MultiplexCreatedWaiter = client.get_waiter("multiplex_created")
multiplex_deleted_waiter: MultiplexDeletedWaiter = client.get_waiter("multiplex_deleted")
multiplex_running_waiter: MultiplexRunningWaiter = client.get_waiter("multiplex_running")
multiplex_stopped_waiter: MultiplexStoppedWaiter = client.get_waiter("multiplex_stopped")
node_deregistered_waiter: NodeDeregisteredWaiter = client.get_waiter("node_deregistered")
node_registered_waiter: NodeRegisteredWaiter = client.get_waiter("node_registered")
signal_map_created_waiter: SignalMapCreatedWaiter = client.get_waiter("signal_map_created")
signal_map_monitor_deleted_waiter: SignalMapMonitorDeletedWaiter = client.get_waiter(
    "signal_map_monitor_deleted"
)
signal_map_monitor_deployed_waiter: SignalMapMonitorDeployedWaiter = client.get_waiter(
    "signal_map_monitor_deployed"
)
signal_map_updated_waiter: SignalMapUpdatedWaiter = client.get_waiter("signal_map_updated")
```

<a id="literals"></a>

### Literals

`types_boto3_medialive.literals` module contains literals extracted from shapes
that can be used in user code for type checking.

Full list of `MediaLive` Literals can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/literals/).

```python
from types_boto3_medialive.literals import AacCodingModeType


def check_value(value: AacCodingModeType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`types_boto3_medialive.type_defs` module contains structures and shapes
assembled to typed dictionaries and unions for additional type checking.

Full list of `MediaLive` TypeDefs can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/type_defs/).

```python
# TypedDict usage example
from types_boto3_medialive.type_defs import AacSettingsTypeDef


def get_value() -> AacSettingsTypeDef:
    return {
        "Bitrate": ...,
    }
```

<a id="how-it-works"></a>

## How it works

Fully automated
[mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder) carefully
generates type annotations for each service, patiently waiting for `boto3`
updates. It delivers drop-in type annotations for you and makes sure that:

- All available `boto3` services are covered.
- Each public class and method of every `boto3` service gets valid type
  annotations extracted from `botocore` schemas.
- Type annotations include up-to-date documentation.
- Link to documentation is provided for every method.
- Code is processed by [ruff](https://docs.astral.sh/ruff/) for readability.

<a id="what's-new"></a>

## What's new

<a id="implemented-features"></a>

### Implemented features

- Fully type annotated `boto3`, `botocore`, `aiobotocore` and `aioboto3`
  libraries
- `mypy`, `pyright`, `VSCode`, `PyCharm`, `Sublime Text` and `Emacs`
  compatibility
- `Client`, `ServiceResource`, `Resource`, `Waiter` `Paginator` type
  annotations for each service
- Generated `TypeDefs` for each service
- Generated `Literals` for each service
- Auto discovery of types for `boto3.client` and `boto3.resource` calls
- Auto discovery of types for `session.client` and `session.resource` calls
- Auto discovery of types for `client.get_waiter` and `client.get_paginator`
  calls
- Auto discovery of types for `ServiceResource` and `Resource` collections
- Auto discovery of types for `aiobotocore.Session.create_client` calls

<a id="latest-changes"></a>

### Latest changes

Builder changelog can be found in
[Releases](https://github.com/youtype/mypy_boto3_builder/releases).

<a id="versioning"></a>

## Versioning

`types-boto3-medialive` version is the same as related `boto3` version and
follows
[Python Packaging version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/).

<a id="thank-you"></a>

## Thank you

- [Allie Fitter](https://github.com/alliefitter) for
  [boto3-type-annotations](https://pypi.org/project/boto3-type-annotations/),
  this package is based on top of his work
- [black](https://github.com/psf/black) developers for an awesome formatting
  tool
- [Timothy Edmund Crosley](https://github.com/timothycrosley) for
  [isort](https://github.com/PyCQA/isort) and how flexible it is
- [mypy](https://github.com/python/mypy) developers for doing all dirty work
  for us
- [pyright](https://github.com/microsoft/pyright) team for the new era of typed
  Python

<a id="documentation"></a>

## Documentation

All services type annotations can be found in
[boto3 docs](https://youtype.github.io/types_boto3_docs/types_boto3_medialive/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
