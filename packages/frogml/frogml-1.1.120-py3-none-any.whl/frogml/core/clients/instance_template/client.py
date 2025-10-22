from typing import List

import grpc
from dependency_injector.wiring import Provide

from frogml._proto.qwak.instance_template.instance_template_pb2 import (
    InstanceFilter,
    InstanceTemplateSpec,
    InstanceTypeFilter,
)
from frogml._proto.qwak.instance_template.instance_template_service_pb2 import (
    GetInstanceTemplateRequest,
    GetInstanceTemplateResponse,
    ListInstanceTemplatesRequest,
    ListInstanceTemplatesResponse,
)
from frogml._proto.qwak.instance_template.instance_template_service_pb2_grpc import (
    InstanceTemplateManagementServiceStub,
)
from frogml.core.exceptions import FrogmlException
from frogml.core.inner.di_configuration import FrogmlContainer

GET_INSTANCE_TEMPLATE_ERROR_FORMAT = (
    "An error occurred while trying to get instance template: {e}"
)


class InstanceTemplateManagementClient:
    def __init__(self, grpc_channel=Provide[FrogmlContainer.core_grpc_channel]):
        self._instance_template_service = InstanceTemplateManagementServiceStub(
            grpc_channel
        )

    def get_instance_template(self, instance_template_id: str) -> InstanceTemplateSpec:
        try:
            result: GetInstanceTemplateResponse = (
                self._instance_template_service.GetInstanceTemplate(
                    GetInstanceTemplateRequest(id=instance_template_id)
                )
            )
            return result.instance_template
        except grpc.RpcError as e:
            raise FrogmlException(
                GET_INSTANCE_TEMPLATE_ERROR_FORMAT.format(
                    e=e.details(), error_code=e.code()
                )
            )
        except Exception as e:
            raise FrogmlException(GET_INSTANCE_TEMPLATE_ERROR_FORMAT.format(e=e))

    def list_instance_templates(self) -> List[InstanceTemplateSpec]:
        try:
            result: ListInstanceTemplatesResponse = (
                self._instance_template_service.ListInstanceTemplates(
                    ListInstanceTemplatesRequest(
                        optional_instance_filter=InstanceFilter(
                            instance_type_filter=InstanceTypeFilter.INSTANCE_TYPE_FILTER_ALL
                        )
                    )
                )
            )
            return list(result.instance_template_list)
        except grpc.RpcError as e:
            raise FrogmlException(
                GET_INSTANCE_TEMPLATE_ERROR_FORMAT.format(e=e.details()),
                status_code=e.code(),
            )
        except Exception as e:
            raise FrogmlException(GET_INSTANCE_TEMPLATE_ERROR_FORMAT.format(e=e))
