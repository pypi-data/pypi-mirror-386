<a id="mypy-boto3-iot"></a>

# mypy-boto3-iot

[![PyPI - mypy-boto3-iot](https://img.shields.io/pypi/v/mypy-boto3-iot.svg?color=blue)](https://pypi.org/project/mypy-boto3-iot/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mypy-boto3-iot.svg?color=blue)](https://pypi.org/project/mypy-boto3-iot/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/boto3_stubs_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/mypy-boto3-iot)](https://pypistats.org/packages/mypy-boto3-iot)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 IoT 1.40.57](https://pypi.org/project/boto3/)
compatible with [VSCode](https://code.visualstudio.com/),
[PyCharm](https://www.jetbrains.com/pycharm/),
[Emacs](https://www.gnu.org/software/emacs/),
[Sublime Text](https://www.sublimetext.com/),
[mypy](https://github.com/python/mypy),
[pyright](https://github.com/microsoft/pyright) and other tools.

Generated with
[mypy-boto3-builder 8.11.0](https://github.com/youtype/mypy_boto3_builder).

More information can be found on
[boto3-stubs](https://pypi.org/project/boto3-stubs/) page and in
[mypy-boto3-iot docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [mypy-boto3-iot](#mypy-boto3-iot)
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
   `uvx --with 'boto3==1.40.57' mypy-boto3-builder`
2. Select `boto3-stubs` AWS SDK.
3. Add `IoT` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `IoT`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `boto3-stubs` for `IoT` service.

```bash
# install with boto3 type annotations
python -m pip install 'boto3-stubs[iot]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'boto3-stubs-lite[iot]'

# standalone installation
python -m pip install mypy-boto3-iot
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y mypy-boto3-iot
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
- Install `boto3-stubs[iot]` in your environment:

```bash
python -m pip install 'boto3-stubs[iot]'
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

Install `boto3-stubs[iot]` in your environment:

```bash
python -m pip install 'boto3-stubs[iot]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `boto3-stubs` with services you use in your environment:

```bash
python -m pip install 'boto3-stubs[iot]'
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

- Install `boto3-stubs[iot]` with services you use in your environment:

```bash
python -m pip install 'boto3-stubs[iot]'
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
- Install `boto3-stubs[iot]` in your environment:

```bash
python -m pip install 'boto3-stubs[iot]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `boto3-stubs[iot]` in your environment:

```bash
python -m pip install 'boto3-stubs[iot]'
```

Optionally, you can install `boto3-stubs` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`mypy-boto3-iot` dependency in production. However, there is an issue in
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

`IoTClient` provides annotations for `boto3.client("iot")`.

```python
from boto3.session import Session

from mypy_boto3_iot import IoTClient

client: IoTClient = Session().client("iot")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`mypy_boto3_iot.paginator` module contains type annotations for all paginators.

```python
from boto3.session import Session

from mypy_boto3_iot import IoTClient
from mypy_boto3_iot.paginator import (
    GetBehaviorModelTrainingSummariesPaginator,
    ListActiveViolationsPaginator,
    ListAttachedPoliciesPaginator,
    ListAuditFindingsPaginator,
    ListAuditMitigationActionsExecutionsPaginator,
    ListAuditMitigationActionsTasksPaginator,
    ListAuditSuppressionsPaginator,
    ListAuditTasksPaginator,
    ListAuthorizersPaginator,
    ListBillingGroupsPaginator,
    ListCACertificatesPaginator,
    ListCertificatesByCAPaginator,
    ListCertificatesPaginator,
    ListCommandExecutionsPaginator,
    ListCommandsPaginator,
    ListCustomMetricsPaginator,
    ListDetectMitigationActionsExecutionsPaginator,
    ListDetectMitigationActionsTasksPaginator,
    ListDimensionsPaginator,
    ListDomainConfigurationsPaginator,
    ListFleetMetricsPaginator,
    ListIndicesPaginator,
    ListJobExecutionsForJobPaginator,
    ListJobExecutionsForThingPaginator,
    ListJobTemplatesPaginator,
    ListJobsPaginator,
    ListManagedJobTemplatesPaginator,
    ListMetricValuesPaginator,
    ListMitigationActionsPaginator,
    ListOTAUpdatesPaginator,
    ListOutgoingCertificatesPaginator,
    ListPackageVersionsPaginator,
    ListPackagesPaginator,
    ListPoliciesPaginator,
    ListPolicyPrincipalsPaginator,
    ListPrincipalPoliciesPaginator,
    ListPrincipalThingsPaginator,
    ListPrincipalThingsV2Paginator,
    ListProvisioningTemplateVersionsPaginator,
    ListProvisioningTemplatesPaginator,
    ListRelatedResourcesForAuditFindingPaginator,
    ListRoleAliasesPaginator,
    ListSbomValidationResultsPaginator,
    ListScheduledAuditsPaginator,
    ListSecurityProfilesForTargetPaginator,
    ListSecurityProfilesPaginator,
    ListStreamsPaginator,
    ListTagsForResourcePaginator,
    ListTargetsForPolicyPaginator,
    ListTargetsForSecurityProfilePaginator,
    ListThingGroupsForThingPaginator,
    ListThingGroupsPaginator,
    ListThingPrincipalsPaginator,
    ListThingPrincipalsV2Paginator,
    ListThingRegistrationTaskReportsPaginator,
    ListThingRegistrationTasksPaginator,
    ListThingTypesPaginator,
    ListThingsInBillingGroupPaginator,
    ListThingsInThingGroupPaginator,
    ListThingsPaginator,
    ListTopicRuleDestinationsPaginator,
    ListTopicRulesPaginator,
    ListV2LoggingLevelsPaginator,
    ListViolationEventsPaginator,
)

client: IoTClient = Session().client("iot")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
get_behavior_model_training_summaries_paginator: GetBehaviorModelTrainingSummariesPaginator = (
    client.get_paginator("get_behavior_model_training_summaries")
)
list_active_violations_paginator: ListActiveViolationsPaginator = client.get_paginator(
    "list_active_violations"
)
list_attached_policies_paginator: ListAttachedPoliciesPaginator = client.get_paginator(
    "list_attached_policies"
)
list_audit_findings_paginator: ListAuditFindingsPaginator = client.get_paginator(
    "list_audit_findings"
)
list_audit_mitigation_actions_executions_paginator: ListAuditMitigationActionsExecutionsPaginator = client.get_paginator(
    "list_audit_mitigation_actions_executions"
)
list_audit_mitigation_actions_tasks_paginator: ListAuditMitigationActionsTasksPaginator = (
    client.get_paginator("list_audit_mitigation_actions_tasks")
)
list_audit_suppressions_paginator: ListAuditSuppressionsPaginator = client.get_paginator(
    "list_audit_suppressions"
)
list_audit_tasks_paginator: ListAuditTasksPaginator = client.get_paginator("list_audit_tasks")
list_authorizers_paginator: ListAuthorizersPaginator = client.get_paginator("list_authorizers")
list_billing_groups_paginator: ListBillingGroupsPaginator = client.get_paginator(
    "list_billing_groups"
)
list_ca_certificates_paginator: ListCACertificatesPaginator = client.get_paginator(
    "list_ca_certificates"
)
list_certificates_by_ca_paginator: ListCertificatesByCAPaginator = client.get_paginator(
    "list_certificates_by_ca"
)
list_certificates_paginator: ListCertificatesPaginator = client.get_paginator("list_certificates")
list_command_executions_paginator: ListCommandExecutionsPaginator = client.get_paginator(
    "list_command_executions"
)
list_commands_paginator: ListCommandsPaginator = client.get_paginator("list_commands")
list_custom_metrics_paginator: ListCustomMetricsPaginator = client.get_paginator(
    "list_custom_metrics"
)
list_detect_mitigation_actions_executions_paginator: ListDetectMitigationActionsExecutionsPaginator = client.get_paginator(
    "list_detect_mitigation_actions_executions"
)
list_detect_mitigation_actions_tasks_paginator: ListDetectMitigationActionsTasksPaginator = (
    client.get_paginator("list_detect_mitigation_actions_tasks")
)
list_dimensions_paginator: ListDimensionsPaginator = client.get_paginator("list_dimensions")
list_domain_configurations_paginator: ListDomainConfigurationsPaginator = client.get_paginator(
    "list_domain_configurations"
)
list_fleet_metrics_paginator: ListFleetMetricsPaginator = client.get_paginator("list_fleet_metrics")
list_indices_paginator: ListIndicesPaginator = client.get_paginator("list_indices")
list_job_executions_for_job_paginator: ListJobExecutionsForJobPaginator = client.get_paginator(
    "list_job_executions_for_job"
)
list_job_executions_for_thing_paginator: ListJobExecutionsForThingPaginator = client.get_paginator(
    "list_job_executions_for_thing"
)
list_job_templates_paginator: ListJobTemplatesPaginator = client.get_paginator("list_job_templates")
list_jobs_paginator: ListJobsPaginator = client.get_paginator("list_jobs")
list_managed_job_templates_paginator: ListManagedJobTemplatesPaginator = client.get_paginator(
    "list_managed_job_templates"
)
list_metric_values_paginator: ListMetricValuesPaginator = client.get_paginator("list_metric_values")
list_mitigation_actions_paginator: ListMitigationActionsPaginator = client.get_paginator(
    "list_mitigation_actions"
)
list_ota_updates_paginator: ListOTAUpdatesPaginator = client.get_paginator("list_ota_updates")
list_outgoing_certificates_paginator: ListOutgoingCertificatesPaginator = client.get_paginator(
    "list_outgoing_certificates"
)
list_package_versions_paginator: ListPackageVersionsPaginator = client.get_paginator(
    "list_package_versions"
)
list_packages_paginator: ListPackagesPaginator = client.get_paginator("list_packages")
list_policies_paginator: ListPoliciesPaginator = client.get_paginator("list_policies")
list_policy_principals_paginator: ListPolicyPrincipalsPaginator = client.get_paginator(
    "list_policy_principals"
)
list_principal_policies_paginator: ListPrincipalPoliciesPaginator = client.get_paginator(
    "list_principal_policies"
)
list_principal_things_paginator: ListPrincipalThingsPaginator = client.get_paginator(
    "list_principal_things"
)
list_principal_things_v2_paginator: ListPrincipalThingsV2Paginator = client.get_paginator(
    "list_principal_things_v2"
)
list_provisioning_template_versions_paginator: ListProvisioningTemplateVersionsPaginator = (
    client.get_paginator("list_provisioning_template_versions")
)
list_provisioning_templates_paginator: ListProvisioningTemplatesPaginator = client.get_paginator(
    "list_provisioning_templates"
)
list_related_resources_for_audit_finding_paginator: ListRelatedResourcesForAuditFindingPaginator = (
    client.get_paginator("list_related_resources_for_audit_finding")
)
list_role_aliases_paginator: ListRoleAliasesPaginator = client.get_paginator("list_role_aliases")
list_sbom_validation_results_paginator: ListSbomValidationResultsPaginator = client.get_paginator(
    "list_sbom_validation_results"
)
list_scheduled_audits_paginator: ListScheduledAuditsPaginator = client.get_paginator(
    "list_scheduled_audits"
)
list_security_profiles_for_target_paginator: ListSecurityProfilesForTargetPaginator = (
    client.get_paginator("list_security_profiles_for_target")
)
list_security_profiles_paginator: ListSecurityProfilesPaginator = client.get_paginator(
    "list_security_profiles"
)
list_streams_paginator: ListStreamsPaginator = client.get_paginator("list_streams")
list_tags_for_resource_paginator: ListTagsForResourcePaginator = client.get_paginator(
    "list_tags_for_resource"
)
list_targets_for_policy_paginator: ListTargetsForPolicyPaginator = client.get_paginator(
    "list_targets_for_policy"
)
list_targets_for_security_profile_paginator: ListTargetsForSecurityProfilePaginator = (
    client.get_paginator("list_targets_for_security_profile")
)
list_thing_groups_for_thing_paginator: ListThingGroupsForThingPaginator = client.get_paginator(
    "list_thing_groups_for_thing"
)
list_thing_groups_paginator: ListThingGroupsPaginator = client.get_paginator("list_thing_groups")
list_thing_principals_paginator: ListThingPrincipalsPaginator = client.get_paginator(
    "list_thing_principals"
)
list_thing_principals_v2_paginator: ListThingPrincipalsV2Paginator = client.get_paginator(
    "list_thing_principals_v2"
)
list_thing_registration_task_reports_paginator: ListThingRegistrationTaskReportsPaginator = (
    client.get_paginator("list_thing_registration_task_reports")
)
list_thing_registration_tasks_paginator: ListThingRegistrationTasksPaginator = client.get_paginator(
    "list_thing_registration_tasks"
)
list_thing_types_paginator: ListThingTypesPaginator = client.get_paginator("list_thing_types")
list_things_in_billing_group_paginator: ListThingsInBillingGroupPaginator = client.get_paginator(
    "list_things_in_billing_group"
)
list_things_in_thing_group_paginator: ListThingsInThingGroupPaginator = client.get_paginator(
    "list_things_in_thing_group"
)
list_things_paginator: ListThingsPaginator = client.get_paginator("list_things")
list_topic_rule_destinations_paginator: ListTopicRuleDestinationsPaginator = client.get_paginator(
    "list_topic_rule_destinations"
)
list_topic_rules_paginator: ListTopicRulesPaginator = client.get_paginator("list_topic_rules")
list_v2_logging_levels_paginator: ListV2LoggingLevelsPaginator = client.get_paginator(
    "list_v2_logging_levels"
)
list_violation_events_paginator: ListViolationEventsPaginator = client.get_paginator(
    "list_violation_events"
)
```

<a id="literals"></a>

### Literals

`mypy_boto3_iot.literals` module contains literals extracted from shapes that
can be used in user code for type checking.

Full list of `IoT` Literals can be found in
[docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot/literals/).

```python
from mypy_boto3_iot.literals import AbortActionType


def check_value(value: AbortActionType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`mypy_boto3_iot.type_defs` module contains structures and shapes assembled to
typed dictionaries and unions for additional type checking.

Full list of `IoT` TypeDefs can be found in
[docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot/type_defs/).

```python
# TypedDict usage example
from mypy_boto3_iot.type_defs import AbortCriteriaTypeDef


def get_value() -> AbortCriteriaTypeDef:
    return {
        "failureType": ...,
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

`mypy-boto3-iot` version is the same as related `boto3` version and follows
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
[boto3 docs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
