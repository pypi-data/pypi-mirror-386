<a id="types-boto3-eks"></a>

# types-boto3-eks

[![PyPI - types-boto3-eks](https://img.shields.io/pypi/v/types-boto3-eks.svg?color=blue)](https://pypi.org/project/types-boto3-eks/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/types-boto3-eks.svg?color=blue)](https://pypi.org/project/types-boto3-eks/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/types_boto3_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/types-boto3-eks)](https://pypistats.org/packages/types-boto3-eks)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 EKS 1.40.59](https://pypi.org/project/boto3/)
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
[types-boto3-eks docs](https://youtype.github.io/types_boto3_docs/types_boto3_eks/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [types-boto3-eks](#types-boto3-eks)
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
   `uvx --with 'boto3==1.40.59' mypy-boto3-builder`
2. Select `boto3` AWS SDK.
3. Add `EKS` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `EKS`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `types-boto3` for `EKS` service.

```bash
# install with boto3 type annotations
python -m pip install 'types-boto3[eks]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'types-boto3-lite[eks]'

# standalone installation
python -m pip install types-boto3-eks
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y types-boto3-eks
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
- Install `types-boto3[eks]` in your environment:

```bash
python -m pip install 'types-boto3[eks]'
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

Install `types-boto3[eks]` in your environment:

```bash
python -m pip install 'types-boto3[eks]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `types-boto3` with services you use in your environment:

```bash
python -m pip install 'types-boto3[eks]'
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

- Install `types-boto3[eks]` with services you use in your environment:

```bash
python -m pip install 'types-boto3[eks]'
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
- Install `types-boto3[eks]` in your environment:

```bash
python -m pip install 'types-boto3[eks]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `types-boto3[eks]` in your environment:

```bash
python -m pip install 'types-boto3[eks]'
```

Optionally, you can install `types-boto3` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`types-boto3-eks` dependency in production. However, there is an issue in
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

`EKSClient` provides annotations for `boto3.client("eks")`.

```python
from boto3.session import Session

from types_boto3_eks import EKSClient

client: EKSClient = Session().client("eks")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`types_boto3_eks.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from types_boto3_eks import EKSClient
from types_boto3_eks.paginator import (
    DescribeAddonVersionsPaginator,
    DescribeClusterVersionsPaginator,
    ListAccessEntriesPaginator,
    ListAccessPoliciesPaginator,
    ListAddonsPaginator,
    ListAssociatedAccessPoliciesPaginator,
    ListClustersPaginator,
    ListEksAnywhereSubscriptionsPaginator,
    ListFargateProfilesPaginator,
    ListIdentityProviderConfigsPaginator,
    ListInsightsPaginator,
    ListNodegroupsPaginator,
    ListPodIdentityAssociationsPaginator,
    ListUpdatesPaginator,
)

client: EKSClient = Session().client("eks")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
describe_addon_versions_paginator: DescribeAddonVersionsPaginator = client.get_paginator(
    "describe_addon_versions"
)
describe_cluster_versions_paginator: DescribeClusterVersionsPaginator = client.get_paginator(
    "describe_cluster_versions"
)
list_access_entries_paginator: ListAccessEntriesPaginator = client.get_paginator(
    "list_access_entries"
)
list_access_policies_paginator: ListAccessPoliciesPaginator = client.get_paginator(
    "list_access_policies"
)
list_addons_paginator: ListAddonsPaginator = client.get_paginator("list_addons")
list_associated_access_policies_paginator: ListAssociatedAccessPoliciesPaginator = (
    client.get_paginator("list_associated_access_policies")
)
list_clusters_paginator: ListClustersPaginator = client.get_paginator("list_clusters")
list_eks_anywhere_subscriptions_paginator: ListEksAnywhereSubscriptionsPaginator = (
    client.get_paginator("list_eks_anywhere_subscriptions")
)
list_fargate_profiles_paginator: ListFargateProfilesPaginator = client.get_paginator(
    "list_fargate_profiles"
)
list_identity_provider_configs_paginator: ListIdentityProviderConfigsPaginator = (
    client.get_paginator("list_identity_provider_configs")
)
list_insights_paginator: ListInsightsPaginator = client.get_paginator("list_insights")
list_nodegroups_paginator: ListNodegroupsPaginator = client.get_paginator("list_nodegroups")
list_pod_identity_associations_paginator: ListPodIdentityAssociationsPaginator = (
    client.get_paginator("list_pod_identity_associations")
)
list_updates_paginator: ListUpdatesPaginator = client.get_paginator("list_updates")
```

<a id="waiters-annotations"></a>

### Waiters annotations

`types_boto3_eks.waiter` module contains type annotations for all waiters.

```python
from boto3.session import Session

from types_boto3_eks import EKSClient
from types_boto3_eks.waiter import (
    AddonActiveWaiter,
    AddonDeletedWaiter,
    ClusterActiveWaiter,
    ClusterDeletedWaiter,
    FargateProfileActiveWaiter,
    FargateProfileDeletedWaiter,
    NodegroupActiveWaiter,
    NodegroupDeletedWaiter,
)

client: EKSClient = Session().client("eks")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
addon_active_waiter: AddonActiveWaiter = client.get_waiter("addon_active")
addon_deleted_waiter: AddonDeletedWaiter = client.get_waiter("addon_deleted")
cluster_active_waiter: ClusterActiveWaiter = client.get_waiter("cluster_active")
cluster_deleted_waiter: ClusterDeletedWaiter = client.get_waiter("cluster_deleted")
fargate_profile_active_waiter: FargateProfileActiveWaiter = client.get_waiter(
    "fargate_profile_active"
)
fargate_profile_deleted_waiter: FargateProfileDeletedWaiter = client.get_waiter(
    "fargate_profile_deleted"
)
nodegroup_active_waiter: NodegroupActiveWaiter = client.get_waiter("nodegroup_active")
nodegroup_deleted_waiter: NodegroupDeletedWaiter = client.get_waiter("nodegroup_deleted")
```

<a id="literals"></a>

### Literals

`types_boto3_eks.literals` module contains literals extracted from shapes that
can be used in user code for type checking.

Full list of `EKS` Literals can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_eks/literals/).

```python
from types_boto3_eks.literals import AMITypesType


def check_value(value: AMITypesType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`types_boto3_eks.type_defs` module contains structures and shapes assembled to
typed dictionaries and unions for additional type checking.

Full list of `EKS` TypeDefs can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_eks/type_defs/).

```python
# TypedDict usage example
from types_boto3_eks.type_defs import AccessConfigResponseTypeDef


def get_value() -> AccessConfigResponseTypeDef:
    return {
        "bootstrapClusterCreatorAdminPermissions": ...,
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

`types-boto3-eks` version is the same as related `boto3` version and follows
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
[boto3 docs](https://youtype.github.io/types_boto3_docs/types_boto3_eks/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
