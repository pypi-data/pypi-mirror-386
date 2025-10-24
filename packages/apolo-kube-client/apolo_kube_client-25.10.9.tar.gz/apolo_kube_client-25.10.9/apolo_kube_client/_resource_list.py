from ._core import _KubeCore
from ._models import V1APIResource, V1APIResourceList


class ResourceListApi:
    """
    Resource List API wrapper for Kubernetes.
    """

    def __init__(self, core: _KubeCore) -> None:
        self._core = core

    async def get_list(self, resource_list_path: str) -> V1APIResourceList:
        async with self._core.request(
            method="GET", url=self._core.base_url / resource_list_path
        ) as response:
            return await self._core.deserialize_response(response, V1APIResourceList)

    async def find_resource_by_kind(
        self, kind: str, resource_list_path: str
    ) -> V1APIResource | None:
        """
        Find a resource by its kind in the resource list.
        """
        resource_list = await self.get_list(resource_list_path)
        resource: V1APIResource
        for resource in resource_list.resources:
            assert resource.name is not None, resource.name
            if (
                resource.kind == kind and "/" not in resource.name
            ):  # Ensure it's not a subresource
                return resource
        return None
