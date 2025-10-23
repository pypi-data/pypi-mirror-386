<a id="boto3-stubs-lite"></a>

# boto3-stubs-lite

[![PyPI - boto3-stubs-lite](https://img.shields.io/pypi/v/boto3-stubs-lite.svg?color=blue)](https://pypi.org/project/boto3-stubs-lite/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/boto3-stubs-lite.svg?color=blue)](https://pypi.org/project/boto3-stubs-lite/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/boto3_stubs_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/boto3-stubs-lite)](https://pypistats.org/packages/boto3-stubs-lite)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 1.40.57](https://pypi.org/project/boto3/)
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
[boto3-stubs-lite docs](https://youtype.github.io/boto3_stubs_docs/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [boto3-stubs-lite](#boto3-stubs-lite)
  - [How to install](#how-to-install)
    - [Generate locally (recommended)](<#generate-locally-(recommended)>)
    - [VSCode extension](#vscode-extension)
    - [From PyPI with pip](#from-pypi-with-pip)
    - [From conda-forge](#from-conda-forge)
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
  - [How it works](#how-it-works)
  - [What's new](#what's-new)
    - [Implemented features](#implemented-features)
    - [Latest changes](#latest-changes)
  - [Versioning](#versioning)
  - [Thank you](#thank-you)
  - [Documentation](#documentation)
  - [Support and contributing](#support-and-contributing)
  - [Submodules](#submodules)

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
3. Select services you use in the current project.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Auto-discover services` and select services you use in the current
project.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `boto3-stubs` to add type checking for `boto3` package.

```bash
# install type annotations only for boto3
python -m pip install boto3-stubs

# install boto3 type annotations
# for cloudformation, dynamodb, ec2, lambda, rds, s3, sqs
python -m pip install 'boto3-stubs[essential]'

# or install annotations for services you use
python -m pip install 'boto3-stubs[acm,apigateway]'

# or install annotations in sync with boto3 version
python -m pip install 'boto3-stubs[boto3]'

# or install all-in-one annotations for all services
python -m pip install 'boto3-stubs[full]'
```

<a id="from-conda-forge"></a>

### From conda-forge

Add `conda-forge` to your channels with:

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```

Once the `conda-forge` channel has been enabled, `boto3-stubs` and
`boto3-stubs-essential` can be installed with:

```bash
conda install boto3-stubs boto3-stubs-essential
```

List all available versions of `boto3-stubs-lite` available on your platform
with:

```bash
conda search boto3-stubs --channel conda-forge
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
# uninstall boto3-stubs-lite
python -m pip uninstall -y boto3-stubs-lite
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
- Install `boto3-stubs-lite[essential]` in your environment:

```bash
python -m pip install 'boto3-stubs-lite[essential]'
```

Both type checking and code completion should now work. No explicit type
annotations required, write your `boto3` code as usual.

<a id="pycharm"></a>

### PyCharm

Install `boto3-stubs-lite[essential]` in your environment:

```bash
python -m pip install 'boto3-stubs-lite[essential]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `boto3-stubs-lite` with services you use in your environment:

```bash
python -m pip install 'boto3-stubs-lite[essential]'
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

- Make sure emacs uses the environment where you have installed
  `boto3-stubs-lite`

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="sublime-text"></a>

### Sublime Text

- Install `boto3-stubs-lite[essential]` with services you use in your
  environment:

```bash
python -m pip install 'boto3-stubs-lite[essential]'
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
- Install `boto3-stubs-lite[essential]` in your environment:

```bash
python -m pip install 'boto3-stubs-lite[essential]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `boto3-stubs-lite[essential]` in your environment:

```bash
python -m pip install 'boto3-stubs-lite[essential]'
```

Optionally, you can install `boto3-stubs-lite` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`boto3-stubs-lite` dependency in production. However, there is an issue in
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

### Explicit type annotations

To speed up type checking and code completion, you can set types explicitly.

```python
import boto3
from boto3.session import Session

from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_ec2.service_resource import EC2ServiceResource
from mypy_boto3_ec2.waiter import BundleTaskCompleteWaiter
from mypy_boto3_ec2.paginator import DescribeVolumesPaginator

session = Session(region_name="us-west-1")

ec2_client: EC2Client = boto3.client("ec2", region_name="us-west-1")
ec2_resource: EC2ServiceResource = session.resource("ec2")

bundle_task_complete_waiter: BundleTaskCompleteWaiter = ec2_client.get_waiter(
    "bundle_task_complete"
)
describe_volumes_paginator: DescribeVolumesPaginator = ec2_client.get_paginator("describe_volumes")
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

`boto3-stubs-lite` version is the same as related `boto3` version and follows
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
[boto3 docs](https://youtype.github.io/boto3_stubs_docs/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.

<a id="submodules"></a>

## Submodules

- `boto3-stubs-lite[full]` - Type annotations for all 413 services in one
  package (recommended).
- `boto3-stubs-lite[all]` - Type annotations for all 413 services in separate
  packages.
- `boto3-stubs-lite[essential]` - Type annotations for
  [CloudFormation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudformation/),
  [DynamoDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dynamodb/),
  [EC2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ec2/),
  [Lambda](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lambda/),
  [RDS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rds/),
  [S3](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3/) and
  [SQS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sqs/) services.
- `boto3-stubs-lite[boto3]` - Install annotations in sync with `boto3` version.
- `boto3-stubs-lite[accessanalyzer]` - Type annotations for
  [AccessAnalyzer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_accessanalyzer/)
  service.
- `boto3-stubs-lite[account]` - Type annotations for
  [Account](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_account/)
  service.
- `boto3-stubs-lite[acm]` - Type annotations for
  [ACM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_acm/) service.
- `boto3-stubs-lite[acm-pca]` - Type annotations for
  [ACMPCA](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_acm_pca/)
  service.
- `boto3-stubs-lite[aiops]` - Type annotations for
  [AIOps](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_aiops/)
  service.
- `boto3-stubs-lite[amp]` - Type annotations for
  [PrometheusService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_amp/)
  service.
- `boto3-stubs-lite[amplify]` - Type annotations for
  [Amplify](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_amplify/)
  service.
- `boto3-stubs-lite[amplifybackend]` - Type annotations for
  [AmplifyBackend](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_amplifybackend/)
  service.
- `boto3-stubs-lite[amplifyuibuilder]` - Type annotations for
  [AmplifyUIBuilder](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_amplifyuibuilder/)
  service.
- `boto3-stubs-lite[apigateway]` - Type annotations for
  [APIGateway](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_apigateway/)
  service.
- `boto3-stubs-lite[apigatewaymanagementapi]` - Type annotations for
  [ApiGatewayManagementApi](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_apigatewaymanagementapi/)
  service.
- `boto3-stubs-lite[apigatewayv2]` - Type annotations for
  [ApiGatewayV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_apigatewayv2/)
  service.
- `boto3-stubs-lite[appconfig]` - Type annotations for
  [AppConfig](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appconfig/)
  service.
- `boto3-stubs-lite[appconfigdata]` - Type annotations for
  [AppConfigData](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appconfigdata/)
  service.
- `boto3-stubs-lite[appfabric]` - Type annotations for
  [AppFabric](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appfabric/)
  service.
- `boto3-stubs-lite[appflow]` - Type annotations for
  [Appflow](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appflow/)
  service.
- `boto3-stubs-lite[appintegrations]` - Type annotations for
  [AppIntegrationsService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appintegrations/)
  service.
- `boto3-stubs-lite[application-autoscaling]` - Type annotations for
  [ApplicationAutoScaling](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_application_autoscaling/)
  service.
- `boto3-stubs-lite[application-insights]` - Type annotations for
  [ApplicationInsights](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_application_insights/)
  service.
- `boto3-stubs-lite[application-signals]` - Type annotations for
  [CloudWatchApplicationSignals](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_application_signals/)
  service.
- `boto3-stubs-lite[applicationcostprofiler]` - Type annotations for
  [ApplicationCostProfiler](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_applicationcostprofiler/)
  service.
- `boto3-stubs-lite[appmesh]` - Type annotations for
  [AppMesh](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appmesh/)
  service.
- `boto3-stubs-lite[apprunner]` - Type annotations for
  [AppRunner](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_apprunner/)
  service.
- `boto3-stubs-lite[appstream]` - Type annotations for
  [AppStream](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appstream/)
  service.
- `boto3-stubs-lite[appsync]` - Type annotations for
  [AppSync](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_appsync/)
  service.
- `boto3-stubs-lite[apptest]` - Type annotations for
  [MainframeModernizationApplicationTesting](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_apptest/)
  service.
- `boto3-stubs-lite[arc-region-switch]` - Type annotations for
  [ARCRegionswitch](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_arc_region_switch/)
  service.
- `boto3-stubs-lite[arc-zonal-shift]` - Type annotations for
  [ARCZonalShift](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_arc_zonal_shift/)
  service.
- `boto3-stubs-lite[artifact]` - Type annotations for
  [Artifact](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_artifact/)
  service.
- `boto3-stubs-lite[athena]` - Type annotations for
  [Athena](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_athena/)
  service.
- `boto3-stubs-lite[auditmanager]` - Type annotations for
  [AuditManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_auditmanager/)
  service.
- `boto3-stubs-lite[autoscaling]` - Type annotations for
  [AutoScaling](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_autoscaling/)
  service.
- `boto3-stubs-lite[autoscaling-plans]` - Type annotations for
  [AutoScalingPlans](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_autoscaling_plans/)
  service.
- `boto3-stubs-lite[b2bi]` - Type annotations for
  [B2BI](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_b2bi/) service.
- `boto3-stubs-lite[backup]` - Type annotations for
  [Backup](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_backup/)
  service.
- `boto3-stubs-lite[backup-gateway]` - Type annotations for
  [BackupGateway](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_backup_gateway/)
  service.
- `boto3-stubs-lite[backupsearch]` - Type annotations for
  [BackupSearch](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_backupsearch/)
  service.
- `boto3-stubs-lite[batch]` - Type annotations for
  [Batch](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_batch/)
  service.
- `boto3-stubs-lite[bcm-dashboards]` - Type annotations for
  [BillingandCostManagementDashboards](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bcm_dashboards/)
  service.
- `boto3-stubs-lite[bcm-data-exports]` - Type annotations for
  [BillingandCostManagementDataExports](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bcm_data_exports/)
  service.
- `boto3-stubs-lite[bcm-pricing-calculator]` - Type annotations for
  [BillingandCostManagementPricingCalculator](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bcm_pricing_calculator/)
  service.
- `boto3-stubs-lite[bcm-recommended-actions]` - Type annotations for
  [BillingandCostManagementRecommendedActions](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bcm_recommended_actions/)
  service.
- `boto3-stubs-lite[bedrock]` - Type annotations for
  [Bedrock](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock/)
  service.
- `boto3-stubs-lite[bedrock-agent]` - Type annotations for
  [AgentsforBedrock](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_agent/)
  service.
- `boto3-stubs-lite[bedrock-agent-runtime]` - Type annotations for
  [AgentsforBedrockRuntime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_agent_runtime/)
  service.
- `boto3-stubs-lite[bedrock-agentcore]` - Type annotations for
  [BedrockAgentCoreDataPlaneFrontingLayer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_agentcore/)
  service.
- `boto3-stubs-lite[bedrock-agentcore-control]` - Type annotations for
  [BedrockAgentCoreControlPlaneFrontingLayer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_agentcore_control/)
  service.
- `boto3-stubs-lite[bedrock-data-automation]` - Type annotations for
  [DataAutomationforBedrock](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_data_automation/)
  service.
- `boto3-stubs-lite[bedrock-data-automation-runtime]` - Type annotations for
  [RuntimeforBedrockDataAutomation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_data_automation_runtime/)
  service.
- `boto3-stubs-lite[bedrock-runtime]` - Type annotations for
  [BedrockRuntime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_bedrock_runtime/)
  service.
- `boto3-stubs-lite[billing]` - Type annotations for
  [Billing](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_billing/)
  service.
- `boto3-stubs-lite[billingconductor]` - Type annotations for
  [BillingConductor](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_billingconductor/)
  service.
- `boto3-stubs-lite[braket]` - Type annotations for
  [Braket](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_braket/)
  service.
- `boto3-stubs-lite[budgets]` - Type annotations for
  [Budgets](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_budgets/)
  service.
- `boto3-stubs-lite[ce]` - Type annotations for
  [CostExplorer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ce/)
  service.
- `boto3-stubs-lite[chatbot]` - Type annotations for
  [Chatbot](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chatbot/)
  service.
- `boto3-stubs-lite[chime]` - Type annotations for
  [Chime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chime/)
  service.
- `boto3-stubs-lite[chime-sdk-identity]` - Type annotations for
  [ChimeSDKIdentity](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chime_sdk_identity/)
  service.
- `boto3-stubs-lite[chime-sdk-media-pipelines]` - Type annotations for
  [ChimeSDKMediaPipelines](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chime_sdk_media_pipelines/)
  service.
- `boto3-stubs-lite[chime-sdk-meetings]` - Type annotations for
  [ChimeSDKMeetings](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chime_sdk_meetings/)
  service.
- `boto3-stubs-lite[chime-sdk-messaging]` - Type annotations for
  [ChimeSDKMessaging](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chime_sdk_messaging/)
  service.
- `boto3-stubs-lite[chime-sdk-voice]` - Type annotations for
  [ChimeSDKVoice](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_chime_sdk_voice/)
  service.
- `boto3-stubs-lite[cleanrooms]` - Type annotations for
  [CleanRoomsService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cleanrooms/)
  service.
- `boto3-stubs-lite[cleanroomsml]` - Type annotations for
  [CleanRoomsML](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cleanroomsml/)
  service.
- `boto3-stubs-lite[cloud9]` - Type annotations for
  [Cloud9](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloud9/)
  service.
- `boto3-stubs-lite[cloudcontrol]` - Type annotations for
  [CloudControlApi](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudcontrol/)
  service.
- `boto3-stubs-lite[clouddirectory]` - Type annotations for
  [CloudDirectory](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_clouddirectory/)
  service.
- `boto3-stubs-lite[cloudformation]` - Type annotations for
  [CloudFormation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudformation/)
  service.
- `boto3-stubs-lite[cloudfront]` - Type annotations for
  [CloudFront](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudfront/)
  service.
- `boto3-stubs-lite[cloudfront-keyvaluestore]` - Type annotations for
  [CloudFrontKeyValueStore](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudfront_keyvaluestore/)
  service.
- `boto3-stubs-lite[cloudhsm]` - Type annotations for
  [CloudHSM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudhsm/)
  service.
- `boto3-stubs-lite[cloudhsmv2]` - Type annotations for
  [CloudHSMV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudhsmv2/)
  service.
- `boto3-stubs-lite[cloudsearch]` - Type annotations for
  [CloudSearch](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudsearch/)
  service.
- `boto3-stubs-lite[cloudsearchdomain]` - Type annotations for
  [CloudSearchDomain](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudsearchdomain/)
  service.
- `boto3-stubs-lite[cloudtrail]` - Type annotations for
  [CloudTrail](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudtrail/)
  service.
- `boto3-stubs-lite[cloudtrail-data]` - Type annotations for
  [CloudTrailDataService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudtrail_data/)
  service.
- `boto3-stubs-lite[cloudwatch]` - Type annotations for
  [CloudWatch](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cloudwatch/)
  service.
- `boto3-stubs-lite[codeartifact]` - Type annotations for
  [CodeArtifact](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codeartifact/)
  service.
- `boto3-stubs-lite[codebuild]` - Type annotations for
  [CodeBuild](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codebuild/)
  service.
- `boto3-stubs-lite[codecatalyst]` - Type annotations for
  [CodeCatalyst](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codecatalyst/)
  service.
- `boto3-stubs-lite[codecommit]` - Type annotations for
  [CodeCommit](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codecommit/)
  service.
- `boto3-stubs-lite[codeconnections]` - Type annotations for
  [CodeConnections](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codeconnections/)
  service.
- `boto3-stubs-lite[codedeploy]` - Type annotations for
  [CodeDeploy](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codedeploy/)
  service.
- `boto3-stubs-lite[codeguru-reviewer]` - Type annotations for
  [CodeGuruReviewer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codeguru_reviewer/)
  service.
- `boto3-stubs-lite[codeguru-security]` - Type annotations for
  [CodeGuruSecurity](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codeguru_security/)
  service.
- `boto3-stubs-lite[codeguruprofiler]` - Type annotations for
  [CodeGuruProfiler](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codeguruprofiler/)
  service.
- `boto3-stubs-lite[codepipeline]` - Type annotations for
  [CodePipeline](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codepipeline/)
  service.
- `boto3-stubs-lite[codestar-connections]` - Type annotations for
  [CodeStarconnections](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codestar_connections/)
  service.
- `boto3-stubs-lite[codestar-notifications]` - Type annotations for
  [CodeStarNotifications](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_codestar_notifications/)
  service.
- `boto3-stubs-lite[cognito-identity]` - Type annotations for
  [CognitoIdentity](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cognito_identity/)
  service.
- `boto3-stubs-lite[cognito-idp]` - Type annotations for
  [CognitoIdentityProvider](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cognito_idp/)
  service.
- `boto3-stubs-lite[cognito-sync]` - Type annotations for
  [CognitoSync](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cognito_sync/)
  service.
- `boto3-stubs-lite[comprehend]` - Type annotations for
  [Comprehend](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_comprehend/)
  service.
- `boto3-stubs-lite[comprehendmedical]` - Type annotations for
  [ComprehendMedical](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_comprehendmedical/)
  service.
- `boto3-stubs-lite[compute-optimizer]` - Type annotations for
  [ComputeOptimizer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_compute_optimizer/)
  service.
- `boto3-stubs-lite[config]` - Type annotations for
  [ConfigService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_config/)
  service.
- `boto3-stubs-lite[connect]` - Type annotations for
  [Connect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_connect/)
  service.
- `boto3-stubs-lite[connect-contact-lens]` - Type annotations for
  [ConnectContactLens](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_connect_contact_lens/)
  service.
- `boto3-stubs-lite[connectcampaigns]` - Type annotations for
  [ConnectCampaignService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_connectcampaigns/)
  service.
- `boto3-stubs-lite[connectcampaignsv2]` - Type annotations for
  [ConnectCampaignServiceV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_connectcampaignsv2/)
  service.
- `boto3-stubs-lite[connectcases]` - Type annotations for
  [ConnectCases](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_connectcases/)
  service.
- `boto3-stubs-lite[connectparticipant]` - Type annotations for
  [ConnectParticipant](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_connectparticipant/)
  service.
- `boto3-stubs-lite[controlcatalog]` - Type annotations for
  [ControlCatalog](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_controlcatalog/)
  service.
- `boto3-stubs-lite[controltower]` - Type annotations for
  [ControlTower](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_controltower/)
  service.
- `boto3-stubs-lite[cost-optimization-hub]` - Type annotations for
  [CostOptimizationHub](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cost_optimization_hub/)
  service.
- `boto3-stubs-lite[cur]` - Type annotations for
  [CostandUsageReportService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_cur/)
  service.
- `boto3-stubs-lite[customer-profiles]` - Type annotations for
  [CustomerProfiles](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_customer_profiles/)
  service.
- `boto3-stubs-lite[databrew]` - Type annotations for
  [GlueDataBrew](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_databrew/)
  service.
- `boto3-stubs-lite[dataexchange]` - Type annotations for
  [DataExchange](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dataexchange/)
  service.
- `boto3-stubs-lite[datapipeline]` - Type annotations for
  [DataPipeline](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_datapipeline/)
  service.
- `boto3-stubs-lite[datasync]` - Type annotations for
  [DataSync](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_datasync/)
  service.
- `boto3-stubs-lite[datazone]` - Type annotations for
  [DataZone](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_datazone/)
  service.
- `boto3-stubs-lite[dax]` - Type annotations for
  [DAX](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dax/) service.
- `boto3-stubs-lite[deadline]` - Type annotations for
  [DeadlineCloud](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_deadline/)
  service.
- `boto3-stubs-lite[detective]` - Type annotations for
  [Detective](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_detective/)
  service.
- `boto3-stubs-lite[devicefarm]` - Type annotations for
  [DeviceFarm](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_devicefarm/)
  service.
- `boto3-stubs-lite[devops-guru]` - Type annotations for
  [DevOpsGuru](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_devops_guru/)
  service.
- `boto3-stubs-lite[directconnect]` - Type annotations for
  [DirectConnect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_directconnect/)
  service.
- `boto3-stubs-lite[discovery]` - Type annotations for
  [ApplicationDiscoveryService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_discovery/)
  service.
- `boto3-stubs-lite[dlm]` - Type annotations for
  [DLM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dlm/) service.
- `boto3-stubs-lite[dms]` - Type annotations for
  [DatabaseMigrationService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dms/)
  service.
- `boto3-stubs-lite[docdb]` - Type annotations for
  [DocDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_docdb/)
  service.
- `boto3-stubs-lite[docdb-elastic]` - Type annotations for
  [DocDBElastic](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_docdb_elastic/)
  service.
- `boto3-stubs-lite[drs]` - Type annotations for
  [Drs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_drs/) service.
- `boto3-stubs-lite[ds]` - Type annotations for
  [DirectoryService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ds/)
  service.
- `boto3-stubs-lite[ds-data]` - Type annotations for
  [DirectoryServiceData](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ds_data/)
  service.
- `boto3-stubs-lite[dsql]` - Type annotations for
  [AuroraDSQL](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dsql/)
  service.
- `boto3-stubs-lite[dynamodb]` - Type annotations for
  [DynamoDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dynamodb/)
  service.
- `boto3-stubs-lite[dynamodbstreams]` - Type annotations for
  [DynamoDBStreams](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dynamodbstreams/)
  service.
- `boto3-stubs-lite[ebs]` - Type annotations for
  [EBS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ebs/) service.
- `boto3-stubs-lite[ec2]` - Type annotations for
  [EC2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ec2/) service.
- `boto3-stubs-lite[ec2-instance-connect]` - Type annotations for
  [EC2InstanceConnect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ec2_instance_connect/)
  service.
- `boto3-stubs-lite[ecr]` - Type annotations for
  [ECR](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ecr/) service.
- `boto3-stubs-lite[ecr-public]` - Type annotations for
  [ECRPublic](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ecr_public/)
  service.
- `boto3-stubs-lite[ecs]` - Type annotations for
  [ECS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ecs/) service.
- `boto3-stubs-lite[efs]` - Type annotations for
  [EFS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_efs/) service.
- `boto3-stubs-lite[eks]` - Type annotations for
  [EKS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_eks/) service.
- `boto3-stubs-lite[eks-auth]` - Type annotations for
  [EKSAuth](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_eks_auth/)
  service.
- `boto3-stubs-lite[elasticache]` - Type annotations for
  [ElastiCache](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_elasticache/)
  service.
- `boto3-stubs-lite[elasticbeanstalk]` - Type annotations for
  [ElasticBeanstalk](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_elasticbeanstalk/)
  service.
- `boto3-stubs-lite[elastictranscoder]` - Type annotations for
  [ElasticTranscoder](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_elastictranscoder/)
  service.
- `boto3-stubs-lite[elb]` - Type annotations for
  [ElasticLoadBalancing](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_elb/)
  service.
- `boto3-stubs-lite[elbv2]` - Type annotations for
  [ElasticLoadBalancingv2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_elbv2/)
  service.
- `boto3-stubs-lite[emr]` - Type annotations for
  [EMR](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_emr/) service.
- `boto3-stubs-lite[emr-containers]` - Type annotations for
  [EMRContainers](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_emr_containers/)
  service.
- `boto3-stubs-lite[emr-serverless]` - Type annotations for
  [EMRServerless](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_emr_serverless/)
  service.
- `boto3-stubs-lite[entityresolution]` - Type annotations for
  [EntityResolution](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_entityresolution/)
  service.
- `boto3-stubs-lite[es]` - Type annotations for
  [ElasticsearchService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_es/)
  service.
- `boto3-stubs-lite[events]` - Type annotations for
  [EventBridge](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_events/)
  service.
- `boto3-stubs-lite[evidently]` - Type annotations for
  [CloudWatchEvidently](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_evidently/)
  service.
- `boto3-stubs-lite[evs]` - Type annotations for
  [EVS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_evs/) service.
- `boto3-stubs-lite[finspace]` - Type annotations for
  [Finspace](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_finspace/)
  service.
- `boto3-stubs-lite[finspace-data]` - Type annotations for
  [FinSpaceData](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_finspace_data/)
  service.
- `boto3-stubs-lite[firehose]` - Type annotations for
  [Firehose](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_firehose/)
  service.
- `boto3-stubs-lite[fis]` - Type annotations for
  [FIS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_fis/) service.
- `boto3-stubs-lite[fms]` - Type annotations for
  [FMS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_fms/) service.
- `boto3-stubs-lite[forecast]` - Type annotations for
  [ForecastService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_forecast/)
  service.
- `boto3-stubs-lite[forecastquery]` - Type annotations for
  [ForecastQueryService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_forecastquery/)
  service.
- `boto3-stubs-lite[frauddetector]` - Type annotations for
  [FraudDetector](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_frauddetector/)
  service.
- `boto3-stubs-lite[freetier]` - Type annotations for
  [FreeTier](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_freetier/)
  service.
- `boto3-stubs-lite[fsx]` - Type annotations for
  [FSx](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_fsx/) service.
- `boto3-stubs-lite[gamelift]` - Type annotations for
  [GameLift](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_gamelift/)
  service.
- `boto3-stubs-lite[gameliftstreams]` - Type annotations for
  [GameLiftStreams](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_gameliftstreams/)
  service.
- `boto3-stubs-lite[geo-maps]` - Type annotations for
  [LocationServiceMapsV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_geo_maps/)
  service.
- `boto3-stubs-lite[geo-places]` - Type annotations for
  [LocationServicePlacesV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_geo_places/)
  service.
- `boto3-stubs-lite[geo-routes]` - Type annotations for
  [LocationServiceRoutesV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_geo_routes/)
  service.
- `boto3-stubs-lite[glacier]` - Type annotations for
  [Glacier](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_glacier/)
  service.
- `boto3-stubs-lite[globalaccelerator]` - Type annotations for
  [GlobalAccelerator](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_globalaccelerator/)
  service.
- `boto3-stubs-lite[glue]` - Type annotations for
  [Glue](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_glue/) service.
- `boto3-stubs-lite[grafana]` - Type annotations for
  [ManagedGrafana](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_grafana/)
  service.
- `boto3-stubs-lite[greengrass]` - Type annotations for
  [Greengrass](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_greengrass/)
  service.
- `boto3-stubs-lite[greengrassv2]` - Type annotations for
  [GreengrassV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_greengrassv2/)
  service.
- `boto3-stubs-lite[groundstation]` - Type annotations for
  [GroundStation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_groundstation/)
  service.
- `boto3-stubs-lite[guardduty]` - Type annotations for
  [GuardDuty](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_guardduty/)
  service.
- `boto3-stubs-lite[health]` - Type annotations for
  [Health](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_health/)
  service.
- `boto3-stubs-lite[healthlake]` - Type annotations for
  [HealthLake](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_healthlake/)
  service.
- `boto3-stubs-lite[iam]` - Type annotations for
  [IAM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iam/) service.
- `boto3-stubs-lite[identitystore]` - Type annotations for
  [IdentityStore](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_identitystore/)
  service.
- `boto3-stubs-lite[imagebuilder]` - Type annotations for
  [Imagebuilder](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_imagebuilder/)
  service.
- `boto3-stubs-lite[importexport]` - Type annotations for
  [ImportExport](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_importexport/)
  service.
- `boto3-stubs-lite[inspector]` - Type annotations for
  [Inspector](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_inspector/)
  service.
- `boto3-stubs-lite[inspector-scan]` - Type annotations for
  [Inspectorscan](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_inspector_scan/)
  service.
- `boto3-stubs-lite[inspector2]` - Type annotations for
  [Inspector2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_inspector2/)
  service.
- `boto3-stubs-lite[internetmonitor]` - Type annotations for
  [CloudWatchInternetMonitor](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_internetmonitor/)
  service.
- `boto3-stubs-lite[invoicing]` - Type annotations for
  [Invoicing](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_invoicing/)
  service.
- `boto3-stubs-lite[iot]` - Type annotations for
  [IoT](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot/) service.
- `boto3-stubs-lite[iot-data]` - Type annotations for
  [IoTDataPlane](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot_data/)
  service.
- `boto3-stubs-lite[iot-jobs-data]` - Type annotations for
  [IoTJobsDataPlane](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot_jobs_data/)
  service.
- `boto3-stubs-lite[iot-managed-integrations]` - Type annotations for
  [ManagedintegrationsforIoTDeviceManagement](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iot_managed_integrations/)
  service.
- `boto3-stubs-lite[iotanalytics]` - Type annotations for
  [IoTAnalytics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotanalytics/)
  service.
- `boto3-stubs-lite[iotdeviceadvisor]` - Type annotations for
  [IoTDeviceAdvisor](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotdeviceadvisor/)
  service.
- `boto3-stubs-lite[iotevents]` - Type annotations for
  [IoTEvents](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotevents/)
  service.
- `boto3-stubs-lite[iotevents-data]` - Type annotations for
  [IoTEventsData](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotevents_data/)
  service.
- `boto3-stubs-lite[iotfleethub]` - Type annotations for
  [IoTFleetHub](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotfleethub/)
  service.
- `boto3-stubs-lite[iotfleetwise]` - Type annotations for
  [IoTFleetWise](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotfleetwise/)
  service.
- `boto3-stubs-lite[iotsecuretunneling]` - Type annotations for
  [IoTSecureTunneling](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotsecuretunneling/)
  service.
- `boto3-stubs-lite[iotsitewise]` - Type annotations for
  [IoTSiteWise](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotsitewise/)
  service.
- `boto3-stubs-lite[iotthingsgraph]` - Type annotations for
  [IoTThingsGraph](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotthingsgraph/)
  service.
- `boto3-stubs-lite[iottwinmaker]` - Type annotations for
  [IoTTwinMaker](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iottwinmaker/)
  service.
- `boto3-stubs-lite[iotwireless]` - Type annotations for
  [IoTWireless](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_iotwireless/)
  service.
- `boto3-stubs-lite[ivs]` - Type annotations for
  [IVS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ivs/) service.
- `boto3-stubs-lite[ivs-realtime]` - Type annotations for
  [Ivsrealtime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ivs_realtime/)
  service.
- `boto3-stubs-lite[ivschat]` - Type annotations for
  [Ivschat](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ivschat/)
  service.
- `boto3-stubs-lite[kafka]` - Type annotations for
  [Kafka](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kafka/)
  service.
- `boto3-stubs-lite[kafkaconnect]` - Type annotations for
  [KafkaConnect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kafkaconnect/)
  service.
- `boto3-stubs-lite[kendra]` - Type annotations for
  [Kendra](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kendra/)
  service.
- `boto3-stubs-lite[kendra-ranking]` - Type annotations for
  [KendraRanking](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kendra_ranking/)
  service.
- `boto3-stubs-lite[keyspaces]` - Type annotations for
  [Keyspaces](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_keyspaces/)
  service.
- `boto3-stubs-lite[keyspacesstreams]` - Type annotations for
  [KeyspacesStreams](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_keyspacesstreams/)
  service.
- `boto3-stubs-lite[kinesis]` - Type annotations for
  [Kinesis](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesis/)
  service.
- `boto3-stubs-lite[kinesis-video-archived-media]` - Type annotations for
  [KinesisVideoArchivedMedia](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesis_video_archived_media/)
  service.
- `boto3-stubs-lite[kinesis-video-media]` - Type annotations for
  [KinesisVideoMedia](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesis_video_media/)
  service.
- `boto3-stubs-lite[kinesis-video-signaling]` - Type annotations for
  [KinesisVideoSignalingChannels](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesis_video_signaling/)
  service.
- `boto3-stubs-lite[kinesis-video-webrtc-storage]` - Type annotations for
  [KinesisVideoWebRTCStorage](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesis_video_webrtc_storage/)
  service.
- `boto3-stubs-lite[kinesisanalytics]` - Type annotations for
  [KinesisAnalytics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesisanalytics/)
  service.
- `boto3-stubs-lite[kinesisanalyticsv2]` - Type annotations for
  [KinesisAnalyticsV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesisanalyticsv2/)
  service.
- `boto3-stubs-lite[kinesisvideo]` - Type annotations for
  [KinesisVideo](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kinesisvideo/)
  service.
- `boto3-stubs-lite[kms]` - Type annotations for
  [KMS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_kms/) service.
- `boto3-stubs-lite[lakeformation]` - Type annotations for
  [LakeFormation](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lakeformation/)
  service.
- `boto3-stubs-lite[lambda]` - Type annotations for
  [Lambda](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lambda/)
  service.
- `boto3-stubs-lite[launch-wizard]` - Type annotations for
  [LaunchWizard](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_launch_wizard/)
  service.
- `boto3-stubs-lite[lex-models]` - Type annotations for
  [LexModelBuildingService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lex_models/)
  service.
- `boto3-stubs-lite[lex-runtime]` - Type annotations for
  [LexRuntimeService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lex_runtime/)
  service.
- `boto3-stubs-lite[lexv2-models]` - Type annotations for
  [LexModelsV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lexv2_models/)
  service.
- `boto3-stubs-lite[lexv2-runtime]` - Type annotations for
  [LexRuntimeV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lexv2_runtime/)
  service.
- `boto3-stubs-lite[license-manager]` - Type annotations for
  [LicenseManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_license_manager/)
  service.
- `boto3-stubs-lite[license-manager-linux-subscriptions]` - Type annotations
  for
  [LicenseManagerLinuxSubscriptions](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_license_manager_linux_subscriptions/)
  service.
- `boto3-stubs-lite[license-manager-user-subscriptions]` - Type annotations for
  [LicenseManagerUserSubscriptions](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_license_manager_user_subscriptions/)
  service.
- `boto3-stubs-lite[lightsail]` - Type annotations for
  [Lightsail](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lightsail/)
  service.
- `boto3-stubs-lite[location]` - Type annotations for
  [LocationService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_location/)
  service.
- `boto3-stubs-lite[logs]` - Type annotations for
  [CloudWatchLogs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_logs/)
  service.
- `boto3-stubs-lite[lookoutequipment]` - Type annotations for
  [LookoutEquipment](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lookoutequipment/)
  service.
- `boto3-stubs-lite[lookoutmetrics]` - Type annotations for
  [LookoutMetrics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lookoutmetrics/)
  service.
- `boto3-stubs-lite[lookoutvision]` - Type annotations for
  [LookoutforVision](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_lookoutvision/)
  service.
- `boto3-stubs-lite[m2]` - Type annotations for
  [MainframeModernization](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_m2/)
  service.
- `boto3-stubs-lite[machinelearning]` - Type annotations for
  [MachineLearning](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_machinelearning/)
  service.
- `boto3-stubs-lite[macie2]` - Type annotations for
  [Macie2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_macie2/)
  service.
- `boto3-stubs-lite[mailmanager]` - Type annotations for
  [MailManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mailmanager/)
  service.
- `boto3-stubs-lite[managedblockchain]` - Type annotations for
  [ManagedBlockchain](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_managedblockchain/)
  service.
- `boto3-stubs-lite[managedblockchain-query]` - Type annotations for
  [ManagedBlockchainQuery](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_managedblockchain_query/)
  service.
- `boto3-stubs-lite[marketplace-agreement]` - Type annotations for
  [AgreementService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_marketplace_agreement/)
  service.
- `boto3-stubs-lite[marketplace-catalog]` - Type annotations for
  [MarketplaceCatalog](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_marketplace_catalog/)
  service.
- `boto3-stubs-lite[marketplace-deployment]` - Type annotations for
  [MarketplaceDeploymentService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_marketplace_deployment/)
  service.
- `boto3-stubs-lite[marketplace-entitlement]` - Type annotations for
  [MarketplaceEntitlementService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_marketplace_entitlement/)
  service.
- `boto3-stubs-lite[marketplace-reporting]` - Type annotations for
  [MarketplaceReportingService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_marketplace_reporting/)
  service.
- `boto3-stubs-lite[marketplacecommerceanalytics]` - Type annotations for
  [MarketplaceCommerceAnalytics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_marketplacecommerceanalytics/)
  service.
- `boto3-stubs-lite[mediaconnect]` - Type annotations for
  [MediaConnect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediaconnect/)
  service.
- `boto3-stubs-lite[mediaconvert]` - Type annotations for
  [MediaConvert](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediaconvert/)
  service.
- `boto3-stubs-lite[medialive]` - Type annotations for
  [MediaLive](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_medialive/)
  service.
- `boto3-stubs-lite[mediapackage]` - Type annotations for
  [MediaPackage](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediapackage/)
  service.
- `boto3-stubs-lite[mediapackage-vod]` - Type annotations for
  [MediaPackageVod](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediapackage_vod/)
  service.
- `boto3-stubs-lite[mediapackagev2]` - Type annotations for
  [Mediapackagev2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediapackagev2/)
  service.
- `boto3-stubs-lite[mediastore]` - Type annotations for
  [MediaStore](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediastore/)
  service.
- `boto3-stubs-lite[mediastore-data]` - Type annotations for
  [MediaStoreData](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediastore_data/)
  service.
- `boto3-stubs-lite[mediatailor]` - Type annotations for
  [MediaTailor](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mediatailor/)
  service.
- `boto3-stubs-lite[medical-imaging]` - Type annotations for
  [HealthImaging](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_medical_imaging/)
  service.
- `boto3-stubs-lite[memorydb]` - Type annotations for
  [MemoryDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_memorydb/)
  service.
- `boto3-stubs-lite[meteringmarketplace]` - Type annotations for
  [MarketplaceMetering](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_meteringmarketplace/)
  service.
- `boto3-stubs-lite[mgh]` - Type annotations for
  [MigrationHub](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mgh/)
  service.
- `boto3-stubs-lite[mgn]` - Type annotations for
  [Mgn](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mgn/) service.
- `boto3-stubs-lite[migration-hub-refactor-spaces]` - Type annotations for
  [MigrationHubRefactorSpaces](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_migration_hub_refactor_spaces/)
  service.
- `boto3-stubs-lite[migrationhub-config]` - Type annotations for
  [MigrationHubConfig](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_migrationhub_config/)
  service.
- `boto3-stubs-lite[migrationhuborchestrator]` - Type annotations for
  [MigrationHubOrchestrator](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_migrationhuborchestrator/)
  service.
- `boto3-stubs-lite[migrationhubstrategy]` - Type annotations for
  [MigrationHubStrategyRecommendations](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_migrationhubstrategy/)
  service.
- `boto3-stubs-lite[mpa]` - Type annotations for
  [MultipartyApproval](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mpa/)
  service.
- `boto3-stubs-lite[mq]` - Type annotations for
  [MQ](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mq/) service.
- `boto3-stubs-lite[mturk]` - Type annotations for
  [MTurk](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mturk/)
  service.
- `boto3-stubs-lite[mwaa]` - Type annotations for
  [MWAA](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_mwaa/) service.
- `boto3-stubs-lite[neptune]` - Type annotations for
  [Neptune](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_neptune/)
  service.
- `boto3-stubs-lite[neptune-graph]` - Type annotations for
  [NeptuneGraph](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_neptune_graph/)
  service.
- `boto3-stubs-lite[neptunedata]` - Type annotations for
  [NeptuneData](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_neptunedata/)
  service.
- `boto3-stubs-lite[network-firewall]` - Type annotations for
  [NetworkFirewall](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_network_firewall/)
  service.
- `boto3-stubs-lite[networkflowmonitor]` - Type annotations for
  [NetworkFlowMonitor](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_networkflowmonitor/)
  service.
- `boto3-stubs-lite[networkmanager]` - Type annotations for
  [NetworkManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_networkmanager/)
  service.
- `boto3-stubs-lite[networkmonitor]` - Type annotations for
  [CloudWatchNetworkMonitor](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_networkmonitor/)
  service.
- `boto3-stubs-lite[notifications]` - Type annotations for
  [UserNotifications](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_notifications/)
  service.
- `boto3-stubs-lite[notificationscontacts]` - Type annotations for
  [UserNotificationsContacts](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_notificationscontacts/)
  service.
- `boto3-stubs-lite[oam]` - Type annotations for
  [CloudWatchObservabilityAccessManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_oam/)
  service.
- `boto3-stubs-lite[observabilityadmin]` - Type annotations for
  [CloudWatchObservabilityAdminService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_observabilityadmin/)
  service.
- `boto3-stubs-lite[odb]` - Type annotations for
  [Odb](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_odb/) service.
- `boto3-stubs-lite[omics]` - Type annotations for
  [Omics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_omics/)
  service.
- `boto3-stubs-lite[opensearch]` - Type annotations for
  [OpenSearchService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_opensearch/)
  service.
- `boto3-stubs-lite[opensearchserverless]` - Type annotations for
  [OpenSearchServiceServerless](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_opensearchserverless/)
  service.
- `boto3-stubs-lite[organizations]` - Type annotations for
  [Organizations](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_organizations/)
  service.
- `boto3-stubs-lite[osis]` - Type annotations for
  [OpenSearchIngestion](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_osis/)
  service.
- `boto3-stubs-lite[outposts]` - Type annotations for
  [Outposts](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_outposts/)
  service.
- `boto3-stubs-lite[panorama]` - Type annotations for
  [Panorama](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_panorama/)
  service.
- `boto3-stubs-lite[partnercentral-selling]` - Type annotations for
  [PartnerCentralSellingAPI](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_partnercentral_selling/)
  service.
- `boto3-stubs-lite[payment-cryptography]` - Type annotations for
  [PaymentCryptographyControlPlane](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_payment_cryptography/)
  service.
- `boto3-stubs-lite[payment-cryptography-data]` - Type annotations for
  [PaymentCryptographyDataPlane](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_payment_cryptography_data/)
  service.
- `boto3-stubs-lite[pca-connector-ad]` - Type annotations for
  [PcaConnectorAd](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pca_connector_ad/)
  service.
- `boto3-stubs-lite[pca-connector-scep]` - Type annotations for
  [PrivateCAConnectorforSCEP](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pca_connector_scep/)
  service.
- `boto3-stubs-lite[pcs]` - Type annotations for
  [ParallelComputingService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pcs/)
  service.
- `boto3-stubs-lite[personalize]` - Type annotations for
  [Personalize](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_personalize/)
  service.
- `boto3-stubs-lite[personalize-events]` - Type annotations for
  [PersonalizeEvents](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_personalize_events/)
  service.
- `boto3-stubs-lite[personalize-runtime]` - Type annotations for
  [PersonalizeRuntime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_personalize_runtime/)
  service.
- `boto3-stubs-lite[pi]` - Type annotations for
  [PI](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pi/) service.
- `boto3-stubs-lite[pinpoint]` - Type annotations for
  [Pinpoint](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pinpoint/)
  service.
- `boto3-stubs-lite[pinpoint-email]` - Type annotations for
  [PinpointEmail](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pinpoint_email/)
  service.
- `boto3-stubs-lite[pinpoint-sms-voice]` - Type annotations for
  [PinpointSMSVoice](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pinpoint_sms_voice/)
  service.
- `boto3-stubs-lite[pinpoint-sms-voice-v2]` - Type annotations for
  [PinpointSMSVoiceV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pinpoint_sms_voice_v2/)
  service.
- `boto3-stubs-lite[pipes]` - Type annotations for
  [EventBridgePipes](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pipes/)
  service.
- `boto3-stubs-lite[polly]` - Type annotations for
  [Polly](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_polly/)
  service.
- `boto3-stubs-lite[pricing]` - Type annotations for
  [Pricing](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_pricing/)
  service.
- `boto3-stubs-lite[proton]` - Type annotations for
  [Proton](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_proton/)
  service.
- `boto3-stubs-lite[qapps]` - Type annotations for
  [QApps](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_qapps/)
  service.
- `boto3-stubs-lite[qbusiness]` - Type annotations for
  [QBusiness](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_qbusiness/)
  service.
- `boto3-stubs-lite[qconnect]` - Type annotations for
  [QConnect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_qconnect/)
  service.
- `boto3-stubs-lite[qldb]` - Type annotations for
  [QLDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_qldb/) service.
- `boto3-stubs-lite[qldb-session]` - Type annotations for
  [QLDBSession](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_qldb_session/)
  service.
- `boto3-stubs-lite[quicksight]` - Type annotations for
  [QuickSight](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_quicksight/)
  service.
- `boto3-stubs-lite[ram]` - Type annotations for
  [RAM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ram/) service.
- `boto3-stubs-lite[rbin]` - Type annotations for
  [RecycleBin](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rbin/)
  service.
- `boto3-stubs-lite[rds]` - Type annotations for
  [RDS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rds/) service.
- `boto3-stubs-lite[rds-data]` - Type annotations for
  [RDSDataService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rds_data/)
  service.
- `boto3-stubs-lite[redshift]` - Type annotations for
  [Redshift](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_redshift/)
  service.
- `boto3-stubs-lite[redshift-data]` - Type annotations for
  [RedshiftDataAPIService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_redshift_data/)
  service.
- `boto3-stubs-lite[redshift-serverless]` - Type annotations for
  [RedshiftServerless](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_redshift_serverless/)
  service.
- `boto3-stubs-lite[rekognition]` - Type annotations for
  [Rekognition](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rekognition/)
  service.
- `boto3-stubs-lite[repostspace]` - Type annotations for
  [RePostPrivate](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_repostspace/)
  service.
- `boto3-stubs-lite[resiliencehub]` - Type annotations for
  [ResilienceHub](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_resiliencehub/)
  service.
- `boto3-stubs-lite[resource-explorer-2]` - Type annotations for
  [ResourceExplorer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_resource_explorer_2/)
  service.
- `boto3-stubs-lite[resource-groups]` - Type annotations for
  [ResourceGroups](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_resource_groups/)
  service.
- `boto3-stubs-lite[resourcegroupstaggingapi]` - Type annotations for
  [ResourceGroupsTaggingAPI](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_resourcegroupstaggingapi/)
  service.
- `boto3-stubs-lite[robomaker]` - Type annotations for
  [RoboMaker](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_robomaker/)
  service.
- `boto3-stubs-lite[rolesanywhere]` - Type annotations for
  [IAMRolesAnywhere](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rolesanywhere/)
  service.
- `boto3-stubs-lite[route53]` - Type annotations for
  [Route53](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53/)
  service.
- `boto3-stubs-lite[route53-recovery-cluster]` - Type annotations for
  [Route53RecoveryCluster](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53_recovery_cluster/)
  service.
- `boto3-stubs-lite[route53-recovery-control-config]` - Type annotations for
  [Route53RecoveryControlConfig](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53_recovery_control_config/)
  service.
- `boto3-stubs-lite[route53-recovery-readiness]` - Type annotations for
  [Route53RecoveryReadiness](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53_recovery_readiness/)
  service.
- `boto3-stubs-lite[route53domains]` - Type annotations for
  [Route53Domains](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53domains/)
  service.
- `boto3-stubs-lite[route53profiles]` - Type annotations for
  [Route53Profiles](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53profiles/)
  service.
- `boto3-stubs-lite[route53resolver]` - Type annotations for
  [Route53Resolver](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_route53resolver/)
  service.
- `boto3-stubs-lite[rtbfabric]` - Type annotations for
  [RTBFabric](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rtbfabric/)
  service.
- `boto3-stubs-lite[rum]` - Type annotations for
  [CloudWatchRUM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_rum/)
  service.
- `boto3-stubs-lite[s3]` - Type annotations for
  [S3](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3/) service.
- `boto3-stubs-lite[s3control]` - Type annotations for
  [S3Control](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3control/)
  service.
- `boto3-stubs-lite[s3outposts]` - Type annotations for
  [S3Outposts](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3outposts/)
  service.
- `boto3-stubs-lite[s3tables]` - Type annotations for
  [S3Tables](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3tables/)
  service.
- `boto3-stubs-lite[s3vectors]` - Type annotations for
  [S3Vectors](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3vectors/)
  service.
- `boto3-stubs-lite[sagemaker]` - Type annotations for
  [SageMaker](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker/)
  service.
- `boto3-stubs-lite[sagemaker-a2i-runtime]` - Type annotations for
  [AugmentedAIRuntime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker_a2i_runtime/)
  service.
- `boto3-stubs-lite[sagemaker-edge]` - Type annotations for
  [SagemakerEdgeManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker_edge/)
  service.
- `boto3-stubs-lite[sagemaker-featurestore-runtime]` - Type annotations for
  [SageMakerFeatureStoreRuntime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker_featurestore_runtime/)
  service.
- `boto3-stubs-lite[sagemaker-geospatial]` - Type annotations for
  [SageMakergeospatialcapabilities](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker_geospatial/)
  service.
- `boto3-stubs-lite[sagemaker-metrics]` - Type annotations for
  [SageMakerMetrics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker_metrics/)
  service.
- `boto3-stubs-lite[sagemaker-runtime]` - Type annotations for
  [SageMakerRuntime](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sagemaker_runtime/)
  service.
- `boto3-stubs-lite[savingsplans]` - Type annotations for
  [SavingsPlans](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_savingsplans/)
  service.
- `boto3-stubs-lite[scheduler]` - Type annotations for
  [EventBridgeScheduler](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_scheduler/)
  service.
- `boto3-stubs-lite[schemas]` - Type annotations for
  [Schemas](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_schemas/)
  service.
- `boto3-stubs-lite[sdb]` - Type annotations for
  [SimpleDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sdb/)
  service.
- `boto3-stubs-lite[secretsmanager]` - Type annotations for
  [SecretsManager](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_secretsmanager/)
  service.
- `boto3-stubs-lite[security-ir]` - Type annotations for
  [SecurityIncidentResponse](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_security_ir/)
  service.
- `boto3-stubs-lite[securityhub]` - Type annotations for
  [SecurityHub](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_securityhub/)
  service.
- `boto3-stubs-lite[securitylake]` - Type annotations for
  [SecurityLake](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_securitylake/)
  service.
- `boto3-stubs-lite[serverlessrepo]` - Type annotations for
  [ServerlessApplicationRepository](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_serverlessrepo/)
  service.
- `boto3-stubs-lite[service-quotas]` - Type annotations for
  [ServiceQuotas](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_service_quotas/)
  service.
- `boto3-stubs-lite[servicecatalog]` - Type annotations for
  [ServiceCatalog](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_servicecatalog/)
  service.
- `boto3-stubs-lite[servicecatalog-appregistry]` - Type annotations for
  [AppRegistry](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_servicecatalog_appregistry/)
  service.
- `boto3-stubs-lite[servicediscovery]` - Type annotations for
  [ServiceDiscovery](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_servicediscovery/)
  service.
- `boto3-stubs-lite[ses]` - Type annotations for
  [SES](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ses/) service.
- `boto3-stubs-lite[sesv2]` - Type annotations for
  [SESV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sesv2/)
  service.
- `boto3-stubs-lite[shield]` - Type annotations for
  [Shield](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_shield/)
  service.
- `boto3-stubs-lite[signer]` - Type annotations for
  [Signer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_signer/)
  service.
- `boto3-stubs-lite[simspaceweaver]` - Type annotations for
  [SimSpaceWeaver](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_simspaceweaver/)
  service.
- `boto3-stubs-lite[snow-device-management]` - Type annotations for
  [SnowDeviceManagement](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_snow_device_management/)
  service.
- `boto3-stubs-lite[snowball]` - Type annotations for
  [Snowball](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_snowball/)
  service.
- `boto3-stubs-lite[sns]` - Type annotations for
  [SNS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sns/) service.
- `boto3-stubs-lite[socialmessaging]` - Type annotations for
  [EndUserMessagingSocial](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_socialmessaging/)
  service.
- `boto3-stubs-lite[sqs]` - Type annotations for
  [SQS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sqs/) service.
- `boto3-stubs-lite[ssm]` - Type annotations for
  [SSM](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ssm/) service.
- `boto3-stubs-lite[ssm-contacts]` - Type annotations for
  [SSMContacts](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ssm_contacts/)
  service.
- `boto3-stubs-lite[ssm-guiconnect]` - Type annotations for
  [SSMGUIConnect](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ssm_guiconnect/)
  service.
- `boto3-stubs-lite[ssm-incidents]` - Type annotations for
  [SSMIncidents](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ssm_incidents/)
  service.
- `boto3-stubs-lite[ssm-quicksetup]` - Type annotations for
  [SystemsManagerQuickSetup](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ssm_quicksetup/)
  service.
- `boto3-stubs-lite[ssm-sap]` - Type annotations for
  [SsmSap](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_ssm_sap/)
  service.
- `boto3-stubs-lite[sso]` - Type annotations for
  [SSO](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sso/) service.
- `boto3-stubs-lite[sso-admin]` - Type annotations for
  [SSOAdmin](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sso_admin/)
  service.
- `boto3-stubs-lite[sso-oidc]` - Type annotations for
  [SSOOIDC](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sso_oidc/)
  service.
- `boto3-stubs-lite[stepfunctions]` - Type annotations for
  [SFN](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_stepfunctions/)
  service.
- `boto3-stubs-lite[storagegateway]` - Type annotations for
  [StorageGateway](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_storagegateway/)
  service.
- `boto3-stubs-lite[sts]` - Type annotations for
  [STS](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_sts/) service.
- `boto3-stubs-lite[supplychain]` - Type annotations for
  [SupplyChain](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_supplychain/)
  service.
- `boto3-stubs-lite[support]` - Type annotations for
  [Support](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_support/)
  service.
- `boto3-stubs-lite[support-app]` - Type annotations for
  [SupportApp](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_support_app/)
  service.
- `boto3-stubs-lite[swf]` - Type annotations for
  [SWF](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_swf/) service.
- `boto3-stubs-lite[synthetics]` - Type annotations for
  [Synthetics](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_synthetics/)
  service.
- `boto3-stubs-lite[taxsettings]` - Type annotations for
  [TaxSettings](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_taxsettings/)
  service.
- `boto3-stubs-lite[textract]` - Type annotations for
  [Textract](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_textract/)
  service.
- `boto3-stubs-lite[timestream-influxdb]` - Type annotations for
  [TimestreamInfluxDB](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_timestream_influxdb/)
  service.
- `boto3-stubs-lite[timestream-query]` - Type annotations for
  [TimestreamQuery](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_timestream_query/)
  service.
- `boto3-stubs-lite[timestream-write]` - Type annotations for
  [TimestreamWrite](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_timestream_write/)
  service.
- `boto3-stubs-lite[tnb]` - Type annotations for
  [TelcoNetworkBuilder](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_tnb/)
  service.
- `boto3-stubs-lite[transcribe]` - Type annotations for
  [TranscribeService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_transcribe/)
  service.
- `boto3-stubs-lite[transfer]` - Type annotations for
  [Transfer](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_transfer/)
  service.
- `boto3-stubs-lite[translate]` - Type annotations for
  [Translate](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_translate/)
  service.
- `boto3-stubs-lite[trustedadvisor]` - Type annotations for
  [TrustedAdvisorPublicAPI](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_trustedadvisor/)
  service.
- `boto3-stubs-lite[verifiedpermissions]` - Type annotations for
  [VerifiedPermissions](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_verifiedpermissions/)
  service.
- `boto3-stubs-lite[voice-id]` - Type annotations for
  [VoiceID](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_voice_id/)
  service.
- `boto3-stubs-lite[vpc-lattice]` - Type annotations for
  [VPCLattice](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_vpc_lattice/)
  service.
- `boto3-stubs-lite[waf]` - Type annotations for
  [WAF](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf/) service.
- `boto3-stubs-lite[waf-regional]` - Type annotations for
  [WAFRegional](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_waf_regional/)
  service.
- `boto3-stubs-lite[wafv2]` - Type annotations for
  [WAFV2](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_wafv2/)
  service.
- `boto3-stubs-lite[wellarchitected]` - Type annotations for
  [WellArchitected](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_wellarchitected/)
  service.
- `boto3-stubs-lite[wisdom]` - Type annotations for
  [ConnectWisdomService](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_wisdom/)
  service.
- `boto3-stubs-lite[workdocs]` - Type annotations for
  [WorkDocs](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workdocs/)
  service.
- `boto3-stubs-lite[workmail]` - Type annotations for
  [WorkMail](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workmail/)
  service.
- `boto3-stubs-lite[workmailmessageflow]` - Type annotations for
  [WorkMailMessageFlow](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workmailmessageflow/)
  service.
- `boto3-stubs-lite[workspaces]` - Type annotations for
  [WorkSpaces](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workspaces/)
  service.
- `boto3-stubs-lite[workspaces-instances]` - Type annotations for
  [WorkspacesInstances](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workspaces_instances/)
  service.
- `boto3-stubs-lite[workspaces-thin-client]` - Type annotations for
  [WorkSpacesThinClient](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workspaces_thin_client/)
  service.
- `boto3-stubs-lite[workspaces-web]` - Type annotations for
  [WorkSpacesWeb](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_workspaces_web/)
  service.
- `boto3-stubs-lite[xray]` - Type annotations for
  [XRay](https://youtype.github.io/boto3_stubs_docs/mypy_boto3_xray/) service.
