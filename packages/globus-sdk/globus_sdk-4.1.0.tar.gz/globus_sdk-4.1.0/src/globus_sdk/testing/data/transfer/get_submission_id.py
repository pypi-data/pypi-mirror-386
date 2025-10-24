from globus_sdk.testing.models import RegisteredResponse, ResponseSet

from ._common import SUBMISSION_ID

RESPONSES = ResponseSet(
    metadata={"submission_id": SUBMISSION_ID},
    default=RegisteredResponse(
        service="transfer",
        path="/v0.10/submission_id",
        json={"value": SUBMISSION_ID},
    ),
)
