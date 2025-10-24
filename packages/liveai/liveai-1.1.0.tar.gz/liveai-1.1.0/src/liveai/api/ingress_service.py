import aiohttp
from liveai.protocol.ingress import (
    CreateIngressRequest,
    IngressInfo,
    UpdateIngressRequest,
    ListIngressRequest,
    DeleteIngressRequest,
    ListIngressResponse,
)
from ._service import Service
from .access_token import VideoGrants

SVC = "Ingress"
"""@private"""


class IngressService(Service):
    """Client for LiveAI Ingress Service API

    Recommended way to use this service is via `liveai.api.LiveAIAPI`:

    ```python
    from liveai import api
    laapi = api.LiveAIAPI()
    ingress = laapi.ingress
    ```

    Also see https://docs.liveai.io/home/ingress/overview/
    """

    def __init__(self, session: aiohttp.ClientSession, url: str, api_key: str, api_secret: str):
        super().__init__(session, url, api_key, api_secret)

    async def create_ingress(self, create: CreateIngressRequest) -> IngressInfo:
        return await self._client.request(
            SVC,
            "CreateIngress",
            create,
            self._auth_header(VideoGrants(ingress_admin=True)),
            IngressInfo,
        )

    async def update_ingress(self, update: UpdateIngressRequest) -> IngressInfo:
        return await self._client.request(
            SVC,
            "UpdateIngress",
            update,
            self._auth_header(VideoGrants(ingress_admin=True)),
            IngressInfo,
        )

    async def list_ingress(self, list: ListIngressRequest) -> ListIngressResponse:
        return await self._client.request(
            SVC,
            "ListIngress",
            list,
            self._auth_header(VideoGrants(ingress_admin=True)),
            ListIngressResponse,
        )

    async def delete_ingress(self, delete: DeleteIngressRequest) -> IngressInfo:
        return await self._client.request(
            SVC,
            "DeleteIngress",
            delete,
            self._auth_header(VideoGrants(ingress_admin=True)),
            IngressInfo,
        )
