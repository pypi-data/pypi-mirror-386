"""HTTP client and request coordination for the PI Web API."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class PIWebAPIEncoder(json.JSONEncoder):
    """Custom JSON encoder for PI Web API that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            # Use isoformat() which produces ISO 8601 compliant strings
            time_str = obj.isoformat()
            # Convert +00:00 to Z for better PI Web API compatibility
            if time_str.endswith('+00:00'):
                time_str = time_str[:-6] + 'Z'
            return time_str
        return super().default(obj)

from .config import AuthMethod, PIWebAPIConfig
from .controllers import (
    AnalysisController,
    AnalysisCategoryController,
    AnalysisRuleController,
    AnalysisRulePlugInController,
    AnalysisTemplateController,
    AssetDatabaseController,
    AssetServerController,
    AttributeController,
    AttributeCategoryController,
    AttributeTemplateController,
    AttributeTraitController,
    BatchController,
    CalculationController,
    ChannelController,
    ConfigurationController,
    DataServerController,
    ElementController,
    ElementCategoryController,
    ElementTemplateController,
    EnumerationSetController,
    EnumerationValueController,
    EventFrameController,
    EventFrameHelpers,
    HomeController,
    MetricsController,
    NotificationContactTemplateController,
    NotificationPlugInController,
    NotificationRuleController,
    NotificationRuleSubscriberController,
    NotificationRuleTemplateController,
    OmfController,
    PointController,
    SecurityIdentityController,
    SecurityMappingController,
    StreamController,
    StreamSetController,
    SystemController,
    TableController,
    TableCategoryController,
    TimeRuleController,
    TimeRulePlugInController,
    UnitController,
    UnitClassController,
)
from .exceptions import PIWebAPIError

__all__ = ['PIWebAPIClient']

class PIWebAPIClient:
    """Main PI Web API client."""

    def __init__(self, config: PIWebAPIConfig):
        self.config = config
        self.session = requests.Session()
        self._setup_authentication()

        # Initialize controller instances
        self.analysis = AnalysisController(self)
        self.analysis_category = AnalysisCategoryController(self)
        self.analysis_rule = AnalysisRuleController(self)
        self.analysis_rule_plugin = AnalysisRulePlugInController(self)
        self.analysis_template = AnalysisTemplateController(self)
        self.asset_database = AssetDatabaseController(self)
        self.asset_server = AssetServerController(self)
        self.attribute = AttributeController(self)
        self.attribute_category = AttributeCategoryController(self)
        self.attribute_template = AttributeTemplateController(self)
        self.attribute_trait = AttributeTraitController(self)
        self.batch = BatchController(self)
        self.calculation = CalculationController(self)
        self.channel = ChannelController(self)
        self.configuration = ConfigurationController(self)
        self.data_server = DataServerController(self)
        self.element = ElementController(self)
        self.element_category = ElementCategoryController(self)
        self.element_template = ElementTemplateController(self)
        self.enumeration_set = EnumerationSetController(self)
        self.enumeration_value = EnumerationValueController(self)
        self.event_frame = EventFrameController(self)
        self.event_frame_helpers = EventFrameHelpers(self)
        self.home = HomeController(self)
        self.point = PointController(self)
        self.stream = StreamController(self)
        self.streamset = StreamSetController(self)
        self.system = SystemController(self)
        self.table = TableController(self)
        self.table_category = TableCategoryController(self)

        # New controllers
        self.omf = OmfController(self)
        self.security_identity = SecurityIdentityController(self)
        self.security_mapping = SecurityMappingController(self)
        self.notification_contact_template = NotificationContactTemplateController(self)
        self.notification_plugin = NotificationPlugInController(self)
        self.notification_rule = NotificationRuleController(self)
        self.notification_rule_subscriber = NotificationRuleSubscriberController(self)
        self.notification_rule_template = NotificationRuleTemplateController(self)
        self.time_rule = TimeRuleController(self)
        self.time_rule_plugin = TimeRulePlugInController(self)
        self.unit = UnitController(self)
        self.unit_class = UnitClassController(self)
        self.metrics = MetricsController(self)

    def _setup_authentication(self):
        """Setup authentication for the session."""
        logger.debug(f"Setting up authentication: {self.config.auth_method}")
        if self.config.auth_method == AuthMethod.BASIC:
            if self.config.username and self.config.password:
                self.session.auth = (self.config.username, self.config.password)
                logger.debug(f"Basic authentication configured for user: {self.config.username}")
            else:
                raise PIWebAPIError(
                    "Username and password required for basic authentication"
                )
        elif self.config.auth_method == AuthMethod.BEARER:
            if self.config.token:
                self.session.headers.update(
                    {"Authorization": f"Bearer {self.config.token}"}
                )
                logger.debug("Bearer token authentication configured")
            else:
                raise PIWebAPIError("Token required for bearer authentication")
        elif self.config.auth_method == AuthMethod.KERBEROS:
            # Kerberos authentication would require additional setup
            raise PIWebAPIError("Kerberos authentication not implemented in this SDK")
        elif self.config.auth_method == AuthMethod.ANONYMOUS:
            # No authentication setup needed for anonymous access
            logger.debug("Anonymous authentication configured")
            pass

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """Make HTTP request to PI Web API."""
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Add webIdType to params if not already specified
        if params is None:
            params = {}
        if "webIdType" not in params:
            params["webIdType"] = self.config.webid_type.value

        # Prepare headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)

        logger.debug(f"{method} {url}")
        if params:
            logger.debug(f"Params: {params}")
        if json_data:
            logger.debug(f"JSON Data: {json_data}")

        # Serialize json_data with custom encoder if provided
        serialized_json = None
        if json_data is not None:
            serialized_json = json.dumps(json_data, cls=PIWebAPIEncoder)
            # Set content-type header for JSON
            if 'Content-Type' not in request_headers:
                request_headers['Content-Type'] = 'application/json'

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=serialized_json if serialized_json else data,
                headers=request_headers,
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
            )

            logger.debug(f"Response: {response.status_code}")

            # Check for HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = (
                        error_data.get("Errors", [response.text])[0]
                        if error_data.get("Errors")
                        else response.text
                    )
                except:
                    error_message = response.text
                logger.error(f"HTTP {response.status_code}: {error_message}")
                raise PIWebAPIError(
                    error_message,
                    response.status_code,
                    error_data if "error_data" in locals() else None,
                )

            # Parse JSON response
            try:
                json_response = response.json()
                logger.debug(f"Response data: {str(json_response)[:200]}...")
                return json_response
            except ValueError:
                # For POST/PATCH/DELETE, check Location header for WebId
                result = {"content": response.text}
                if "Location" in response.headers:
                    result["Location"] = response.headers["Location"]
                    # Extract WebId from Location header
                    location = response.headers["Location"]
                    # WebId can be in query param (webid=...) or path (/resource/WEBID)
                    if "webid=" in location.lower():
                        web_id = location.split("webid=")[-1].split("&")[0]
                        result["WebId"] = web_id
                    else:
                        # Extract from URL path (last segment after last /)
                        path_parts = location.rstrip("/").split("/")
                        if path_parts:
                            result["WebId"] = path_parts[-1]
                logger.debug(f"Non-JSON response, returning: {result}")
                return result

        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise PIWebAPIError(f"Request failed: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params)

    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make POST request."""
        # Add X-Requested-With header for POST requests
        post_headers = {"X-Requested-With": "XMLHttpRequest"}
        if headers:
            post_headers.update(headers)
            
        return self._make_request("POST", endpoint, params=params, json_data=data, headers=post_headers)

    def put(
        self, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, params=params, json_data=data)

    def patch(
        self, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict:
        """Make PATCH request."""
        return self._make_request("PATCH", endpoint, params=params, json_data=data)

    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, params=params)
