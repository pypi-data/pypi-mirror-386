from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Dict, List, Optional, Union, Iterable

import requests
from requests import Response
from requests.auth import AuthBase

from frogml._proto.qwak.build.v1.build_pb2 import DESCRIPTOR
from frogml._proto.qwak.models.models_pb2 import (
    ListModelsMetadataResponse,
    ModelMetadata as ModelMetadataProto,
)
from frogml.core.clients.analytics.client import AnalyticsEngineClient
from frogml.core.clients.automation_management.client import AutomationsManagementClient
from frogml.core.clients.batch_job_management.client import BatchJobManagerClient
from frogml.core.clients.build_orchestrator.client import (
    BuildFilter,
    BuildOrchestratorClient,
)
from frogml.core.clients.data_versioning.client import DataVersioningManagementClient
from frogml.core.clients.data_versioning.data_tag_filter import DataTagFilter
from frogml.core.clients.deployment.client import DeploymentManagementClient
from frogml.core.clients.feature_store import FeatureRegistryClient
from frogml.core.clients.file_versioning.client import FileVersioningManagementClient
from frogml.core.clients.file_versioning.file_tag_filter import FileTagFilter
from frogml.core.clients.instance_template.client import (
    InstanceTemplateManagementClient,
)
from frogml.core.clients.jfrog_gateway.client import JfrogGatewayClient
from frogml.core.clients.model_management.client import ModelsManagementClient
from frogml.core.clients.model_version_manager import ModelVersionManagerClient
from frogml.core.exceptions import FrogmlException
from frogml.core.inner.build_config.build_config_v1 import BuildConfigV1
from frogml.core.inner.tool.auth import FrogMLAuthClient
from frogml.feature_store.feature_sets.batch import BatchFeatureSet
from frogml.sdk.frogml_client.batch_jobs.execution import Execution
from frogml.sdk.frogml_client.batch_jobs.task import Task
from frogml.sdk.frogml_client.builds.build import Build
from frogml.sdk.frogml_client.builds.filters.metric_filter import MetricFilter
from frogml.sdk.frogml_client.builds.filters.parameter_filter import ParameterFilter
from frogml.sdk.frogml_client.data_versioning.data_tag import DataTag
from frogml.sdk.frogml_client.deployments.deployment import (
    Deployment,
    EnvironmentAudienceRoute,
)
from frogml.sdk.frogml_client.file_versioning.file_tag import FileTag
from frogml.sdk.frogml_client.models.model import Model
from frogml.sdk.frogml_client.models.model_metadata import ModelMetadata
from frogml.sdk.model.base import BaseModel

if TYPE_CHECKING:
    try:
        import pandas as pd
    except ImportError:
        pass


class FrogMLClient:
    """
    Comprehensive Frogml client to manage operations performed against the Frogml system.
    Acts as a wrapper and single entry point for the different Frogml clients - BatchClient,
    DeploymentClient, and more.
    """

    @lru_cache(maxsize=1)
    def _get_model_management(self) -> ModelsManagementClient:
        return ModelsManagementClient()

    @lru_cache(maxsize=1)
    def _get_build_orchestrator(self) -> BuildOrchestratorClient:
        return BuildOrchestratorClient()

    @lru_cache(maxsize=1)
    def _get_batch_job_manager(self) -> BatchJobManagerClient:
        return BatchJobManagerClient()

    @lru_cache(maxsize=1)
    def _get_file_versioning_management(self) -> FileVersioningManagementClient:
        return FileVersioningManagementClient()

    @lru_cache(maxsize=1)
    def _get_data_versioning_management(self) -> DataVersioningManagementClient:
        return DataVersioningManagementClient()

    @lru_cache(maxsize=1)
    def _get_deployment_management(self) -> DeploymentManagementClient:
        return DeploymentManagementClient()

    @lru_cache(maxsize=1)
    def _get_feature_registry_client(self) -> FeatureRegistryClient:
        return FeatureRegistryClient()

    @lru_cache(maxsize=1)
    def _get_automations_client(self) -> AutomationsManagementClient:
        return AutomationsManagementClient()

    @lru_cache(maxsize=1)
    def _get_analytics_engine(self) -> AnalyticsEngineClient:
        return AnalyticsEngineClient()

    @lru_cache(maxsize=1)
    def _get_instance_template_client(self) -> InstanceTemplateManagementClient:
        return InstanceTemplateManagementClient()

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_auth_client():
        return FrogMLAuthClient()

    @lru_cache(maxsize=1)
    def _get_model_version_manager_client(self) -> ModelVersionManagerClient:
        return ModelVersionManagerClient()

    @lru_cache(maxsize=1)
    def _get_jfrog_gateway_client(self) -> JfrogGatewayClient:
        return JfrogGatewayClient()

    def get_token(self) -> str:
        """
        Retrieve a token by api key.
        Use Cases:
        Default - from already configured (frogml configured) - conf file
        Support FROGML_API_KEY environment variable
        Get token for a specified API key
        Returns:
            str: a client token
        """
        client = self._get_auth_client()
        return client.get_token()

    def get_latest_build(
        self, model_id: str, build_status: str = "SUCCESSFUL"
    ) -> Optional[str]:
        """
        Get the latest build by its model ID.
        Optionally gets a build_status, by default filters on 'SUCCESSFUL'

        Args:
            model_id (str): The model ID
            build_status (str): build statuses to filter on. Valid values are 'SUCCESSFUL', 'IN_PROGRESS', 'FAILED'

        Returns:
             str: The build ID of the latest build according to the build status. None if no builds match the filter.

        """
        if (
            build_status
            not in DESCRIPTOR.enum_types_by_name["BuildStatus"].values_by_name
        ):
            raise FrogmlException(
                f"Invalid build status {build_status}. Valid options are 'SUCCESSFUL', 'IN_PROGRESS', 'FAILED'"
            )

        model = self._get_model_management().get_model(model_id=model_id)
        model_uuid = model.uuid

        builds = self._get_build_orchestrator().list_builds(model_uuid=model_uuid).build
        if not builds:
            return None

        builds = [
            build
            for build in builds
            if build.build_status
            == DESCRIPTOR.enum_types_by_name["BuildStatus"]
            .values_by_name[build_status]
            .number
        ]
        builds.sort(key=lambda r: r.audit.created_at.seconds)

        return builds[-1].buildId if builds else None

    def get_builds_by_tags(
        self,
        model_id: str,
        tags: List[str],
        match_any: bool = True,
        include_extra_tags: bool = True,
    ) -> List[Build]:
        """
        Get builds by its model ID and explicit tags

        Args:
            model_id (str): The model ID
            tags (List[str]): List of tags to filter by
            match_any (bool): Whether matching any tag is enough to return a build (default: True)
            include_extra_tags (bool): Whether builds are allowed to have more tags than the ones specified in the tags list (default: True)

        Returns:
             List[Build]: List of builds that contains the requested tags.

        """
        model = self._get_model_management().get_model(model_id=model_id)
        model_uuid = model.uuid

        builds_proto = (
            self._get_build_orchestrator()
            .list_builds(
                model_uuid=model_uuid,
                build_filter=BuildFilter(
                    tags=tags,
                    require_all_tags=not match_any,
                    include_extra_tags=include_extra_tags,
                ),
            )
            .build
        )

        builds = [Build.from_proto(build) for build in builds_proto]

        return builds if builds else None

    def get_build(self, build_id: str) -> Build:
        """
        Get builds by its build ID

        Args:
            build_id (str): The build ID

        Returns:
             Build: The requested build.

        """
        build_proto = self._get_build_orchestrator().get_build(build_id).build

        build = Build.from_proto(build_proto)

        if build:
            model_proto = self._get_model_management().get_model_by_uuid(
                model_uuid=build_proto.model_uuid
            )
            build.model_id = model_proto.model_id

        return build if build else None

    def list_builds(
        self,
        model_id: str,
        tags: Optional[List[str]] = None,
        filters: Optional[List[Union[MetricFilter, ParameterFilter]]] = None,
    ) -> List[Build]:
        """
        List builds by its model ID and explicit filters

        Args:
            model_id (str): The model ID
            tags (List[str]): List of tags to filter by
            filters (List[str]): List of metric and parameter filters

        Returns:
             List[Build]: List of builds that contains the requested filters.

        """
        tags = tags if tags is not None else []
        filters = filters if filters is not None else []

        model = self._get_model_management().get_model(model_id=model_id)
        model_uuid = model.uuid

        metric_filters = list()
        parameter_filters = list()

        for build_filter in filters:
            if isinstance(build_filter, MetricFilter):
                metric_filters.append(MetricFilter.to_proto(build_filter))
            else:
                parameter_filters.append(ParameterFilter.to_proto(build_filter))

        builds_proto = (
            self._get_build_orchestrator()
            .list_builds(
                model_uuid=model_uuid,
                build_filter=BuildFilter(
                    tags=tags,
                    metric_filters=metric_filters,
                    parameter_filters=parameter_filters,
                ),
            )
            .build
        )

        return [Build.from_proto(build) for build in builds_proto]

    def list_file_tags(
        self,
        model_id: str,
        build_id: str = "",
        filter: Optional[FileTagFilter] = None,
    ) -> List[FileTag]:
        """
        List file tags by its model ID

        Args:
            model_id (str): The model ID
            build_id (str): The build ID - optional.
                If not specified, returns all model file tags.
            filter (FileTagFilter): Filter list by - optional.
                value (str): The filter value.
                type (enum): The filter type - FILE_TAG_FILTER_TYPE_CONTAINS/FILE_TAG_FILTER_TYPE_PREFIX.
                If not specified, returns all model file tags.


        Returns:
             List[FileTag]: List of file tags with their specifications.

        """
        model_file_tags_proto = (
            self._get_file_versioning_management().get_model_file_tags(
                model_id=model_id,
                build_id=build_id,
                file_tag_filter=None if filter is None else filter.to_proto(),
            )
        )

        return [
            FileTag.from_proto(file_tag) for file_tag in model_file_tags_proto.file_tags
        ]

    def list_data_tags(
        self,
        model_id: str,
        build_id: str = "",
        filter: Optional[DataTagFilter] = None,
    ) -> List[DataTag]:
        """
        List data tags by its model ID

        Args:
            model_id (str): The model ID
            build_id (str): The build ID - optional.
                If not specified, returns all model data tags.
            filter (DataTagFilter): Filter list by - optional.
                value (str): The filter value.
                type (enum): The filter type - DATA_TAG_FILTER_TYPE_CONTAINS/DATA_TAG_FILTER_TYPE_PREFIX.
                If not specified, returns all model file tags.

        Returns:
             List[DataTag]: List of data tags with their specifications.

        """
        model_data_tags_proto = (
            self._get_data_versioning_management().get_model_data_tags(
                model_id=model_id,
                build_id=build_id,
                data_tag_filter=None if filter is None else filter.to_proto(),
            )
        )

        return [
            DataTag.from_proto(data_tag) for data_tag in model_data_tags_proto.data_tags
        ]

    def set_tag(self, build_id: str, tag: str) -> None:
        """
        Assign a tag to an existing build

        Args:
            build_id (str): The build ID
            tag (str): The tag to assign

        """
        self._get_build_orchestrator().register_tags(build_id=build_id, tags=[tag])

    def set_tags(self, build_id: str, tags: List[str]) -> None:
        """
        Assign a list of tags to an existing build

        Args:
            build_id (str): The build ID
            tags (List[str]): List of tags to assign
        """
        self._get_build_orchestrator().register_tags(build_id=build_id, tags=tags)

    def create_model(
        self,
        project_id: str,
        model_name: str,
        model_description: str,
        jfrog_project_key: Optional[str] = None,
    ) -> str:
        """
        Create model

        Args:
            project_id (str): The project ID to associate the model
            model_name (str): The requested name
            model_description (str): The requested description
            jfrog_project_key (Optional[str]): The JFrog project key

        Returns:
             str: The model ID of the newly created project

        """
        model = self._get_model_management().create_model(
            project_id=project_id,
            model_name=model_name,
            model_description=model_description,
            jfrog_project_key=jfrog_project_key,
        )

        return model.model_id

    def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get model by its model ID

        Args:
            model_id (str): The model ID

        Returns:
             Optional[Model]: Model by ID.

        """
        return Model.from_proto(
            self._get_model_management().get_model(model_id=model_id)
        )

    def list_model_metadata(self, project_id: str) -> List[ModelMetadata]:
        """
        Lists metadata of all models in a project.
        Args:
            project_id (str): The project ID
        Returns:
            List[ModelMetadata]: List of model metadata
        """
        service_response: ListModelsMetadataResponse = (
            self._get_model_management().list_models_metadata(project_id)
        )
        model_metadata_from_service: Iterable[ModelMetadataProto] = (
            service_response.model_metadata
        )

        result: List[ModelMetadata] = []
        for metadata_source in model_metadata_from_service:
            model_metadata = ModelMetadata()

            model_metadata.model = Model.from_proto(metadata_source.model)
            model_metadata.deployed_builds = [
                Build.from_proto(build) for build in metadata_source.build
            ]
            model_metadata.deployments = [
                Deployment.from_proto(deployment)
                for deployment in metadata_source.deployment_details
            ]

            audience_routes = []
            for (
                env_id,
                env,
            ) in metadata_source.audience_routes_grouped_by_environment.items():
                for route in env.audience_routes:
                    audience_routes.append(
                        EnvironmentAudienceRoute.from_proto(route, env_id)
                    )

            model_metadata.audience_routes = audience_routes
            result.append(model_metadata)

        return result

    def list_models(self, project_id: str) -> List[Model]:
        """
        List models

        Args:
            project_id (str): The project ID to list models from

        Returns:
             List[BaseModel]: List of models

        """
        models_proto = (
            self._get_model_management().list_models(project_id=project_id).models
        )

        return [Model.from_proto(model) for model in models_proto]

    def get_model_metadata(self, model_id: str) -> ModelMetadata:
        """
        Get model metadata by its model ID

        Args:
            model_id (str): The model ID

        Returns:
            Model metadata by ID.
        """
        service_response = self._get_model_management().get_model_metadata(model_id)
        model_metadata_from_service = service_response.model_metadata
        model_metadata = ModelMetadata()

        model_metadata.model = Model.from_proto(model_metadata_from_service.model)
        model_metadata.deployed_builds = [
            Build.from_builds_management(build)
            for build in model_metadata_from_service.build
        ]
        model_metadata.deployments = [
            Deployment.from_proto(deployment)
            for deployment in model_metadata_from_service.deployment_details
        ]

        audience_routes = []
        for (
            env_id,
            env,
        ) in model_metadata_from_service.audience_routes_grouped_by_environment.items():
            for route in env.audience_routes:
                audience_routes.append(
                    EnvironmentAudienceRoute.from_proto(env_id, route)
                )
        model_metadata.audience_routes = audience_routes

        return model_metadata

    def list_models_metadata(self, project_id: str) -> List[ModelMetadata]:
        """
        List models metadata

        Args:
            project_id (str): The project ID to list models metadata from

        Returns:
             List[ModelMetadata]: List of models metadata

        """
        models_metadata_proto = (
            self._get_model_management()
            .list_models_metadata(project_id=project_id)
            .model_metadata
        )

        return [
            ModelMetadata.from_proto(model_metadata)
            for model_metadata in models_metadata_proto
        ]

    def delete_model(self, model_id: str) -> None:
        """
        Delete model by its model ID

        Args:
            model_id (str): The model ID
        """
        return self._get_model_management().delete_model(
            project_id=self.get_model(model_id).project_id, model_id=model_id
        )

    def get_deployed_build_id_per_environment(
        self, model_id: str
    ) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Get deployed build ID per environment by its model ID

        Args:
            model_id (str): The model ID

        Returns:
             Dict[str, str]: Map environment to deployed build ID. None if the model is not deployed.

        """
        model = self._get_model_management().get_model(model_id=model_id)
        model_uuid = model.uuid

        deployment_details = self._get_deployment_management().get_deployment_details(
            model_id=model_id, model_uuid=model_uuid
        )

        if not deployment_details:
            return None

        environment_to_deployment_details = (
            deployment_details.environment_to_deployment_details
        )

        return {
            env_id: {
                deployment.variation.name: deployment.build_id
                for deployment in v.deployments_details
            }
            for env_id, v in environment_to_deployment_details.items()
        }

    def run_analytics_query(
        self, query: str, timeout: timedelta = None
    ) -> "pd.DataFrame":
        """
        Runs a Frogml Analytics Query and returns the Pandas DataFrame with the results.

        Args:
            query (str): The query to run
            timeout (timedelta): The timeout for the query - optional.
                If not specified, the function will wait indefinitely.

        Returns:
            pd.DataFrame: The results of the query
        """
        try:
            import pandas as pd
        except ImportError:
            raise FrogmlException(
                "Missing Pandas dependency required for running an analytics query."
            )
        client = self._get_analytics_engine()
        url = client.get_analytics_data(query=query, timeout=timeout)
        return pd.read_csv(url)

    def list_feature_sets(self) -> List[BatchFeatureSet]:
        """
        List all feature sets

        Returns:
            List[FeatureSet]: List of feature sets
        """
        client = self._get_feature_registry_client()
        feature_set_protos = client.list_feature_sets().feature_families

        return [
            BatchFeatureSet._from_proto(
                feature_set.feature_set_definition.feature_set_spec
            )
            for feature_set in feature_set_protos
        ]

    def delete_feature_set(self, feature_set_name: str):
        """
        Delete a feature set

        Args:
            feature_set_name (str): The feature set name
        """
        client = self._get_feature_registry_client()
        feature_set_def = client.get_feature_set_by_name(
            feature_set_name=feature_set_name
        )
        if feature_set_def:
            client.delete_feature_set(
                feature_set_def.feature_set.feature_set_definition.feature_set_id
            )
        else:
            raise FrogmlException(f"Feature set named '{feature_set_name}' not found")

    def delete_featureset_version(self, featureset_name: str, version_number: int):
        """
        Delete a feature set version

        Args:
            featureset_name (str): The feature set name
            version_number (int): version number
        """
        client = self._get_feature_registry_client()

        client.delete_featureset_version(
            featureset_name=featureset_name, version_number=version_number
        )

    def set_featureset_active_version(self, featureset_name: str, version_number: int):
        """
        Set active feature set version

        Args:
            featureset_name (str): The feature set name
            version_number (int): version number
        """
        client = self._get_feature_registry_client()

        client.set_active_featureset_version(
            featureset_name=featureset_name, version_number=version_number
        )

    def delete_data_source(self, data_source_name: str):
        """
        Delete a data source

        Args:
            data_source_name (str): The data source name
        """
        client = self._get_feature_registry_client()
        data_source_def = client.get_data_source_by_name(
            data_source_name=data_source_name
        )
        if data_source_def:
            client.delete_data_source(
                data_source_def.data_source.data_source_definition.data_source_id
            )
        else:
            raise FrogmlException(f"Data source named '{data_source_name}' not found")

    def delete_entity(self, entity_name: str):
        """
        Delete an entity_name

        Args:
            entity_name (str): The entity name
        """
        client = self._get_feature_registry_client()
        entity_def = client.get_entity_by_name(entity_name=entity_name)
        if entity_def:
            client.delete_entity(entity_def.entity.entity_definition.entity_id)
        else:
            raise FrogmlException(f"Entity named '{entity_name}' not found")

    def trigger_batch_feature_set(self, feature_set_name):
        """
        Triggers a batch feature set ingestion job immediately.

        Args:
            feature_set_name (str): The feature set name
        """
        client = self._get_feature_registry_client()
        client.run_feature_set(feature_set_name=feature_set_name)

    def trigger_automation(self, automation_name):
        """
        Triggers an automation immediately.

        Args:
            automation_name (str): The automation name
        """
        client = self._get_automations_client()
        automation = client.get_automation_by_name(automation_name=automation_name)
        if not automation:
            raise FrogmlException(
                f"Could not find automation with given name '{automation_name}'"
            )
        client.run_automation(automation_id=automation.id)

    def build_model(
        self,
        model_id: str,
        main_module_path: str = ".",
        dependencies_file: Optional[str] = None,
        dependencies_list: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        instance: str = "small",
        gpu_compatible: bool = False,
        run_tests: bool = True,
        validate_build_artifact: bool = True,
        validate_build_artifact_timeout: Optional[int] = None,
        prebuilt_frogml_model: Optional[BaseModel] = None,
        base_image: Optional[str] = None,
        build_name: str = "",
    ):
        from frogml.sdk.frogml_client.build_api_helpers.trigger_build_api import (
            trigger_build_api,
        )

        config = BuildConfigV1()
        config.build_properties.model_id = model_id
        config.build_properties.build_name = build_name
        config.build_properties.model_uri.uri = main_module_path
        config.build_env.python_env.dependency_file_path = dependencies_file
        config.build_properties.tags = tags if tags else []
        config.build_env.remote.resources.instance = instance
        config.build_properties.gpu_compatible = gpu_compatible
        config.step.validate_build_artifact = validate_build_artifact
        config.step.tests = run_tests
        config.fetch_base_docker_image_name(
            self._get_build_orchestrator(), self._get_instance_template_client()
        )
        config.pre_built_model = prebuilt_frogml_model
        if validate_build_artifact_timeout:
            config.step.validate_build_artifact_timeout = (
                validate_build_artifact_timeout
            )
        if base_image:
            config.build_env.docker.base_image = base_image
        if dependencies_list:
            with TemporaryDirectory() as temporary_directory:
                requirements_filename = Path(temporary_directory) / "requirements.txt"
                with open(requirements_filename, "w") as temp_dependencies_file:
                    temp_dependencies_file.write("\n".join(dependencies_list))
                config.build_env.python_env.dependency_file_path = requirements_filename
                return trigger_build_api(config)
        else:
            return trigger_build_api(config)

    def list_executions(
        self,
        model_id: str,
        build_id: str = "",
    ) -> List[Execution]:
        """
        List batch executions by its model ID

        Args:
            model_id (str): The model ID
            build_id (str): The build ID - optional.
                If not specified, returns all model executions.


        Returns:
             List[Execution]: List of executions with their specifications.

        """
        model_executions_proto = self._get_batch_job_manager().list_batch_jobs(
            model_id=model_id,
            build_id=build_id,
        )

        return [
            Execution.from_proto(execution)
            for execution in model_executions_proto.batch_jobs
        ]

    def list_execution_tasks(
        self,
        execution_id: str,
    ) -> List[Task]:
        """
        List batch executions tasks by its job ID

        Args:
            execution_id (str): The execution ID


        Returns:
             List[Task]: List of execution tasks with their specifications.

        """
        model_execution_tasks_proto = (
            self._get_batch_job_manager().get_batch_job_details(
                job_id=execution_id,
            )
        )

        return [
            Task.from_proto(task)
            for task in model_execution_tasks_proto.batch_job.task_executions
        ]

    @staticmethod
    def download_artifact(download_url: str, timeout: int = 60) -> Response:
        auth: AuthBase = FrogMLClient._get_auth_client().get_auth()

        return requests.get(download_url, auth=auth, timeout=timeout)
