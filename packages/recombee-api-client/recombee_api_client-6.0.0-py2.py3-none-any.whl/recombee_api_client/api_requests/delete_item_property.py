from recombee_api_client.api_requests.request import Request
from recombee_api_client.utils.serialize_to_json import serialize_to_json
from typing import Union, List
from datetime import datetime
import uuid

DEFAULT = uuid.uuid4()


class DeleteItemProperty(Request):
    """
    Deleting an item property is roughly equivalent to removing a column from the table of items.

    Required parameters:

    :param property_name: Name of the property to be deleted.

    """

    def __init__(self, property_name: str):
        super().__init__(
            path="/items/properties/%s" % (property_name),
            method="delete",
            timeout=100000,
            ensure_https=False,
        )
        self.property_name = property_name

    def get_body_parameters(self) -> dict:
        """
        Values of body parameters as a dictionary (name of parameter: value of the parameter).
        """
        p = dict()

        return p

    def get_query_parameters(self) -> dict:
        """
        Values of query parameters as a dictionary (name of parameter: value of the parameter).
        """
        params = dict()

        return params
