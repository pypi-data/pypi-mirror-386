from recombee_api_client.api_requests.request import Request
from recombee_api_client.utils.serialize_to_json import serialize_to_json
from typing import Union, List
from datetime import datetime
import uuid

DEFAULT = uuid.uuid4()


class UpdateManualReqlSegment(Request):
    """
    Update definition of the Segment.

    Required parameters:

    :param segmentation_id: ID of the Segmentation to which the updated Segment belongs

    :param segment_id: ID of the Segment that will be updated

    :param filter: ReQL filter that returns `true` for items that belong to this Segment. Otherwise returns `false`.



    Optional parameters:

    :param title: Human-readable name of the Segment that is shown in the Recombee Admin UI.


    """

    def __init__(
        self, segmentation_id: str, segment_id: str, filter: str, title: str = DEFAULT
    ):
        super().__init__(
            path="/segmentations/manual-reql/%s/segments/%s"
            % (segmentation_id, segment_id),
            method="post",
            timeout=10000,
            ensure_https=False,
        )
        self.segmentation_id = segmentation_id
        self.segment_id = segment_id
        self.filter = filter
        self.title = title

    def get_body_parameters(self) -> dict:
        """
        Values of body parameters as a dictionary (name of parameter: value of the parameter).
        """
        p = dict()
        p["filter"] = serialize_to_json(self.filter)
        if self.title is not DEFAULT:
            p["title"] = serialize_to_json(self.title)

        return p

    def get_query_parameters(self) -> dict:
        """
        Values of query parameters as a dictionary (name of parameter: value of the parameter).
        """
        params = dict()

        return params
