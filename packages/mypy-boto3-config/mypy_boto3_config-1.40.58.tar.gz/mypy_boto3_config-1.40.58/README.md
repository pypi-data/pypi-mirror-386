<a id="mypy-boto3-config"></a>

# mypy-boto3-config

[![PyPI - mypy-boto3-config](https://img.shields.io/pypi/v/mypy-boto3-config.svg?color=blue)](https://pypi.org/project/mypy-boto3-config/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mypy-boto3-config.svg?color=blue)](https://pypi.org/project/mypy-boto3-config/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/boto3_stubs_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/mypy-boto3-config)](https://pypistats.org/packages/mypy-boto3-config)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for
[boto3 ConfigService 1.40.58](https://pypi.org/project/boto3/) compatible with
[VSCode](https://code.visualstudio.com/),
[PyCharm](https://www.jetbrains.com/pycharm/),
[Emacs](https://www.gnu.org/software/emacs/),
[Sublime Text](https://www.sublimetext.com/),
[mypy](https://github.com/python/mypy),
[pyright](https://github.com/microsoft/pyright) and other tools.

Generated with
[mypy-boto3-builder 8.11.0](https://github.com/youtype/mypy_boto3_builder).

More information can be found on
[boto3-stubs](https://pypi.org/project/boto3-stubs/) page and in
[mypy-boto3-config docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_config/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [mypy-boto3-config](#mypy-boto3-config)
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
   `uvx --with 'boto3==1.40.58' mypy-boto3-builder`
2. Select `boto3-stubs` AWS SDK.
3. Add `ConfigService` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `ConfigService`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `boto3-stubs` for `ConfigService` service.

```bash
# install with boto3 type annotations
python -m pip install 'boto3-stubs[config]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'boto3-stubs-lite[config]'

# standalone installation
python -m pip install mypy-boto3-config
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y mypy-boto3-config
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
- Install `boto3-stubs[config]` in your environment:

```bash
python -m pip install 'boto3-stubs[config]'
```

Both type checking and code completion should now work. No explicit type
annotations required, write your `boto3` code as usual.

<a id="pycharm"></a>

### PyCharm

> ⚠️ Due to slow PyCharm performance on `Literal` overloads (issue
> [PY-40997](https://youtrack.jetbrains.com/issue/PY-40997)), it is recommended
> to use [boto3-stubs-lite](https://pypi.org/project/boto3-stubs-lite/) until
> the issue is resolved.

> ⚠️ If you experience slow performance and high CPU usage, try to disable
> `PyCharm` type checker and use [mypy](https://github.com/python/mypy) or
> [pyright](https://github.com/microsoft/pyright) instead.

> ⚠️ To continue using `PyCharm` type checker, you can try to replace
> `boto3-stubs` with
> [boto3-stubs-lite](https://pypi.org/project/boto3-stubs-lite/):

```bash
pip uninstall boto3-stubs
pip install boto3-stubs-lite
```

Install `boto3-stubs[config]` in your environment:

```bash
python -m pip install 'boto3-stubs[config]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `boto3-stubs` with services you use in your environment:

```bash
python -m pip install 'boto3-stubs[config]'
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

- Make sure emacs uses the environment where you have installed `boto3-stubs`

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="sublime-text"></a>

### Sublime Text

- Install `boto3-stubs[config]` with services you use in your environment:

```bash
python -m pip install 'boto3-stubs[config]'
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
- Install `boto3-stubs[config]` in your environment:

```bash
python -m pip install 'boto3-stubs[config]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `boto3-stubs[config]` in your environment:

```bash
python -m pip install 'boto3-stubs[config]'
```

Optionally, you can install `boto3-stubs` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`mypy-boto3-config` dependency in production. However, there is an issue in
`pylint` that it complains about undefined variables. To fix it, set all types
to `object` in non-`TYPE_CHECKING` mode.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_ec2 import EC2Client, EC2ServiceResource
    from mypy_boto3_ec2.waiters import BundleTaskCompleteWaiter
    from mypy_boto3_ec2.paginators import DescribeVolumesPaginator
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

`ConfigServiceClient` provides annotations for `boto3.client("config")`.

```python
from boto3.session import Session

from mypy_boto3_config import ConfigServiceClient

client: ConfigServiceClient = Session().client("config")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`mypy_boto3_config.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from mypy_boto3_config import ConfigServiceClient
from mypy_boto3_config.paginator import (
    DescribeAggregateComplianceByConfigRulesPaginator,
    DescribeAggregateComplianceByConformancePacksPaginator,
    DescribeAggregationAuthorizationsPaginator,
    DescribeComplianceByConfigRulePaginator,
    DescribeComplianceByResourcePaginator,
    DescribeConfigRuleEvaluationStatusPaginator,
    DescribeConfigRulesPaginator,
    DescribeConfigurationAggregatorSourcesStatusPaginator,
    DescribeConfigurationAggregatorsPaginator,
    DescribeConformancePackStatusPaginator,
    DescribeConformancePacksPaginator,
    DescribeOrganizationConfigRuleStatusesPaginator,
    DescribeOrganizationConfigRulesPaginator,
    DescribeOrganizationConformancePackStatusesPaginator,
    DescribeOrganizationConformancePacksPaginator,
    DescribePendingAggregationRequestsPaginator,
    DescribeRemediationExecutionStatusPaginator,
    DescribeRetentionConfigurationsPaginator,
    GetAggregateComplianceDetailsByConfigRulePaginator,
    GetComplianceDetailsByConfigRulePaginator,
    GetComplianceDetailsByResourcePaginator,
    GetConformancePackComplianceSummaryPaginator,
    GetOrganizationConfigRuleDetailedStatusPaginator,
    GetOrganizationConformancePackDetailedStatusPaginator,
    GetResourceConfigHistoryPaginator,
    ListAggregateDiscoveredResourcesPaginator,
    ListConfigurationRecordersPaginator,
    ListDiscoveredResourcesPaginator,
    ListResourceEvaluationsPaginator,
    ListTagsForResourcePaginator,
    SelectAggregateResourceConfigPaginator,
    SelectResourceConfigPaginator,
)

client: ConfigServiceClient = Session().client("config")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
describe_aggregate_compliance_by_config_rules_paginator: DescribeAggregateComplianceByConfigRulesPaginator = client.get_paginator(
    "describe_aggregate_compliance_by_config_rules"
)
describe_aggregate_compliance_by_conformance_packs_paginator: DescribeAggregateComplianceByConformancePacksPaginator = client.get_paginator(
    "describe_aggregate_compliance_by_conformance_packs"
)
describe_aggregation_authorizations_paginator: DescribeAggregationAuthorizationsPaginator = (
    client.get_paginator("describe_aggregation_authorizations")
)
describe_compliance_by_config_rule_paginator: DescribeComplianceByConfigRulePaginator = (
    client.get_paginator("describe_compliance_by_config_rule")
)
describe_compliance_by_resource_paginator: DescribeComplianceByResourcePaginator = (
    client.get_paginator("describe_compliance_by_resource")
)
describe_config_rule_evaluation_status_paginator: DescribeConfigRuleEvaluationStatusPaginator = (
    client.get_paginator("describe_config_rule_evaluation_status")
)
describe_config_rules_paginator: DescribeConfigRulesPaginator = client.get_paginator(
    "describe_config_rules"
)
describe_configuration_aggregator_sources_status_paginator: DescribeConfigurationAggregatorSourcesStatusPaginator = client.get_paginator(
    "describe_configuration_aggregator_sources_status"
)
describe_configuration_aggregators_paginator: DescribeConfigurationAggregatorsPaginator = (
    client.get_paginator("describe_configuration_aggregators")
)
describe_conformance_pack_status_paginator: DescribeConformancePackStatusPaginator = (
    client.get_paginator("describe_conformance_pack_status")
)
describe_conformance_packs_paginator: DescribeConformancePacksPaginator = client.get_paginator(
    "describe_conformance_packs"
)
describe_organization_config_rule_statuses_paginator: DescribeOrganizationConfigRuleStatusesPaginator = client.get_paginator(
    "describe_organization_config_rule_statuses"
)
describe_organization_config_rules_paginator: DescribeOrganizationConfigRulesPaginator = (
    client.get_paginator("describe_organization_config_rules")
)
describe_organization_conformance_pack_statuses_paginator: DescribeOrganizationConformancePackStatusesPaginator = client.get_paginator(
    "describe_organization_conformance_pack_statuses"
)
describe_organization_conformance_packs_paginator: DescribeOrganizationConformancePacksPaginator = (
    client.get_paginator("describe_organization_conformance_packs")
)
describe_pending_aggregation_requests_paginator: DescribePendingAggregationRequestsPaginator = (
    client.get_paginator("describe_pending_aggregation_requests")
)
describe_remediation_execution_status_paginator: DescribeRemediationExecutionStatusPaginator = (
    client.get_paginator("describe_remediation_execution_status")
)
describe_retention_configurations_paginator: DescribeRetentionConfigurationsPaginator = (
    client.get_paginator("describe_retention_configurations")
)
get_aggregate_compliance_details_by_config_rule_paginator: GetAggregateComplianceDetailsByConfigRulePaginator = client.get_paginator(
    "get_aggregate_compliance_details_by_config_rule"
)
get_compliance_details_by_config_rule_paginator: GetComplianceDetailsByConfigRulePaginator = (
    client.get_paginator("get_compliance_details_by_config_rule")
)
get_compliance_details_by_resource_paginator: GetComplianceDetailsByResourcePaginator = (
    client.get_paginator("get_compliance_details_by_resource")
)
get_conformance_pack_compliance_summary_paginator: GetConformancePackComplianceSummaryPaginator = (
    client.get_paginator("get_conformance_pack_compliance_summary")
)
get_organization_config_rule_detailed_status_paginator: GetOrganizationConfigRuleDetailedStatusPaginator = client.get_paginator(
    "get_organization_config_rule_detailed_status"
)
get_organization_conformance_pack_detailed_status_paginator: GetOrganizationConformancePackDetailedStatusPaginator = client.get_paginator(
    "get_organization_conformance_pack_detailed_status"
)
get_resource_config_history_paginator: GetResourceConfigHistoryPaginator = client.get_paginator(
    "get_resource_config_history"
)
list_aggregate_discovered_resources_paginator: ListAggregateDiscoveredResourcesPaginator = (
    client.get_paginator("list_aggregate_discovered_resources")
)
list_configuration_recorders_paginator: ListConfigurationRecordersPaginator = client.get_paginator(
    "list_configuration_recorders"
)
list_discovered_resources_paginator: ListDiscoveredResourcesPaginator = client.get_paginator(
    "list_discovered_resources"
)
list_resource_evaluations_paginator: ListResourceEvaluationsPaginator = client.get_paginator(
    "list_resource_evaluations"
)
list_tags_for_resource_paginator: ListTagsForResourcePaginator = client.get_paginator(
    "list_tags_for_resource"
)
select_aggregate_resource_config_paginator: SelectAggregateResourceConfigPaginator = (
    client.get_paginator("select_aggregate_resource_config")
)
select_resource_config_paginator: SelectResourceConfigPaginator = client.get_paginator(
    "select_resource_config"
)
```

<a id="literals"></a>

### Literals

`mypy_boto3_config.literals` module contains literals extracted from shapes
that can be used in user code for type checking.

Full list of `ConfigService` Literals can be found in
[docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_config/literals/).

```python
from mypy_boto3_config.literals import AggregateConformancePackComplianceSummaryGroupKeyType


def check_value(value: AggregateConformancePackComplianceSummaryGroupKeyType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`mypy_boto3_config.type_defs` module contains structures and shapes assembled
to typed dictionaries and unions for additional type checking.

Full list of `ConfigService` TypeDefs can be found in
[docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_config/type_defs/).

```python
# TypedDict usage example
from mypy_boto3_config.type_defs import AccountAggregationSourceOutputTypeDef


def get_value() -> AccountAggregationSourceOutputTypeDef:
    return {
        "AccountIds": ...,
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

`mypy-boto3-config` version is the same as related `boto3` version and follows
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
[boto3 docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_config/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
