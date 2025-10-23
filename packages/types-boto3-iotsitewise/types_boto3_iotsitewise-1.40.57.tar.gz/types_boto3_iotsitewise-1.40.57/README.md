<a id="types-boto3-iotsitewise"></a>

# types-boto3-iotsitewise

[![PyPI - types-boto3-iotsitewise](https://img.shields.io/pypi/v/types-boto3-iotsitewise.svg?color=blue)](https://pypi.org/project/types-boto3-iotsitewise/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/types-boto3-iotsitewise.svg?color=blue)](https://pypi.org/project/types-boto3-iotsitewise/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/types_boto3_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/types-boto3-iotsitewise)](https://pypistats.org/packages/types-boto3-iotsitewise)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for
[boto3 IoTSiteWise 1.40.57](https://pypi.org/project/boto3/) compatible with
[VSCode](https://code.visualstudio.com/),
[PyCharm](https://www.jetbrains.com/pycharm/),
[Emacs](https://www.gnu.org/software/emacs/),
[Sublime Text](https://www.sublimetext.com/),
[mypy](https://github.com/python/mypy),
[pyright](https://github.com/microsoft/pyright) and other tools.

Generated with
[mypy-boto3-builder 8.11.0](https://github.com/youtype/mypy_boto3_builder).

More information can be found on
[types-boto3](https://pypi.org/project/types-boto3/) page and in
[types-boto3-iotsitewise docs](https://youtype.github.io/types_boto3_docs/types_boto3_iotsitewise/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [types-boto3-iotsitewise](#types-boto3-iotsitewise)
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
3. Add `IoTSiteWise` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `IoTSiteWise`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `types-boto3` for `IoTSiteWise` service.

```bash
# install with boto3 type annotations
python -m pip install 'types-boto3[iotsitewise]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'types-boto3-lite[iotsitewise]'

# standalone installation
python -m pip install types-boto3-iotsitewise
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y types-boto3-iotsitewise
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
- Install `types-boto3[iotsitewise]` in your environment:

```bash
python -m pip install 'types-boto3[iotsitewise]'
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

Install `types-boto3[iotsitewise]` in your environment:

```bash
python -m pip install 'types-boto3[iotsitewise]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `types-boto3` with services you use in your environment:

```bash
python -m pip install 'types-boto3[iotsitewise]'
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

- Install `types-boto3[iotsitewise]` with services you use in your environment:

```bash
python -m pip install 'types-boto3[iotsitewise]'
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
- Install `types-boto3[iotsitewise]` in your environment:

```bash
python -m pip install 'types-boto3[iotsitewise]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `types-boto3[iotsitewise]` in your environment:

```bash
python -m pip install 'types-boto3[iotsitewise]'
```

Optionally, you can install `types-boto3` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`types-boto3-iotsitewise` dependency in production. However, there is an issue
in `pylint` that it complains about undefined variables. To fix it, set all
types to `object` in non-`TYPE_CHECKING` mode.

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

`IoTSiteWiseClient` provides annotations for `boto3.client("iotsitewise")`.

```python
from boto3.session import Session

from types_boto3_iotsitewise import IoTSiteWiseClient

client: IoTSiteWiseClient = Session().client("iotsitewise")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`types_boto3_iotsitewise.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from types_boto3_iotsitewise import IoTSiteWiseClient
from types_boto3_iotsitewise.paginator import (
    ExecuteQueryPaginator,
    GetAssetPropertyAggregatesPaginator,
    GetAssetPropertyValueHistoryPaginator,
    GetInterpolatedAssetPropertyValuesPaginator,
    ListAccessPoliciesPaginator,
    ListActionsPaginator,
    ListAssetModelCompositeModelsPaginator,
    ListAssetModelPropertiesPaginator,
    ListAssetModelsPaginator,
    ListAssetPropertiesPaginator,
    ListAssetRelationshipsPaginator,
    ListAssetsPaginator,
    ListAssociatedAssetsPaginator,
    ListBulkImportJobsPaginator,
    ListCompositionRelationshipsPaginator,
    ListComputationModelDataBindingUsagesPaginator,
    ListComputationModelResolveToResourcesPaginator,
    ListComputationModelsPaginator,
    ListDashboardsPaginator,
    ListDatasetsPaginator,
    ListExecutionsPaginator,
    ListGatewaysPaginator,
    ListInterfaceRelationshipsPaginator,
    ListPortalsPaginator,
    ListProjectAssetsPaginator,
    ListProjectsPaginator,
    ListTimeSeriesPaginator,
)

client: IoTSiteWiseClient = Session().client("iotsitewise")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
execute_query_paginator: ExecuteQueryPaginator = client.get_paginator("execute_query")
get_asset_property_aggregates_paginator: GetAssetPropertyAggregatesPaginator = client.get_paginator(
    "get_asset_property_aggregates"
)
get_asset_property_value_history_paginator: GetAssetPropertyValueHistoryPaginator = (
    client.get_paginator("get_asset_property_value_history")
)
get_interpolated_asset_property_values_paginator: GetInterpolatedAssetPropertyValuesPaginator = (
    client.get_paginator("get_interpolated_asset_property_values")
)
list_access_policies_paginator: ListAccessPoliciesPaginator = client.get_paginator(
    "list_access_policies"
)
list_actions_paginator: ListActionsPaginator = client.get_paginator("list_actions")
list_asset_model_composite_models_paginator: ListAssetModelCompositeModelsPaginator = (
    client.get_paginator("list_asset_model_composite_models")
)
list_asset_model_properties_paginator: ListAssetModelPropertiesPaginator = client.get_paginator(
    "list_asset_model_properties"
)
list_asset_models_paginator: ListAssetModelsPaginator = client.get_paginator("list_asset_models")
list_asset_properties_paginator: ListAssetPropertiesPaginator = client.get_paginator(
    "list_asset_properties"
)
list_asset_relationships_paginator: ListAssetRelationshipsPaginator = client.get_paginator(
    "list_asset_relationships"
)
list_assets_paginator: ListAssetsPaginator = client.get_paginator("list_assets")
list_associated_assets_paginator: ListAssociatedAssetsPaginator = client.get_paginator(
    "list_associated_assets"
)
list_bulk_import_jobs_paginator: ListBulkImportJobsPaginator = client.get_paginator(
    "list_bulk_import_jobs"
)
list_composition_relationships_paginator: ListCompositionRelationshipsPaginator = (
    client.get_paginator("list_composition_relationships")
)
list_computation_model_data_binding_usages_paginator: ListComputationModelDataBindingUsagesPaginator = client.get_paginator(
    "list_computation_model_data_binding_usages"
)
list_computation_model_resolve_to_resources_paginator: ListComputationModelResolveToResourcesPaginator = client.get_paginator(
    "list_computation_model_resolve_to_resources"
)
list_computation_models_paginator: ListComputationModelsPaginator = client.get_paginator(
    "list_computation_models"
)
list_dashboards_paginator: ListDashboardsPaginator = client.get_paginator("list_dashboards")
list_datasets_paginator: ListDatasetsPaginator = client.get_paginator("list_datasets")
list_executions_paginator: ListExecutionsPaginator = client.get_paginator("list_executions")
list_gateways_paginator: ListGatewaysPaginator = client.get_paginator("list_gateways")
list_interface_relationships_paginator: ListInterfaceRelationshipsPaginator = client.get_paginator(
    "list_interface_relationships"
)
list_portals_paginator: ListPortalsPaginator = client.get_paginator("list_portals")
list_project_assets_paginator: ListProjectAssetsPaginator = client.get_paginator(
    "list_project_assets"
)
list_projects_paginator: ListProjectsPaginator = client.get_paginator("list_projects")
list_time_series_paginator: ListTimeSeriesPaginator = client.get_paginator("list_time_series")
```

<a id="waiters-annotations"></a>

### Waiters annotations

`types_boto3_iotsitewise.waiter` module contains type annotations for all
waiters.

```python
from boto3.session import Session

from types_boto3_iotsitewise import IoTSiteWiseClient
from types_boto3_iotsitewise.waiter import (
    AssetActiveWaiter,
    AssetModelActiveWaiter,
    AssetModelNotExistsWaiter,
    AssetNotExistsWaiter,
    PortalActiveWaiter,
    PortalNotExistsWaiter,
)

client: IoTSiteWiseClient = Session().client("iotsitewise")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
asset_active_waiter: AssetActiveWaiter = client.get_waiter("asset_active")
asset_model_active_waiter: AssetModelActiveWaiter = client.get_waiter("asset_model_active")
asset_model_not_exists_waiter: AssetModelNotExistsWaiter = client.get_waiter(
    "asset_model_not_exists"
)
asset_not_exists_waiter: AssetNotExistsWaiter = client.get_waiter("asset_not_exists")
portal_active_waiter: PortalActiveWaiter = client.get_waiter("portal_active")
portal_not_exists_waiter: PortalNotExistsWaiter = client.get_waiter("portal_not_exists")
```

<a id="literals"></a>

### Literals

`types_boto3_iotsitewise.literals` module contains literals extracted from
shapes that can be used in user code for type checking.

Full list of `IoTSiteWise` Literals can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_iotsitewise/literals/).

```python
from types_boto3_iotsitewise.literals import AggregateTypeType


def check_value(value: AggregateTypeType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`types_boto3_iotsitewise.type_defs` module contains structures and shapes
assembled to typed dictionaries and unions for additional type checking.

Full list of `IoTSiteWise` TypeDefs can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_iotsitewise/type_defs/).

```python
# TypedDict usage example
from types_boto3_iotsitewise.type_defs import AccessDeniedExceptionTypeDef


def get_value() -> AccessDeniedExceptionTypeDef:
    return {
        "message": ...,
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

`types-boto3-iotsitewise` version is the same as related `boto3` version and
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
[boto3 docs](https://youtype.github.io/types_boto3_docs/types_boto3_iotsitewise/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
