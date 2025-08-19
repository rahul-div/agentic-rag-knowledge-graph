"""
Abstract base interface for Onyx integration with dependency injection support.

This module defines the contract that all Onyx service implementations must follow,
enabling dependency injection and facilitating testing with mock implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class OnyxInterface(ABC):
    """
    Abstract base class defining the interface for Onyx service implementations.

    This interface supports dependency injection patterns and provides a contract
    for both real and mock implementations of Onyx API interactions.

    Attributes:
        api_key (str): API key for authentication with Onyx services
    """

    def __init__(self, api_key: str):
        """
        Initialize the Onyx interface with an API key.

        Args:
            api_key (str): The API key for authenticating with Onyx services
        """
        self.api_key = api_key

    @abstractmethod
    def create_chat_session(self, document_set_id: Optional[str] = None) -> str:
        """
        Create a new chat session with optional document set targeting.

        Args:
            document_set_id (Optional[str]): ID of the document set to target for this session

        Returns:
            str: Unique session ID for the created chat session

        Raises:
            Exception: If session creation fails
        """
        pass

    @abstractmethod
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
            Exception: If chat interaction fails or session doesn't exist
        """
        pass

    @abstractmethod
    def simple_chat(self, message: str, persona_id: Optional[int] = None) -> str:
        """
        Send a simple chat message without maintaining session state.

        Args:
            message (str): The message content to send
            persona_id (Optional[int]): ID of the persona/assistant to use

        Returns:
            str: Response message from the Onyx service

        Raises:
            Exception: If chat interaction fails
        """
        pass

    @abstractmethod
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

        Args:
            query (str): The question or query to answer
            document_set_ids (Optional[List[str]]): Specific document sets to search
            num_docs (int): Number of documents to retrieve
            include_quotes (bool): Whether to include supporting quotes
            persona_id (Optional[int]): Persona/assistant to use for answering
            search_type (str): Type of search - "hybrid", "semantic", or "keyword"
            max_chunks (Optional[int]): Maximum number of document chunks to use
            filters (Optional[Dict[str, Any]]): Additional search filters

        Returns:
            Dict[str, Any]: Response with answer, quotes, and source documents

        Raises:
            Exception: If the query fails
        """
        pass

    @abstractmethod
    def ingest_document(
        self,
        sections: List[Dict[str, str]],
        document_id: Optional[str] = None,
        source: str = "api",
        semantic_identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        doc_updated_at: Optional[str] = None,
        cc_pair_id: int = 1,
    ) -> Dict[str, Any]:
        """
        Directly ingest a document into Onyx using the Ingestion API.

        Args:
            sections (List[Dict[str, str]]): List of document sections
            document_id (Optional[str]): Unique document ID
            source (str): Source type identifier
            semantic_identifier (Optional[str]): Human-readable document identifier
            metadata (Optional[Dict[str, Any]]): Additional metadata
            doc_updated_at (Optional[str]): ISO format timestamp of last update
            cc_pair_id (int): Connector-credential pair ID

        Returns:
            Dict[str, Any]: Response from the ingestion API

        Raises:
            Exception: If document ingestion fails
        """
        pass

    @abstractmethod
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

        Args:
            query (str): Search query
            document_set_ids (Optional[List[str]]): Specific document sets to search
            num_results (int): Number of results to return
            search_type (str): "hybrid", "semantic", or "keyword"
            filters (Optional[Dict[str, Any]]): Additional search filters
            offset (int): Result offset for pagination

        Returns:
            Dict[str, Any]: Search results with document matches

        Raises:
            Exception: If search fails
        """
        pass

    @abstractmethod
    def get_personas(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available personas/assistants in the system.

        Returns:
            List[Dict[str, Any]]: List of persona configurations

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_document_sets(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available document sets in the system.

        Returns:
            List[Dict[str, Any]]: List of document set configurations

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def verify_cc_pair_status(self, cc_pair_id: int) -> bool:
        """
        Verify CC-pair status and readiness for search.

        Args:
            cc_pair_id (int): CC-pair ID to verify

        Returns:
            bool: True if CC-pair is ready for search

        Raises:
            Exception: If verification fails
        """
        pass

    @abstractmethod
    def create_document_set_validated(
        self, cc_pair_id: int, name: str, description: str = ""
    ) -> Optional[int]:
        """
        Create document set using validated endpoints with fallback logic.

        Args:
            cc_pair_id (int): CC-pair ID to include in document set
            name (str): Name for the document set
            description (str): Description for the document set

        Returns:
            Optional[int]: Document set ID if successful, None if failed

        Raises:
            Exception: If creation fails
        """
        pass

    @abstractmethod
    def search_with_document_set_validated(
        self, query: str, document_set_id: int, max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute search with document set restriction using validated implementation.

        Args:
            query (str): Search query
            document_set_id (int): Document set ID to restrict search to
            max_retries (int): Maximum number of retry attempts

        Returns:
            Dict[str, Any]: Search results with success status, answer, and source documents

        Raises:
            Exception: If search fails
        """
        pass


class MockOnyxService(OnyxInterface):
    """
    Mock implementation of OnyxInterface for testing purposes.

    This implementation provides realistic mock responses and maintains
    in-memory storage for sessions and connectors without requiring
    actual API calls to Onyx services.
    """

    def __init__(self, api_key: str = "mock_api_key"):
        """
        Initialize the mock service with optional API key.

        Args:
            api_key (str): Mock API key (defaults to "mock_api_key")
        """
        super().__init__(api_key)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._connectors: Dict[str, Dict[str, Any]] = {}
        self._session_counter = 0
        self._connector_counter = 0
        self._response_behaviors: Dict[str, Any] = {}

    def configure_response_behavior(
        self, behavior_type: str, config: Dict[str, Any]
    ) -> None:
        """
        Configure specific response behaviors for testing scenarios.

        Args:
            behavior_type (str): Type of behavior to configure (e.g., "chat_error", "delay")
            config (Dict[str, Any]): Configuration for the behavior
        """
        self._response_behaviors[behavior_type] = config

    def create_chat_session(self, document_set_id: Optional[str] = None) -> str:
        """
        Create a mock chat session with in-memory storage.

        Args:
            document_set_id (Optional[str]): ID of the document set to target

        Returns:
            str: Mock session ID in format "mock_session_N"
        """
        self._session_counter += 1
        session_id = f"mock_session_{self._session_counter}"

        self._sessions[session_id] = {
            "id": session_id,
            "document_set_id": document_set_id,
            "messages": [],
            "created_at": "2025-07-13T00:00:00Z",
            "status": "active",
        }

        return session_id

    def chat(
        self,
        session_id: str,
        message: str,
        document_set_ids: Optional[List[str]] = None,
        persona_id: Optional[int] = None,
        use_agentic_search: bool = False,
    ) -> str:
        """
        Send a message to a mock chat session and generate a realistic response.

        Args:
            session_id (str): ID of the session to send message to
            message (str): The message content to send
            document_set_ids (Optional[List[str]]): List of document set IDs to target
            persona_id (Optional[int]): Override the default persona for this message
            use_agentic_search (bool): Whether to use agentic search capabilities

        Returns:
            str: Mock response based on message content

        Raises:
            ValueError: If session doesn't exist
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        # Check for configured error behaviors
        if "chat_error" in self._response_behaviors:
            raise Exception("Mock chat error configured")

        # Store the message
        self._sessions[session_id]["messages"].append(
            {"type": "user", "content": message, "timestamp": "2025-07-13T00:00:00Z"}
        )

        # Generate contextual mock responses
        if "topic" in message.lower():
            response = "Based on the documents, I've identified the following topics: AI, Machine Learning, Data Science, Natural Language Processing."
        elif "question" in message.lower():
            response = """Here are some questions based on the content:
1. What is machine learning? - Machine learning is a subset of AI that enables systems to learn from data.
2. How does NLP work? - NLP combines computational linguistics with machine learning to help computers understand human language."""
        elif "assess" in message.lower():
            response = "The answer is correct. The user demonstrates good understanding of the concept."
        else:
            response = f"This is a mock response to: {message[:50]}..."

        # Store the response
        self._sessions[session_id]["messages"].append(
            {
                "type": "assistant",
                "content": response,
                "timestamp": "2025-07-13T00:00:00Z",
            }
        )

        return response

    def simple_chat(self, message: str, persona_id: Optional[int] = None) -> str:
        """
        Send a simple chat message and return a mock response.

        Args:
            message (str): The message content to send
            persona_id (Optional[int]): ID of the persona/assistant to use

        Returns:
            str: Mock response message

        Raises:
            Exception: If an error occurs during processing
        """
        # Check for configured error behaviors
        if "chat_error" in self._response_behaviors:
            raise Exception("Mock chat error configured")

        # Generate a simple mock response
        response = f"Simple mock response to: {message}"

        return response

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
        Generate a mock answer to a query, with optional quotes and citations.

        Args:
            query (str): The question or query to answer
            document_set_ids (Optional[List[str]]): Specific document sets to search
            num_docs (int): Number of documents to retrieve
            include_quotes (bool): Whether to include supporting quotes
            persona_id (Optional[int]): Persona/assistant to use for answering
            search_type (str): Type of search - "hybrid", "semantic", or "keyword"
            max_chunks (Optional[int]): Maximum number of document chunks to use
            filters (Optional[Dict[str, Any]]): Additional search filters

        Returns:
            Dict[str, Any]: Mock response with answer, quotes, and source documents

        Raises:
            Exception: If the query fails
        """
        # Mocked response construction
        answer = "This is a mock answer to your query."
        quotes = [
            {"quote": "Mocked quote 1", "source": "Document 1"},
            {"quote": "Mocked quote 2", "source": "Document 2"},
        ]

        response = {
            "answer": answer,
            "quotes": quotes if include_quotes else [],
            "document_set_ids": document_set_ids or [],
            "num_docs": num_docs,
        }

        return response

    def ingest_document(
        self,
        sections: List[Dict[str, str]],
        document_id: Optional[str] = None,
        source: str = "api",
        semantic_identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        doc_updated_at: Optional[str] = None,
        cc_pair_id: int = 1,
    ) -> Dict[str, Any]:
        """
        Mock the ingestion of a document, simulating API behavior.

        Args:
            sections (List[Dict[str, str]]): List of document sections
            document_id (Optional[str]): Unique document ID
            source (str): Source type identifier
            semantic_identifier (Optional[str]): Human-readable document identifier
            metadata (Optional[Dict[str, Any]]): Additional metadata
            doc_updated_at (Optional[str]): ISO format timestamp of last update
            cc_pair_id (int): Connector-credential pair ID

        Returns:
            Dict[str, Any]: Mock response from the ingestion API

        Raises:
            Exception: If document ingestion fails
        """
        # Simulate document ingestion logic
        if not sections or len(sections) == 0:
            raise Exception("No sections provided for ingestion")

        # Mocked successful ingestion response
        response = {
            "status": "success",
            "document_id": document_id or "mock_document_id",
            "ingested_at": "2025-07-13T00:00:00Z",
            "source": source,
            "metadata": metadata or {},
            "doc_updated_at": doc_updated_at or "2025-07-13T00:00:00Z",
            "cc_pair_id": cc_pair_id,
        }

        return response

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
        Mock the search functionality, returning simulated document matches.

        Args:
            query (str): Search query
            document_set_ids (Optional[List[str]]): Specific document sets to search
            num_results (int): Number of results to return
            search_type (str): "hybrid", "semantic", or "keyword"
            filters (Optional[Dict[str, Any]]): Additional search filters
            offset (int): Result offset for pagination

        Returns:
            Dict[str, Any]: Mock search results with document matches

        Raises:
            Exception: If search fails
        """
        # Simulate search logic
        if not query or len(query) == 0:
            raise Exception("Empty query string")

        # Mocked search results
        results = [
            {
                "document_id": "doc1",
                "score": 0.9,
                "snippet": "This is a snippet from document 1.",
            },
            {
                "document_id": "doc2",
                "score": 0.85,
                "snippet": "This is a snippet from document 2.",
            },
        ]

        # Mocked successful search response
        response = {
            "query": query,
            "document_set_ids": document_set_ids or [],
            "num_results": num_results,
            "offset": offset,
            "results": results[:num_results],
        }

        return response

    def get_personas(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available personas/assistants in the system.

        Returns:
            List[Dict[str, Any]]: List of persona configurations

        Raises:
            Exception: If retrieval fails
        """
        # Mocked persona list
        return [
            {"id": 1, "name": "Default Persona", "description": "The standard persona"},
            {
                "id": 2,
                "name": "Expert Persona",
                "description": "A persona with expert knowledge",
            },
        ]

    def get_document_sets(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available document sets in the system.

        Returns:
            List[Dict[str, Any]]: List of document set configurations

        Raises:
            Exception: If retrieval fails
        """
        # Mocked document set list
        return [
            {
                "id": "set1",
                "name": "Document Set 1",
                "description": "The first set of documents",
            },
            {
                "id": "set2",
                "name": "Document Set 2",
                "description": "The second set of documents",
            },
        ]

    def get_connectors(self) -> Dict[str, str]:
        """
        Retrieve all available connectors in the system (mock implementation).

        Returns:
            Dict[str, str]: Dictionary mapping connector names to cc_pair_ids

        Raises:
            Exception: If retrieval fails
        """
        # Mocked connector list
        return {
            "Google Drive Connector": "cc_pair_1",
            "Slack Connector": "cc_pair_2",
            "GitHub Connector": "cc_pair_3",
        }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve mock session data and history for a given session ID.

        Args:
            session_id (str): ID of the session to retrieve

        Returns:
            Dict[str, Any]: Session data including history, metadata, and configuration

        Raises:
            ValueError: If session doesn't exist
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        return self._sessions[session_id]

    def create_connector(self, name: str, documents: List[str]) -> str:
        """
        Create a mock document connector for testing purposes.

        Args:
            name (str): Name for the document connector
            documents (List[str]): List of document paths or content to process

        Returns:
            str: Mock connector ID in format "mock_connector_N"

        Raises:
            ValueError: If name is empty or documents list is empty
        """
        if not name:
            raise ValueError("Connector name cannot be empty")
        if not documents:
            raise ValueError("Documents list cannot be empty")

        self._connector_counter += 1
        connector_id = f"mock_connector_{self._connector_counter}"

        self._connectors[connector_id] = {
            "id": connector_id,
            "name": name,
            "documents": documents,
            "created_at": "2025-07-13T00:00:00Z",
            "status": "active",
        }

        return connector_id

    def reset(self) -> None:
        """Reset all mock data for clean test states."""
        self._sessions.clear()
        self._connectors.clear()
        self._session_counter = 0
        self._connector_counter = 0
        self._response_behaviors.clear()
