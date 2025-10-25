import typing as t

from apolo_app_types.clients.kube import get_service_host_port
from apolo_app_types.outputs.common import INSTANCE_LABEL
from apolo_app_types.outputs.utils.ingress import get_ingress_host_port
from apolo_app_types.protocols.common.networking import (
    RestAPI,
    ServiceAPI,
    WebApp,
)
from apolo_app_types.protocols.dify import DifyAppOutputs, DifySpecificOutputs


async def get_dify_outputs(
    helm_values: dict[str, t.Any],
    app_instance_id: str,
) -> dict[str, t.Any]:
    main_labels = {"application": "dify", INSTANCE_LABEL: app_instance_id}
    api_labels = {**main_labels, "component": "api"}
    api_internal_host, api_internal_port = await get_service_host_port(
        match_labels=api_labels
    )
    internal_api_url = None
    if api_internal_host:
        internal_api_url = RestAPI(
            host=api_internal_host,
            port=int(api_internal_port),
            base_path="/",
            protocol="http",
        )
    web_labels = {**main_labels, "component": "web"}
    web_internal_host, web_internal_port = await get_service_host_port(
        match_labels=web_labels
    )
    internal_web_app_url = None
    if web_internal_host:
        internal_web_app_url = WebApp(
            host=web_internal_host,
            port=int(web_internal_port),
            base_path="/",
            protocol="http",
        )
    host_port = await get_ingress_host_port(match_labels=main_labels)
    external_web_app_url = None
    if host_port:
        host, port = host_port
        external_web_app_url = WebApp(
            host=host,
            port=int(port),
            base_path="/",
            protocol="https",
        )

    # Create external API URL if external web app URL exists
    external_api_url = None
    if external_web_app_url:
        external_api_url = RestAPI(
            host=external_web_app_url.host,
            port=external_web_app_url.port,
            base_path=external_web_app_url.base_path + "/v1",
            protocol=external_web_app_url.protocol,
        )

    init_password = helm_values.get("api", {}).get("initPassword", "")
    outputs = DifyAppOutputs(
        app_url=ServiceAPI[WebApp](
            internal_url=internal_web_app_url,
            external_url=external_web_app_url,
        )
        if internal_web_app_url or external_web_app_url
        else None,
        api_url=ServiceAPI[RestAPI](
            internal_url=internal_api_url,
            external_url=external_api_url,
        )
        if internal_api_url or external_api_url
        else None,
        dify_specific=DifySpecificOutputs(
            init_password=init_password,
        ),
    )
    return outputs.model_dump()
