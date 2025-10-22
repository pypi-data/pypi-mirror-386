import grpc
from dependency_injector import containers, providers

from frogml.core.inner.tool.grpc.grpc_tools import (
    create_grpc_channel,
    create_grpc_channel_or_none,
)


class FrogmlContainer(containers.DeclarativeContainer):
    """
    JFrog ML CLI dependencies
    """

    config = providers.Configuration(strict=True)

    core_grpc_channel = providers.Singleton(
        create_grpc_channel,
        url=config.grpc.core.address,
        enable_ssl=config.grpc.core.enable_ssl,
        status_for_retry=(
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.CANCELLED,
            grpc.StatusCode.DEADLINE_EXCEEDED,
        ),
    )

    unauthenticated_core_grpc_channel = providers.Singleton(
        create_grpc_channel,
        url=config.grpc.core.address,
        enable_ssl=config.grpc.authentication.enable_ssl,
        enable_auth=False,
    )

    non_jf_tenant_core_grpc_channel = providers.Singleton(
        create_grpc_channel,
        url=config.grpc.core.address,
        enable_ssl=config.grpc.authentication.enable_ssl,
        should_pass_jf_tenant_id=False,
    )

    internal_grpc_channel_for_builds_orchestrator_factory = providers.Singleton(
        create_grpc_channel_or_none,
        url=config.grpc.builds.internal_address,
        enable_ssl=config.grpc.builds.enable_ssl,
        enable_auth=False,
        status_for_retry=(
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.DEADLINE_EXCEEDED,
        ),
    )
