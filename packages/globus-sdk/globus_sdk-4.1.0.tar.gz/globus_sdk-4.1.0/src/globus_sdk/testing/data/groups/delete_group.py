from globus_sdk.testing.models import RegisteredResponse, ResponseSet

from ._common import BASE_GROUP_DOC, GROUP_ID

RESPONSES = ResponseSet(
    metadata={"group_id": GROUP_ID},
    default=RegisteredResponse(
        service="groups",
        path=f"/v2/groups/{GROUP_ID}",
        method="DELETE",
        json=BASE_GROUP_DOC,
    ),
)
