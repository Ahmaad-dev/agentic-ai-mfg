"""
Smart Planning API Client

Handles all HTTP communication with the ESAROM Smart Planning API.
Based on smartplanning-api-v1.yml specification.

Uses OAuth2 Bearer Token authentication.
"""

import requests
import logging
import urllib3
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SmartPlanningAPIError(Exception):
    """Base exception for API errors"""
    pass


class SmartPlanningAPI:
    """
    Client for ESAROM Smart Planning API
    
    API Endpoints used:
    - POST /api/v1/snapshots - Create new snapshot
    - GET /api/v1/snapshots/{id} - Fetch snapshot
    - PUT /api/v1/snapshots/{id} - Update snapshot
    - GET /api/v1/snapshots/{id}/validation-messages - Get validation errors
    
    Authentication:
    - Uses OAuth2 Bearer Token (must be provided manually)
    """
    
    def __init__(
        self, 
        base_url: str, 
        bearer_token: str,
        timeout: int = 30,
        verify_ssl: bool = False
    ):
        """
        Args:
            base_url: Base URL of Smart Planning API 
                     (e.g., https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/esarom-be/api/v1)
            bearer_token: OAuth2 Bearer Token (get from Keycloak)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates (False for test environments)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set Bearer Token in session headers
        self.session.headers.update({
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        })
        
        # Disable SSL verification if needed (for test environments)
        self.verify_ssl = verify_ssl
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL verification disabled - only use in test environments!")
        
    def create_snapshot(
        self, 
        snapshot_data: Dict[str, Any] = None,
        name: str = None,
        comment: str = None,
        run_crawler: bool = True,
        copy_from: str = None
    ) -> Dict[str, Any]:
        """
        Creates a new snapshot in Smart Planning system.
        
        Args:
            snapshot_data: The complete snapshot JSON (articles, demands, etc.)
                          If provided, snapshot will be created and immediately updated with data.
            name: Optional name for the snapshot
            comment: Optional comment
            run_crawler: If True, runs crawler to populate snapshot with real data (default: True)
            copy_from: Optional snapshot ID to copy data from
            
        Returns:
            Complete snapshot metadata dict including:
            - id: UUID of created snapshot
            - name: Snapshot name
            - comment: Snapshot comment
            - isSuccessfullyValidated: Validation status
            - dataModifiedAt: Timestamp
            - dataModifiedBy: User/Service account
            - parentId: Parent snapshot ID (if copied)
            - nrOfChildren: Number of child snapshots
            
        Raises:
            SmartPlanningAPIError: If creation fails
        """
        url = f"{self.base_url}/snapshots"
        
        # Add query parameters
        params = {}
        if run_crawler:
            params['runCrawler'] = 'true'
        if copy_from:
            params['copyFrom'] = copy_from
        
        # Generate name if not provided
        if name is None:
            name = f"AutoFix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Create snapshot (with crawler if enabled)
        payload = {
            "name": name,
            "comment": comment or "Auto-generated snapshot for validation"
        }
        
        logger.info(f"Creating snapshot: {name} (runCrawler={run_crawler})")
        
        try:
            response = self.session.post(
                url,
                json=payload,
                params=params,  # Added query parameters
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            result = response.json()
            snapshot_id = result['id']
            
            logger.info(f"✅ Snapshot created: {snapshot_id}")
            logger.info(f"   - isSuccessfullyValidated: {result.get('isSuccessfullyValidated', 'N/A')}")
            logger.info(f"   - dataModifiedAt: {result.get('dataModifiedAt', 'N/A')}")
            logger.info(f"   - dataModifiedBy: {result.get('dataModifiedBy', 'N/A')}")
            
            # Step 2: If data provided, UPDATE with data immediately
            if snapshot_data:
                logger.info(f"Updating snapshot {snapshot_id} with data...")
                self.update_snapshot(
                    snapshot_id, 
                    snapshot_data,
                    name=name,  # name is required in UPDATE!
                    comment=comment
                )
            
            return result  # Return full metadata instead of just ID
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise SmartPlanningAPIError(f"Snapshot creation failed: {e}")
    
    def get_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Fetches a snapshot including its data.
        
        Args:
            snapshot_id: UUID of the snapshot
            
        Returns:
            Complete snapshot object with dataJson
        """
        url = f"{self.base_url}/snapshots/{snapshot_id}"
        
        logger.debug(f"Fetching snapshot: {snapshot_id}")
        
        try:
            response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch snapshot: {e}")
            raise SmartPlanningAPIError(f"Snapshot fetch failed: {e}")
    
    def update_snapshot(
        self,
        snapshot_id: str,
        snapshot_data: Dict[str, Any],
        name: str = None,
        comment: str = None
    ) -> Dict[str, Any]:
        """
        Updates an existing snapshot.
        
        Args:
            snapshot_id: UUID of snapshot to update
            snapshot_data: Updated snapshot JSON
            name: Optional new name
            comment: Optional new comment
            
        Returns:
            Updated snapshot metadata (without dataJson)
        """
        import json as json_lib
        
        url = f"{self.base_url}/snapshots/{snapshot_id}"
        
        # dataJson MUST be a string (JSON-encoded), not an object!
        # name is REQUIRED in UPDATE!
        if not name:
            # Get current name from snapshot
            current_snapshot = self.get_snapshot(snapshot_id)
            name = current_snapshot.get('name', 'Updated Snapshot')
        
        payload = {
            "name": name,  # Required!
            "dataJson": json_lib.dumps(snapshot_data, ensure_ascii=False)
        }
        if comment:
            payload["comment"] = comment
        
        logger.info(f"Updating snapshot: {snapshot_id}")
        
        try:
            response = self.session.put(
                url,
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            logger.info(f"✅ Snapshot updated: {snapshot_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Try to get detailed error message
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{e} - Detail: {error_json}"
                except:
                    error_detail = f"{e} - Response: {e.response.text[:500]}"
            
            logger.error(f"Failed to update snapshot: {error_detail}")
            raise SmartPlanningAPIError(f"Snapshot update failed: {error_detail}")
    
    def get_validation_messages(self, snapshot_id: str) -> List[Dict[str, str]]:
        """
        Gets validation messages for a snapshot.
        
        Args:
            snapshot_id: UUID of the snapshot
            
        Returns:
            List of validation messages with 'level' and 'message' fields
            Example:
            [
                {
                    "level": "ERROR",
                    "message": "[validate_density_values] Article 106270 has invalid..."
                },
                {
                    "level": "WARNING",
                    "message": "[validate_worker_consistency] Workers with..."
                }
            ]
        """
        url = f"{self.base_url}/snapshots/{snapshot_id}/validation-messages"
        
        logger.debug(f"Fetching validation messages: {snapshot_id}")
        
        try:
            response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            
            # API returns paginated list
            result = response.json()
            
            # Extract elements from paged response
            if isinstance(result, dict) and 'elements' in result:
                messages = result['elements']
            elif isinstance(result, list):
                messages = result
            else:
                messages = []
            
            error_count = len([m for m in messages if m.get('level') == 'ERROR'])
            warning_count = len([m for m in messages if m.get('level') == 'WARNING'])
            
            logger.info(f"Validation: {error_count} ERRORs, {warning_count} WARNINGs")
            
            return messages
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch validation messages: {e}")
            raise SmartPlanningAPIError(f"Validation fetch failed: {e}")
    
    def delete_snapshot(self, snapshot_id: str):
        """
        Deletes a snapshot.
        
        Args:
            snapshot_id: UUID of snapshot to delete
        """
        url = f"{self.base_url}/snapshots/{snapshot_id}"
        
        logger.debug(f"Deleting snapshot: {snapshot_id}")
        
        try:
            response = self.session.delete(url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            logger.info(f"✅ Snapshot deleted: {snapshot_id}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete snapshot: {e}")
            raise SmartPlanningAPIError(f"Snapshot deletion failed: {e}")
    
    def validate_snapshot(self, snapshot_data: Dict[str, Any]) -> tuple[str, List[Dict[str, str]]]:
        """
        Convenience method: Upload snapshot and get validation messages.
        
        Args:
            snapshot_data: Complete snapshot JSON
            
        Returns:
            Tuple of (snapshot_id, validation_messages)
        """
        snapshot_id = self.create_snapshot(snapshot_data)
        validation_messages = self.get_validation_messages(snapshot_id)
        return snapshot_id, validation_messages
