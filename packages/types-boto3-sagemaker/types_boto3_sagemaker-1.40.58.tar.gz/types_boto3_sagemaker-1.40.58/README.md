<a id="types-boto3-sagemaker"></a>

# types-boto3-sagemaker

[![PyPI - types-boto3-sagemaker](https://img.shields.io/pypi/v/types-boto3-sagemaker.svg?color=blue)](https://pypi.org/project/types-boto3-sagemaker/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/types-boto3-sagemaker.svg?color=blue)](https://pypi.org/project/types-boto3-sagemaker/)
[![Docs](https://img.shields.io/readthedocs/boto3-stubs.svg?color=blue)](https://youtype.github.io/types_boto3_docs/)
[![PyPI - Downloads](https://static.pepy.tech/badge/types-boto3-sagemaker)](https://pypistats.org/packages/types-boto3-sagemaker)

![boto3.typed](https://github.com/youtype/mypy_boto3_builder/raw/main/logo.png)

Type annotations for [boto3 SageMaker 1.40.58](https://pypi.org/project/boto3/)
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
[types-boto3-sagemaker docs](https://youtype.github.io/types_boto3_docs/types_boto3_sagemaker/).

See how it helps you find and fix potential bugs:

![types-boto3 demo](https://github.com/youtype/mypy_boto3_builder/raw/main/demo.gif)

- [types-boto3-sagemaker](#types-boto3-sagemaker)
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
   `uvx --with 'boto3==1.40.58' mypy-boto3-builder`
2. Select `boto3` AWS SDK.
3. Add `SageMaker` service.
4. Use provided commands to install generated packages.

<a id="vscode-extension"></a>

### VSCode extension

Add
[AWS Boto3](https://marketplace.visualstudio.com/items?itemName=Boto3typed.boto3-ide)
extension to your VSCode and run `AWS boto3: Quick Start` command.

Click `Modify` and select `boto3 common` and `SageMaker`.

<a id="from-pypi-with-pip"></a>

### From PyPI with pip

Install `types-boto3` for `SageMaker` service.

```bash
# install with boto3 type annotations
python -m pip install 'types-boto3[sagemaker]'

# Lite version does not provide session.client/resource overloads
# it is more RAM-friendly, but requires explicit type annotations
python -m pip install 'types-boto3-lite[sagemaker]'

# standalone installation
python -m pip install types-boto3-sagemaker
```

<a id="how-to-uninstall"></a>

## How to uninstall

```bash
python -m pip uninstall -y types-boto3-sagemaker
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
- Install `types-boto3[sagemaker]` in your environment:

```bash
python -m pip install 'types-boto3[sagemaker]'
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

Install `types-boto3[sagemaker]` in your environment:

```bash
python -m pip install 'types-boto3[sagemaker]'
```

Both type checking and code completion should now work.

<a id="emacs"></a>

### Emacs

- Install `types-boto3` with services you use in your environment:

```bash
python -m pip install 'types-boto3[sagemaker]'
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

- Install `types-boto3[sagemaker]` with services you use in your environment:

```bash
python -m pip install 'types-boto3[sagemaker]'
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
- Install `types-boto3[sagemaker]` in your environment:

```bash
python -m pip install 'types-boto3[sagemaker]'
```

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pyright"></a>

### pyright

- Install `pyright`: `npm i -g pyright`
- Install `types-boto3[sagemaker]` in your environment:

```bash
python -m pip install 'types-boto3[sagemaker]'
```

Optionally, you can install `types-boto3` to `typings` directory.

Type checking should now work. No explicit type annotations required, write
your `boto3` code as usual.

<a id="pylint-compatibility"></a>

### Pylint compatibility

It is totally safe to use `TYPE_CHECKING` flag in order to avoid
`types-boto3-sagemaker` dependency in production. However, there is an issue in
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

`SageMakerClient` provides annotations for `boto3.client("sagemaker")`.

```python
from boto3.session import Session

from types_boto3_sagemaker import SageMakerClient

client: SageMakerClient = Session().client("sagemaker")

# now client usage is checked by mypy and IDE should provide code completion
```

<a id="paginators-annotations"></a>

### Paginators annotations

`types_boto3_sagemaker.paginator` module contains type annotations for all
paginators.

```python
from boto3.session import Session

from types_boto3_sagemaker import SageMakerClient
from types_boto3_sagemaker.paginator import (
    CreateHubContentPresignedUrlsPaginator,
    ListActionsPaginator,
    ListAlgorithmsPaginator,
    ListAliasesPaginator,
    ListAppImageConfigsPaginator,
    ListAppsPaginator,
    ListArtifactsPaginator,
    ListAssociationsPaginator,
    ListAutoMLJobsPaginator,
    ListCandidatesForAutoMLJobPaginator,
    ListClusterEventsPaginator,
    ListClusterNodesPaginator,
    ListClusterSchedulerConfigsPaginator,
    ListClustersPaginator,
    ListCodeRepositoriesPaginator,
    ListCompilationJobsPaginator,
    ListComputeQuotasPaginator,
    ListContextsPaginator,
    ListDataQualityJobDefinitionsPaginator,
    ListDeviceFleetsPaginator,
    ListDevicesPaginator,
    ListDomainsPaginator,
    ListEdgeDeploymentPlansPaginator,
    ListEdgePackagingJobsPaginator,
    ListEndpointConfigsPaginator,
    ListEndpointsPaginator,
    ListExperimentsPaginator,
    ListFeatureGroupsPaginator,
    ListFlowDefinitionsPaginator,
    ListHumanTaskUisPaginator,
    ListHyperParameterTuningJobsPaginator,
    ListImageVersionsPaginator,
    ListImagesPaginator,
    ListInferenceComponentsPaginator,
    ListInferenceExperimentsPaginator,
    ListInferenceRecommendationsJobStepsPaginator,
    ListInferenceRecommendationsJobsPaginator,
    ListLabelingJobsForWorkteamPaginator,
    ListLabelingJobsPaginator,
    ListLineageGroupsPaginator,
    ListMlflowTrackingServersPaginator,
    ListModelBiasJobDefinitionsPaginator,
    ListModelCardExportJobsPaginator,
    ListModelCardVersionsPaginator,
    ListModelCardsPaginator,
    ListModelExplainabilityJobDefinitionsPaginator,
    ListModelMetadataPaginator,
    ListModelPackageGroupsPaginator,
    ListModelPackagesPaginator,
    ListModelQualityJobDefinitionsPaginator,
    ListModelsPaginator,
    ListMonitoringAlertHistoryPaginator,
    ListMonitoringAlertsPaginator,
    ListMonitoringExecutionsPaginator,
    ListMonitoringSchedulesPaginator,
    ListNotebookInstanceLifecycleConfigsPaginator,
    ListNotebookInstancesPaginator,
    ListOptimizationJobsPaginator,
    ListPartnerAppsPaginator,
    ListPipelineExecutionStepsPaginator,
    ListPipelineExecutionsPaginator,
    ListPipelineParametersForExecutionPaginator,
    ListPipelineVersionsPaginator,
    ListPipelinesPaginator,
    ListProcessingJobsPaginator,
    ListResourceCatalogsPaginator,
    ListSpacesPaginator,
    ListStageDevicesPaginator,
    ListStudioLifecycleConfigsPaginator,
    ListSubscribedWorkteamsPaginator,
    ListTagsPaginator,
    ListTrainingJobsForHyperParameterTuningJobPaginator,
    ListTrainingJobsPaginator,
    ListTrainingPlansPaginator,
    ListTransformJobsPaginator,
    ListTrialComponentsPaginator,
    ListTrialsPaginator,
    ListUltraServersByReservedCapacityPaginator,
    ListUserProfilesPaginator,
    ListWorkforcesPaginator,
    ListWorkteamsPaginator,
    SearchPaginator,
)

client: SageMakerClient = Session().client("sagemaker")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
create_hub_content_presigned_urls_paginator: CreateHubContentPresignedUrlsPaginator = (
    client.get_paginator("create_hub_content_presigned_urls")
)
list_actions_paginator: ListActionsPaginator = client.get_paginator("list_actions")
list_algorithms_paginator: ListAlgorithmsPaginator = client.get_paginator("list_algorithms")
list_aliases_paginator: ListAliasesPaginator = client.get_paginator("list_aliases")
list_app_image_configs_paginator: ListAppImageConfigsPaginator = client.get_paginator(
    "list_app_image_configs"
)
list_apps_paginator: ListAppsPaginator = client.get_paginator("list_apps")
list_artifacts_paginator: ListArtifactsPaginator = client.get_paginator("list_artifacts")
list_associations_paginator: ListAssociationsPaginator = client.get_paginator("list_associations")
list_auto_ml_jobs_paginator: ListAutoMLJobsPaginator = client.get_paginator("list_auto_ml_jobs")
list_candidates_for_auto_ml_job_paginator: ListCandidatesForAutoMLJobPaginator = (
    client.get_paginator("list_candidates_for_auto_ml_job")
)
list_cluster_events_paginator: ListClusterEventsPaginator = client.get_paginator(
    "list_cluster_events"
)
list_cluster_nodes_paginator: ListClusterNodesPaginator = client.get_paginator("list_cluster_nodes")
list_cluster_scheduler_configs_paginator: ListClusterSchedulerConfigsPaginator = (
    client.get_paginator("list_cluster_scheduler_configs")
)
list_clusters_paginator: ListClustersPaginator = client.get_paginator("list_clusters")
list_code_repositories_paginator: ListCodeRepositoriesPaginator = client.get_paginator(
    "list_code_repositories"
)
list_compilation_jobs_paginator: ListCompilationJobsPaginator = client.get_paginator(
    "list_compilation_jobs"
)
list_compute_quotas_paginator: ListComputeQuotasPaginator = client.get_paginator(
    "list_compute_quotas"
)
list_contexts_paginator: ListContextsPaginator = client.get_paginator("list_contexts")
list_data_quality_job_definitions_paginator: ListDataQualityJobDefinitionsPaginator = (
    client.get_paginator("list_data_quality_job_definitions")
)
list_device_fleets_paginator: ListDeviceFleetsPaginator = client.get_paginator("list_device_fleets")
list_devices_paginator: ListDevicesPaginator = client.get_paginator("list_devices")
list_domains_paginator: ListDomainsPaginator = client.get_paginator("list_domains")
list_edge_deployment_plans_paginator: ListEdgeDeploymentPlansPaginator = client.get_paginator(
    "list_edge_deployment_plans"
)
list_edge_packaging_jobs_paginator: ListEdgePackagingJobsPaginator = client.get_paginator(
    "list_edge_packaging_jobs"
)
list_endpoint_configs_paginator: ListEndpointConfigsPaginator = client.get_paginator(
    "list_endpoint_configs"
)
list_endpoints_paginator: ListEndpointsPaginator = client.get_paginator("list_endpoints")
list_experiments_paginator: ListExperimentsPaginator = client.get_paginator("list_experiments")
list_feature_groups_paginator: ListFeatureGroupsPaginator = client.get_paginator(
    "list_feature_groups"
)
list_flow_definitions_paginator: ListFlowDefinitionsPaginator = client.get_paginator(
    "list_flow_definitions"
)
list_human_task_uis_paginator: ListHumanTaskUisPaginator = client.get_paginator(
    "list_human_task_uis"
)
list_hyper_parameter_tuning_jobs_paginator: ListHyperParameterTuningJobsPaginator = (
    client.get_paginator("list_hyper_parameter_tuning_jobs")
)
list_image_versions_paginator: ListImageVersionsPaginator = client.get_paginator(
    "list_image_versions"
)
list_images_paginator: ListImagesPaginator = client.get_paginator("list_images")
list_inference_components_paginator: ListInferenceComponentsPaginator = client.get_paginator(
    "list_inference_components"
)
list_inference_experiments_paginator: ListInferenceExperimentsPaginator = client.get_paginator(
    "list_inference_experiments"
)
list_inference_recommendations_job_steps_paginator: ListInferenceRecommendationsJobStepsPaginator = client.get_paginator(
    "list_inference_recommendations_job_steps"
)
list_inference_recommendations_jobs_paginator: ListInferenceRecommendationsJobsPaginator = (
    client.get_paginator("list_inference_recommendations_jobs")
)
list_labeling_jobs_for_workteam_paginator: ListLabelingJobsForWorkteamPaginator = (
    client.get_paginator("list_labeling_jobs_for_workteam")
)
list_labeling_jobs_paginator: ListLabelingJobsPaginator = client.get_paginator("list_labeling_jobs")
list_lineage_groups_paginator: ListLineageGroupsPaginator = client.get_paginator(
    "list_lineage_groups"
)
list_mlflow_tracking_servers_paginator: ListMlflowTrackingServersPaginator = client.get_paginator(
    "list_mlflow_tracking_servers"
)
list_model_bias_job_definitions_paginator: ListModelBiasJobDefinitionsPaginator = (
    client.get_paginator("list_model_bias_job_definitions")
)
list_model_card_export_jobs_paginator: ListModelCardExportJobsPaginator = client.get_paginator(
    "list_model_card_export_jobs"
)
list_model_card_versions_paginator: ListModelCardVersionsPaginator = client.get_paginator(
    "list_model_card_versions"
)
list_model_cards_paginator: ListModelCardsPaginator = client.get_paginator("list_model_cards")
list_model_explainability_job_definitions_paginator: ListModelExplainabilityJobDefinitionsPaginator = client.get_paginator(
    "list_model_explainability_job_definitions"
)
list_model_metadata_paginator: ListModelMetadataPaginator = client.get_paginator(
    "list_model_metadata"
)
list_model_package_groups_paginator: ListModelPackageGroupsPaginator = client.get_paginator(
    "list_model_package_groups"
)
list_model_packages_paginator: ListModelPackagesPaginator = client.get_paginator(
    "list_model_packages"
)
list_model_quality_job_definitions_paginator: ListModelQualityJobDefinitionsPaginator = (
    client.get_paginator("list_model_quality_job_definitions")
)
list_models_paginator: ListModelsPaginator = client.get_paginator("list_models")
list_monitoring_alert_history_paginator: ListMonitoringAlertHistoryPaginator = client.get_paginator(
    "list_monitoring_alert_history"
)
list_monitoring_alerts_paginator: ListMonitoringAlertsPaginator = client.get_paginator(
    "list_monitoring_alerts"
)
list_monitoring_executions_paginator: ListMonitoringExecutionsPaginator = client.get_paginator(
    "list_monitoring_executions"
)
list_monitoring_schedules_paginator: ListMonitoringSchedulesPaginator = client.get_paginator(
    "list_monitoring_schedules"
)
list_notebook_instance_lifecycle_configs_paginator: ListNotebookInstanceLifecycleConfigsPaginator = client.get_paginator(
    "list_notebook_instance_lifecycle_configs"
)
list_notebook_instances_paginator: ListNotebookInstancesPaginator = client.get_paginator(
    "list_notebook_instances"
)
list_optimization_jobs_paginator: ListOptimizationJobsPaginator = client.get_paginator(
    "list_optimization_jobs"
)
list_partner_apps_paginator: ListPartnerAppsPaginator = client.get_paginator("list_partner_apps")
list_pipeline_execution_steps_paginator: ListPipelineExecutionStepsPaginator = client.get_paginator(
    "list_pipeline_execution_steps"
)
list_pipeline_executions_paginator: ListPipelineExecutionsPaginator = client.get_paginator(
    "list_pipeline_executions"
)
list_pipeline_parameters_for_execution_paginator: ListPipelineParametersForExecutionPaginator = (
    client.get_paginator("list_pipeline_parameters_for_execution")
)
list_pipeline_versions_paginator: ListPipelineVersionsPaginator = client.get_paginator(
    "list_pipeline_versions"
)
list_pipelines_paginator: ListPipelinesPaginator = client.get_paginator("list_pipelines")
list_processing_jobs_paginator: ListProcessingJobsPaginator = client.get_paginator(
    "list_processing_jobs"
)
list_resource_catalogs_paginator: ListResourceCatalogsPaginator = client.get_paginator(
    "list_resource_catalogs"
)
list_spaces_paginator: ListSpacesPaginator = client.get_paginator("list_spaces")
list_stage_devices_paginator: ListStageDevicesPaginator = client.get_paginator("list_stage_devices")
list_studio_lifecycle_configs_paginator: ListStudioLifecycleConfigsPaginator = client.get_paginator(
    "list_studio_lifecycle_configs"
)
list_subscribed_workteams_paginator: ListSubscribedWorkteamsPaginator = client.get_paginator(
    "list_subscribed_workteams"
)
list_tags_paginator: ListTagsPaginator = client.get_paginator("list_tags")
list_training_jobs_for_hyper_parameter_tuning_job_paginator: ListTrainingJobsForHyperParameterTuningJobPaginator = client.get_paginator(
    "list_training_jobs_for_hyper_parameter_tuning_job"
)
list_training_jobs_paginator: ListTrainingJobsPaginator = client.get_paginator("list_training_jobs")
list_training_plans_paginator: ListTrainingPlansPaginator = client.get_paginator(
    "list_training_plans"
)
list_transform_jobs_paginator: ListTransformJobsPaginator = client.get_paginator(
    "list_transform_jobs"
)
list_trial_components_paginator: ListTrialComponentsPaginator = client.get_paginator(
    "list_trial_components"
)
list_trials_paginator: ListTrialsPaginator = client.get_paginator("list_trials")
list_ultra_servers_by_reserved_capacity_paginator: ListUltraServersByReservedCapacityPaginator = (
    client.get_paginator("list_ultra_servers_by_reserved_capacity")
)
list_user_profiles_paginator: ListUserProfilesPaginator = client.get_paginator("list_user_profiles")
list_workforces_paginator: ListWorkforcesPaginator = client.get_paginator("list_workforces")
list_workteams_paginator: ListWorkteamsPaginator = client.get_paginator("list_workteams")
search_paginator: SearchPaginator = client.get_paginator("search")
```

<a id="waiters-annotations"></a>

### Waiters annotations

`types_boto3_sagemaker.waiter` module contains type annotations for all
waiters.

```python
from boto3.session import Session

from types_boto3_sagemaker import SageMakerClient
from types_boto3_sagemaker.waiter import (
    EndpointDeletedWaiter,
    EndpointInServiceWaiter,
    ImageCreatedWaiter,
    ImageDeletedWaiter,
    ImageUpdatedWaiter,
    ImageVersionCreatedWaiter,
    ImageVersionDeletedWaiter,
    NotebookInstanceDeletedWaiter,
    NotebookInstanceInServiceWaiter,
    NotebookInstanceStoppedWaiter,
    ProcessingJobCompletedOrStoppedWaiter,
    TrainingJobCompletedOrStoppedWaiter,
    TransformJobCompletedOrStoppedWaiter,
)

client: SageMakerClient = Session().client("sagemaker")

# Explicit type annotations are optional here
# Types should be correctly discovered by mypy and IDEs
endpoint_deleted_waiter: EndpointDeletedWaiter = client.get_waiter("endpoint_deleted")
endpoint_in_service_waiter: EndpointInServiceWaiter = client.get_waiter("endpoint_in_service")
image_created_waiter: ImageCreatedWaiter = client.get_waiter("image_created")
image_deleted_waiter: ImageDeletedWaiter = client.get_waiter("image_deleted")
image_updated_waiter: ImageUpdatedWaiter = client.get_waiter("image_updated")
image_version_created_waiter: ImageVersionCreatedWaiter = client.get_waiter("image_version_created")
image_version_deleted_waiter: ImageVersionDeletedWaiter = client.get_waiter("image_version_deleted")
notebook_instance_deleted_waiter: NotebookInstanceDeletedWaiter = client.get_waiter(
    "notebook_instance_deleted"
)
notebook_instance_in_service_waiter: NotebookInstanceInServiceWaiter = client.get_waiter(
    "notebook_instance_in_service"
)
notebook_instance_stopped_waiter: NotebookInstanceStoppedWaiter = client.get_waiter(
    "notebook_instance_stopped"
)
processing_job_completed_or_stopped_waiter: ProcessingJobCompletedOrStoppedWaiter = (
    client.get_waiter("processing_job_completed_or_stopped")
)
training_job_completed_or_stopped_waiter: TrainingJobCompletedOrStoppedWaiter = client.get_waiter(
    "training_job_completed_or_stopped"
)
transform_job_completed_or_stopped_waiter: TransformJobCompletedOrStoppedWaiter = client.get_waiter(
    "transform_job_completed_or_stopped"
)
```

<a id="literals"></a>

### Literals

`types_boto3_sagemaker.literals` module contains literals extracted from shapes
that can be used in user code for type checking.

Full list of `SageMaker` Literals can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_sagemaker/literals/).

```python
from types_boto3_sagemaker.literals import ActionStatusType


def check_value(value: ActionStatusType) -> bool: ...
```

<a id="type-definitions"></a>

### Type definitions

`types_boto3_sagemaker.type_defs` module contains structures and shapes
assembled to typed dictionaries and unions for additional type checking.

Full list of `SageMaker` TypeDefs can be found in
[docs](https://youtype.github.io/types_boto3_docs/types_boto3_sagemaker/type_defs/).

```python
# TypedDict usage example
from types_boto3_sagemaker.type_defs import ActionSourceTypeDef


def get_value() -> ActionSourceTypeDef:
    return {
        "SourceUri": ...,
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

`types-boto3-sagemaker` version is the same as related `boto3` version and
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
[boto3 docs](https://youtype.github.io/types_boto3_docs/types_boto3_sagemaker/)

<a id="support-and-contributing"></a>

## Support and contributing

This package is auto-generated. Please reports any bugs or request new features
in [mypy-boto3-builder](https://github.com/youtype/mypy_boto3_builder/issues/)
repository.
