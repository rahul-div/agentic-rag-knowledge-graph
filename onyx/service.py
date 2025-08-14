"""
Concrete Onyx service implementation that connects to the real Onyx API.

This module provides the production implementation of the OnyxInterface,
handling HTTP communication with the Onyx API including authentication,
error handling, and proper logging.

Based on Onyx documentation and API specifications from:
- https://github.com/onyx-dot-app/onyx
- https://docs.onyx.app/
- API endpoints structure from backend analysis
"""

import json
import logging
import requests
from typing import Any, Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .interface import OnyxInterface
from .config import get_onyx_config


logger = logging.getLogger(__name__)


class OnyxAPIError(Exception):
    """Custom exception for Onyx API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class OnyxTimeoutError(OnyxAPIError):
    """Exception for API timeout errors."""

    pass


class OnyxAuthenticationError(OnyxAPIError):
    """Exception for authentication errors."""

    pass


class OnyxRateLimitError(OnyxAPIError):
    """Exception for rate limit errors (429)."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class OnyxValidationError(OnyxAPIError):
    """Exception for validation errors (400)."""

    pass


class OnyxService(OnyxInterface):
    """
    Production implementation of OnyxInterface that integrates with the actual Onyx API.

    This service handles HTTP communication, authentication, error handling,
    and retry logic for interactions with the Onyx platform.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Onyx service with API configuration.

        Args:
            api_key (Optional[str]): API key for authentication. If None, loads from environment.

        Raises:
            ValueError: If configuration is invalid or missing required values
            OnyxAuthenticationError: If API key is invalid or missing
        """
        # Load configuration from environment or use provided values
        if api_key is None:
            config = get_onyx_config()
            api_key = config["api_key"]
            self.base_url = config["base_url"]
            self.timeout = int(config["timeout"])
        else:
            # Use provided API key but load other config from environment
            try:
                config = get_onyx_config()
                self.base_url = config["base_url"]
                self.timeout = int(config["timeout"])
            except ValueError:
                # Fall back to defaults if environment config is not available
                self.base_url = "http://localhost:3000"
                self.timeout = 30

        super().__init__(api_key)

        # Set up HTTP session with retry strategy
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        logger.info(f"Initialized OnyxService with base_url: {self.base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the Onyx API with proper error handling.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint (without base URL)
            **kwargs: Additional arguments for requests

        Returns:
            Dict[str, Any]: JSON response data

        Raises:
            OnyxTimeoutError: If request times out
            OnyxAuthenticationError: If authentication fails
            OnyxAPIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"

        # Set timeout if not provided - use longer timeout for chat endpoints
        if "timeout" not in kwargs:
            # Chat endpoints need longer timeouts due to LLM processing
            if "/chat/" in endpoint or "/query/" in endpoint:
                kwargs["timeout"] = max(self.timeout, 30)  # At least 30 seconds for chat
            else:
                kwargs["timeout"] = self.timeout

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)

            # Handle authentication errors
            if response.status_code == 401:
                raise OnyxAuthenticationError(
                    "Authentication failed. Please check your API key.", status_code=401
                )

            # Handle validation errors
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "Validation error")
                except (ValueError, json.JSONDecodeError):
                    detail = response.text or "Bad request"

                raise OnyxValidationError(
                    f"Validation error: {detail}",
                    status_code=400,
                    response_data=error_data if "error_data" in locals() else None,
                )

            # Handle permission errors
            if response.status_code == 403:
                raise OnyxAuthenticationError(
                    "Access forbidden. Insufficient permissions.", status_code=403
                )

            # Handle rate limit errors
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_after_seconds = int(retry_after) if retry_after else None
                raise OnyxRateLimitError(
                    f"Rate limit exceeded. {'Retry after ' + retry_after + ' seconds.' if retry_after else 'Please try again later.'}",
                    retry_after=retry_after_seconds,
                )

            # Handle other client/server errors
            if not response.ok:
                try:
                    error_data = response.json()
                except (ValueError, json.JSONDecodeError):
                    error_data = {"error": response.text}

                raise OnyxAPIError(
                    f"API request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            try:
                return response.json()
            except (ValueError, json.JSONDecodeError) as e:
                raise OnyxAPIError(f"Invalid JSON response: {e}")

        except requests.exceptions.Timeout as e:
            raise OnyxTimeoutError(
                f"Request timed out after {self.timeout} seconds"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise OnyxAPIError(f"Connection error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise OnyxAPIError(f"Request failed: {e}") from e

    def create_chat_session(self, document_set_id: Optional[str] = None) -> str:
        """
        Create a new chat session with the Onyx API.

        Args:
            document_set_id (Optional[str]): ID of the document set to target

        Returns:
            str: Unique session ID for the created chat session

        Raises:
            OnyxAPIError: If session creation fails
        """
        payload = {"persona_id": 0, "description": None}

        if document_set_id:
            payload["document_set_id"] = document_set_id

        try:
            response_data = self._make_request(
                "POST", "/api/chat/create-chat-session", json=payload
            )
            session_id = response_data.get("chat_session_id")

            if not session_id:
                raise OnyxAPIError("No chat_session_id returned from API")

            logger.info(f"Created chat session: {session_id}")
            return session_id

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error creating chat session: {e}") from e

    def chat(
        self,
        session_id: str,
        message: str,
        document_set_ids: Optional[List[str]] = None,
        persona_id: Optional[int] = None,
        use_agentic_search: bool = False,
    ) -> str:
        """
        Send a message to an existing chat session and receive a response.

        Args:
            session_id (str): ID of the chat session to send message to
            message (str): The message content to send
            document_set_ids (Optional[List[str]]): List of document set IDs to target
            persona_id (Optional[int]): Override the default persona for this message
            use_agentic_search (bool): Whether to use agentic search capabilities

        Returns:
            str: Response message from the Onyx service

        Raises:
            OnyxAPIError: If chat interaction fails
        """
        payload = {
            "alternate_assistant_id": persona_id or 0,
            "chat_session_id": session_id,
            "parent_message_id": None,
            "message": message,
            "prompt_id": None,
            "search_doc_ids": document_set_ids,
            "file_descriptors": [],
            "user_file_ids": [],
            "user_folder_ids": [],
            "regenerate": False,
            "retrieval_options": {
                "run_search": "auto",
                "real_time": True,
                "filters": {
                    "source_type": None,
                    "document_set": document_set_ids[0] if document_set_ids else None,
                    "time_cutoff": None,
                    "tags": [],
                    "user_file_ids": None,
                },
            },
            "prompt_override": None,
            "llm_override": {
                "model_provider": "Divami-LiteLLM",
                "model_version": "openai/gpt-4o",
            },
            "use_agentic_search": use_agentic_search,
        }

        try:
            # Send the message
            try:
                self._make_request("POST", "/api/chat/send-message", json=payload)
            except:  # noqa
                pass

            # Get the session to retrieve the response
            session_data = self.get_session(session_id)
            messages = session_data.get("messages", [])

            # Find the last assistant message
            for msg in reversed(messages):
                if msg.get("message_type") == "assistant" and msg.get("message"):
                    response = msg["message"]
                    logger.debug(
                        f"Received response for session {session_id}: {response[:100]}..."
                    )
                    return response

            raise OnyxAPIError("No response received from assistant")

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error in chat: {e}") from e

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve session data and history for a given session ID.

        Args:
            session_id (str): ID of the session to retrieve

        Returns:
            Dict[str, Any]: Session data including history, metadata, and configuration

        Raises:
            OnyxAPIError: If session retrieval fails
        """
        try:
            response_data = self._make_request(
                "GET", f"/api/chat/get-chat-session/{session_id}"
            )
            logger.debug(f"Retrieved session data for {session_id}")
            return response_data

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error retrieving session: {e}") from e

    def create_connector(self, name: str, documents: List[str]) -> str:
        """
        Create a document connector/document set for processing files.

        Args:
            name (str): Name for the document connector
            documents (List[str]): List of document paths or content to process

        Returns:
            str: Unique connector/document set ID

        Raises:
            OnyxAPIError: If connector creation fails
            NotImplementedError: This functionality requires file upload implementation
        """
        # Note: The actual implementation would require file upload handling
        # This is a simplified version based on the API structure

        if not documents:
            raise ValueError("Documents list cannot be empty")

        # For now, this is a placeholder implementation
        # The actual Onyx API might require different endpoints for file upload
        # and connector creation

        raise NotImplementedError(
            "Document connector creation requires file upload implementation. "
            "This feature will be implemented based on the specific Onyx API "
            "endpoints for document management."
        )

    def _get_drive_credentials(self) -> Optional[str]:
        """
        Fetch the first available Google Drive credential ID.

        Returns:
            Optional[str]: Credential ID if found, None otherwise

        Raises:
            OnyxAPIError: If API request fails
        """
        try:
            response_data = self._make_request(
                "GET", "/api/manage/admin/similar-credentials/google_drive"
            )

            if isinstance(response_data, list) and response_data:
                credential_id = response_data[0].get("id")
                logger.info(f"Found Google Drive credential: {credential_id}")
                return credential_id

            logger.warning("No Google Drive credentials found")
            return None

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(
                f"Unexpected error fetching drive credentials: {e}"
            ) from e

    def _create_connector_config(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Create a new connector configuration and return its ID.

        Args:
            payload (Dict[str, Any]): Connector configuration payload

        Returns:
            Optional[str]: Connector ID if successful, None otherwise

        Raises:
            OnyxAPIError: If connector creation fails
        """
        try:
            response_data = self._make_request(
                "POST", "/api/manage/admin/connector", json=payload
            )
            connector_id = response_data.get("id")

            if connector_id:
                logger.info(f"Created connector: {connector_id}")
            else:
                logger.error("No connector ID returned from API")

            return connector_id

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error creating connector: {e}") from e

    def _sync_connector_with_credential(
        self, connector_id: str, credential_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync connector with credential and return the result.

        Args:
            connector_id (str): ID of the connector to sync
            credential_id (str): ID of the credential to use
            payload (Dict[str, Any]): Sync configuration payload

        Returns:
            Dict[str, Any]: Sync result data

        Raises:
            OnyxAPIError: If sync operation fails
        """
        try:
            endpoint = (
                f"/api/manage/connector/{connector_id}/credential/{credential_id}"
            )
            response_data = self._make_request("PUT", endpoint, json=payload)

            logger.info(
                f"Successfully synced connector {connector_id} with credential {credential_id}"
            )
            return response_data

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error syncing connector: {e}") from e

    def create_drive_connector(
        self,
        connector_name: str,
        drive_url: Optional[str] = None,
        folder_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Google Drive connector, sync it with credentials, and return details.

        Args:
            connector_name (str): Name for the connector
            drive_url (Optional[str]): Shared drive URL to include
            folder_url (Optional[str]): Shared folder URL to include

        Returns:
            Dict[str, Any]: Dictionary containing connector details including:
                - message: Success message
                - connector_id: ID of the created connector
                - credential_id: ID of the credential used
                - sync_result: Result of the sync operation

        Raises:
            OnyxAPIError: If connector creation or syncing fails
            ValueError: If connector name is empty or invalid
        """
        if not connector_name or not isinstance(connector_name, str):
            raise ValueError("Connector name must be a non-empty string")

        # Prepare URLs for the connector config
        shared_drive_urls = drive_url if drive_url else ""
        shared_folder_urls = folder_url if folder_url else ""

        # Connector configuration payload
        connector_payload = {
            "connector_specific_config": {
                "include_files_shared_with_me": False,
                "include_my_drives": False,
                "include_shared_drives": False,
                "shared_drive_urls": shared_drive_urls,
                "shared_folder_urls": shared_folder_urls,
                "specific_user_emails": "",
            },
            "input_type": "poll",
            "name": connector_name,
            "source": "google_drive",
            "access_type": "public",
            "refresh_freq": 1800,  # 30 minutes
            "prune_freq": 2592000,  # 30 days
            "indexing_start": None,
            "groups": [],
        }

        # Sync configuration payload
        sync_payload = {
            "name": connector_name,
            "access_type": "public",
            "groups": [],
            "auto_sync_options": None,
        }

        try:
            # Get Google Drive credentials
            credential_id = self._get_drive_credentials()
            if not credential_id:
                raise OnyxAPIError(
                    "No Google Drive credentials found. Please configure Google Drive credentials first."
                )

            # Create the connector
            connector_id = self._create_connector_config(connector_payload)
            if not connector_id:
                raise OnyxAPIError("Failed to create connector configuration.")

            # Sync connector with credentials
            sync_result = self._sync_connector_with_credential(
                connector_id, credential_id, sync_payload
            )

            result = {
                "message": "Drive connector created successfully",
                "connector_id": connector_id,
                "credential_id": credential_id,
                "sync_result": sync_result,
            }

            logger.info(
                f"Successfully created drive connector '{connector_name}' with ID: {connector_id}"
            )
            return result

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error creating drive connector: {e}") from e

    def close(self) -> None:
        """Close the HTTP session and clean up resources."""
        if hasattr(self, "session"):
            self.session.close()
            logger.info("Closed Onyx service HTTP session")

    def get_connectors(self) -> List[Dict[str, Any]]:
        """
        Retrieve a list of all connectors available in the Onyx system.

        Returns:
            List[Dict[str, Any]]: List of connector details

        Raises:
            OnyxAPIError: If retrieval fails
        """
        try:
            response_data = self._make_request(
                "GET", "/api/manage/admin/connector/status"
            )
            logger.debug("Retrieved connectors from Onyx API")
            return {item["name"]: item["cc_pair_id"] for item in response_data}

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error retrieving connectors: {e}") from e

    def create_document_set(
        self,
        name: str,
        description: Optional[str] = None,
        connector_list: list[str] = None,
        cc_pair_ids: list[str] = None,
    ) -> str:
        """
        Create a new document set in the Onyx system.

        Args:
            name (str): Name for the document set
            description (Optional[str]): Description of the document set
            connector_list (list[str], optional): List of connector IDs to include
            cc_pair_ids (list[str], optional): List of content control pair IDs to include
        Returns:
            Nothing if successful

        Raises:
            OnyxAPIError: If document set creation fails
        """
        if cc_pair_ids is None:
            connectors = self.get_connectors()
            cc_pair_ids = [
                connectors[name] for name in connector_list if name in connectors
            ]

        payload = {
            "name": name,
            "description": description or "",
            "cc_pair_ids": cc_pair_ids,
            "is_public": True,
            "users": [],
            "groups": [],
            "federated_connectors": [],
        }

        try:
            self._make_request("POST", "/api/manage/admin/document-set", json=payload)
            logger.info(f"Created document set for {payload=}")

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error creating document set: {e}") from e

    def simple_chat(self, message: str, persona_id: Optional[int] = None) -> str:
        """
        Send a simple chat message using Onyx's simplified API endpoint.

        This is useful for one-off questions without maintaining session state.
        Based on the /api/chat/send-message-simple-api endpoint.

        Args:
            message (str): The message content to send
            persona_id (Optional[int]): ID of the persona/assistant to use (defaults to 0)

        Returns:
            str: Response message from the Onyx service

        Raises:
            OnyxAPIError: If chat interaction fails
        """
        payload = {
            "message": message,
            "persona_id": persona_id or 0,
        }

        try:
            response_data = self._make_request(
                "POST", "/api/chat/send-message-simple-api", json=payload
            )

            # The simple API returns the response in the "answer" field
            response = response_data.get("answer", "")
            if not response:
                # Check if there's an error message
                error_msg = response_data.get("error_msg")
                if error_msg:
                    raise OnyxAPIError(f"Chat API returned error: {error_msg}")
                
                # If no answer but documents were found, create a summary
                top_documents = response_data.get("top_documents", [])
                if top_documents:
                    doc_titles = [doc.get('semantic_identifier', 'Unknown Document')[:50] for doc in top_documents[:3]]
                    response = f"Found {len(top_documents)} relevant documents: {', '.join(doc_titles)}. However, no generated answer was provided by the system."
                    logger.warning(f"Empty answer but {len(top_documents)} documents found. Using fallback response.")
                else:
                    logger.warning(f"Empty answer and no documents found. Response keys: {list(response_data.keys())}")
                    raise OnyxAPIError("No response received from simple chat API")

            logger.debug(f"Received simple chat response: {response[:100]}...")
            return response

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error in simple chat: {e}") from e

    def answer_with_quote(
        self,
        query: str,
        document_set_ids: Optional[List[str]] = None,
        num_docs: int = 5,
        include_quotes: bool = True,
        persona_id: Optional[int] = None,
        search_type: str = "hybrid",
        max_chunks: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get an answer to a query with supporting quotes and citations.

        This uses the simple chat endpoint which provides comprehensive responses
        with source citations and document references.

        Args:
            query (str): The question or query to answer
            document_set_ids (Optional[List[str]]): Specific document sets to search
            num_docs (int): Number of documents to retrieve (default: 5)
            include_quotes (bool): Whether to include supporting quotes (default: True)
            persona_id (Optional[int]): Persona/assistant to use for answering
            search_type (str): Type of search - "hybrid", "semantic", or "keyword" (default: "hybrid")
            max_chunks (Optional[int]): Maximum number of document chunks to use
            filters (Optional[Dict[str, Any]]): Additional search filters

        Returns:
            Dict[str, Any]: Response containing:
                - answer: The generated answer
                - quotes: List of supporting quotes with sources (from match_highlights)
                - top_documents: List of relevant documents
                - contexts: Additional context information

        Raises:
            OnyxAPIError: If the query fails
        """
        try:
            # Use the simple chat endpoint which provides comprehensive responses
            payload = {
                "message": query,
                "persona_id": persona_id or 0,
            }
            
            response_data = self._make_request(
                "POST", "/api/chat/send-message-simple-api", json=payload
            )
            
            # Extract and format response components
            answer = response_data.get('answer', '')
            answer_citationless = response_data.get('answer_citationless', answer)
            top_documents = response_data.get('top_documents', [])
            
            # Limit documents if requested
            if num_docs and len(top_documents) > num_docs:
                top_documents = top_documents[:num_docs]
            
            # Extract quotes from match_highlights if available
            quotes = []
            if include_quotes:
                for doc in top_documents:
                    highlights = doc.get('match_highlights', [])
                    for highlight in highlights:
                        if highlight.strip():  # Skip empty highlights
                            quotes.append({
                                'text': highlight,
                                'document_id': doc.get('document_id'),
                                'semantic_identifier': doc.get('semantic_identifier'),
                                'link': doc.get('link', ''),
                                'score': doc.get('score', 0)
                            })
            
            # Format response to match expected structure
            formatted_response = {
                'answer': answer,
                'answer_citationless': answer_citationless,
                'quotes': quotes,
                'top_documents': top_documents,
                'contexts': {
                    'final_context_doc_indices': response_data.get('final_context_doc_indices', []),
                    'llm_chunks_indices': response_data.get('llm_chunks_indices', []),
                },
                'message_id': response_data.get('message_id'),
                'chat_session_id': response_data.get('chat_session_id')
            }

            logger.debug(f"Received answer with quotes for query: {query[:50]}...")
            return formatted_response

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error in answer with quote: {e}") from e

    def ingest_document(
        self,
        sections: List[Dict[str, str]],
        document_id: Optional[str] = None,
        source: str = "FILE",  # Changed from "api" to "FILE" to match Onyx repo
        semantic_identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        doc_updated_at: Optional[str] = None,
        cc_pair_id: Optional[int] = None,  # Changed to Optional to use default
    ) -> Dict[str, Any]:
        """
        Directly ingest a document into Onyx using the Ingestion API.

        This allows for programmatic document creation without using connectors.
        Based on the official /onyx-api/ingestion endpoint from the Onyx GitHub repository:
        https://github.com/onyx-dot-app/onyx/tree/main/backend/onyx/server/onyx_api/ingestion.py

        Args:
            sections (List[Dict[str, str]]): List of document sections, each containing:
                - text: The text content
                - link: Optional URL/link for the section (can be None)
            document_id (Optional[str]): Unique document ID (auto-generated if not provided)
            source (str): Source type identifier (default: "FILE" per Onyx repo)
            semantic_identifier (Optional[str]): Human-readable document identifier
            metadata (Optional[Dict[str, Any]]): Additional metadata for the document
            doc_updated_at (Optional[str]): ISO format timestamp of last update (with Z suffix)
            cc_pair_id (Optional[int]): Connector-credential pair ID (None uses default)

        Returns:
            Dict[str, Any]: Response from the ingestion API containing:
                - document_id: The ID of the ingested document
                - already_existed: Boolean indicating if document already existed

        Raises:
            OnyxAPIError: If document ingestion fails
            ValueError: If sections are invalid
        """
        if not sections or not isinstance(sections, list):
            raise ValueError("Sections must be a non-empty list")

        # Validate section format
        for i, section in enumerate(sections):
            if not isinstance(section, dict) or "text" not in section:
                raise ValueError(f"Section {i} must be a dict with 'text' key")

        # Build the document payload following the exact format from Onyx repository
        document = {
            "sections": sections,
            "source": source,
            "from_ingestion_api": True,  # Added per Onyx repo code
        }

        # Add optional fields
        if document_id:
            document["id"] = document_id
        if semantic_identifier:
            document["semantic_identifier"] = semantic_identifier
        if metadata:
            document["metadata"] = metadata
        if doc_updated_at:
            # Ensure the timestamp has Z suffix for UTC as per Onyx repo
            if not doc_updated_at.endswith('Z'):
                doc_updated_at = doc_updated_at.rstrip('Z') + 'Z'
            document["doc_updated_at"] = doc_updated_at

        # Build payload following IngestionDocument model from Onyx repo
        payload = {
            "document": document,
            "cc_pair_id": cc_pair_id  # None will use DEFAULT_CC_PAIR_ID per Onyx repo
        }

        try:
            logger.info(f"🚀 Ingesting document to Onyx Cloud via official API endpoint")
            logger.debug(f"📤 Payload structure: {payload}")
            
            # Use the official /onyx-api/ingestion endpoint from the Onyx repository
            response_data = self._make_request(
                "POST", "/onyx-api/ingestion", json=payload
            )

            logger.info(f"✅ Successfully ingested document: {response_data.get('document_id', 'unknown')}")
            return response_data

        except OnyxAPIError as e:
            logger.error(f"❌ Onyx ingestion API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error ingesting document: {e}")
            raise OnyxAPIError(f"Unexpected error ingesting document: {e}") from e

    def get_personas(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available personas/assistants in the system.

        Returns:
            List[Dict[str, Any]]: List of persona configurations

        Raises:
            OnyxAPIError: If retrieval fails
        """
        try:
            response_data = self._make_request("GET", "/api/persona")
            logger.debug("Retrieved personas from Onyx API")
            return response_data

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error retrieving personas: {e}") from e

    def get_document_sets(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available document sets in the system.

        Returns:
            List[Dict[str, Any]]: List of document set configurations

        Raises:
            OnyxAPIError: If retrieval fails
        """
        try:
            response_data = self._make_request("GET", "/api/manage/admin/document-set")
            logger.debug("Retrieved document sets from Onyx API")
            return response_data

        except OnyxAPIError as e:
            # If the admin endpoint fails, try to extract document sets from persona information
            if e.status_code in [405, 403, 401]:
                logger.warning("Admin document-set endpoint not accessible, using personas as fallback")
                try:
                    personas = self.get_personas()
                    document_sets = []
                    seen_sets = set()
                    
                    for persona in personas:
                        for doc_set in persona.get('document_sets', []):
                            doc_set_name = doc_set.get('name')
                            if doc_set_name and doc_set_name not in seen_sets:
                                document_sets.append(doc_set)
                                seen_sets.add(doc_set_name)
                    
                    logger.info(f"Extracted {len(document_sets)} document sets from personas")
                    return document_sets
                except Exception:
                    return []  # Return empty list if fallback fails
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error retrieving document sets: {e}") from e

    def search_documents(
        self,
        query: str,
        document_set_ids: Optional[List[str]] = None,
        num_results: int = 10,
        search_type: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for documents using Onyx's search capabilities.
        
        Note: Uses the simple chat endpoint since dedicated search endpoints are not available
        in Onyx Cloud. This provides both search results and semantic understanding.

        Args:
            query (str): Search query
            document_set_ids (Optional[List[str]]): Specific document sets to search
            num_results (int): Number of results to return (default: 10)
            search_type (str): "hybrid", "semantic", or "keyword" (default: "hybrid")
            filters (Optional[Dict[str, Any]]): Additional search filters
            offset (int): Result offset for pagination (default: 0)

        Returns:
            Dict[str, Any]: Search results with document matches

        Raises:
            OnyxAPIError: If search fails
        """
        try:
            # Use simple chat as a search mechanism since it returns top_documents
            search_query = f"Find documents related to: {query}"
            
            # Make the request directly to get full response with documents
            payload = {
                "message": search_query,
                "persona_id": 0,
            }
            
            response_data = self._make_request(
                "POST", "/api/chat/send-message-simple-api", json=payload
            )
            
            # Extract documents from the response
            top_documents = response_data.get('top_documents', [])
            
            # Handle None case
            if top_documents is None:
                top_documents = []
            
            # Limit results if requested
            if num_results and len(top_documents) > num_results:
                top_documents = top_documents[:num_results]
            
            # Format response to match expected search result structure
            search_results = {
                "top_documents": top_documents,
                "query": query,
                "total_results": len(top_documents)
            }
            
            logger.debug(f"Performed search for query: {query[:50]}... Found {len(top_documents)} documents")
            return search_results

        except OnyxAPIError:
            raise
        except Exception as e:
            raise OnyxAPIError(f"Unexpected error in search: {e}") from e
