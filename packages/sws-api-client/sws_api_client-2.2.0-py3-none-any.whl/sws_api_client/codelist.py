"""Codelists Module for SWS API.

This module provides functionality for managing codelists and retrieving
codelist information through the SWS API client.
"""

import logging
from time import sleep
import os
from pydantic import BaseModel, Extra
from typing import List, Optional, Dict
from sws_api_client.generic_models import Code, Multilanguage
from sws_api_client.sws_api_client import SwsApiClient

logger = logging.getLogger(__name__)

class CodelistModel(BaseModel, extra="allow"):
    """Model representing a codelist's metadata.

    Attributes:
        id (str): Unique identifier of the codelist
        label (Multilanguage): Multilanguage labels for the codelist
        type (str): Type of the codelist
    """
    id: str
    label: Multilanguage
    type: str

class Codelist(BaseModel, extra="allow"):
    """Model representing a complete codelist with its codes.

    Attributes:
        model (CodelistModel): Metadata of the codelist
        codes (List[Code]): List of codes belonging to this codelist
    """
    model: CodelistModel
    codes: List[Code]

class Codelists:
    """Class for managing codelist operations through the SWS API.

    This class provides methods for retrieving codelist information
    and managing codelist data.

    Args:
        sws_client (SwsApiClient): An instance of the SWS API client
    """

    def __init__(self, sws_client: SwsApiClient) -> None:
        """Initialize the Codelists manager with SWS client."""
        self.sws_client = sws_client

    def get_codelist(self, codelist_id: str, nocache: bool = False) -> Codelist:
        """Retrieve a codelist by its ID.

        Args:
            codelist_id (str): The identifier of the codelist
            nocache (bool, optional): Whether to bypass cache. Defaults to False.

        Returns:
            Codelist: The requested codelist with its codes

        Raises:
            HTTPError: If the codelist cannot be retrieved
        """
        url = f"/admin/reference/codelist/{codelist_id}?nocache={'true' if nocache else 'false'}"

        response = self.sws_client.discoverable.get('is_api', url)
        return Codelist(**response)