"""Main Mia21 client implementation."""

import requests
import json
import uuid
from typing import Optional, List, Generator, Dict, Any
from .models import ChatMessage, Space, InitializeResponse, ChatResponse
from .exceptions import Mia21Error, ChatNotInitializedError, APIError


class Mia21Client:
    """
    Mia21 Chat API Client
    
    Example:
        >>> from mia21 import Mia21Client
        >>> client = Mia21Client(api_key="your-api-key")
        >>> client.initialize()
        >>> response = client.chat("Hello!")
        >>> print(response.message)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.mia21.com",
        user_id: Optional[str] = None,
        timeout: int = 90
    ):
        """
        Initialize Mia21 client.
        
        Args:
            api_key: Your Mia21 API key
            base_url: API base URL (default: production)
            user_id: Unique user identifier (auto-generated if not provided)
            timeout: Request timeout in seconds (default: 90)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.user_id = user_id or str(uuid.uuid4())
        self.timeout = timeout
        self.current_space = None
        self._session = requests.Session()
        self._session.headers.update({
            "x-api-key": api_key,
            "Content-Type": "application/json"
        })
    
    def list_spaces(self) -> List[Space]:
        """
        List all available spaces.
        
        Returns:
            List of Space objects
            
        Example:
            >>> spaces = client.list_spaces()
            >>> for space in spaces:
            ...     print(f"{space.id}: {space.name}")
        """
        try:
            response = self._session.post(
                f"{self.api_url}/list_spaces",
                json={"app_id": self.user_id},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return [Space(**s) for s in data.get("spaces", [])]
        except requests.RequestException as e:
            raise APIError(f"Failed to list spaces: {e}")
    
    def initialize(
        self,
        space_id: str = "dr_panda",
        llm_type: str = "openai",
        user_name: Optional[str] = None,
        language: Optional[str] = None,
        generate_first_message: bool = True,
        incognito_mode: bool = False
    ) -> InitializeResponse:
        """
        Initialize a chat session.
        
        Args:
            space_id: Space to use (default: "dr_panda")
            llm_type: "openai" or "gemini"
            user_name: User's display name
            language: Force language (e.g., "es", "de")
            generate_first_message: Generate AI greeting
            incognito_mode: Privacy mode (no data saved)
            
        Returns:
            InitializeResponse with first message
            
        Example:
            >>> response = client.initialize(space_id="customer_support")
            >>> print(response.message)
            "Hello! How can I help you today?"
        """
        try:
            response = self._session.post(
                f"{self.api_url}/initialize_chat",
                json={
                    "app_id": self.user_id,
                    "space_id": space_id,
                    "llm_type": llm_type,
                    "user_name": user_name,
                    "language": language,
                    "generate_first_message": generate_first_message,
                    "incognito_mode": incognito_mode
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            self.current_space = space_id
            return InitializeResponse(**data)
        except requests.RequestException as e:
            raise APIError(f"Failed to initialize chat: {e}")
    
    def chat(
        self,
        message: str,
        space_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """
        Send a message and get a response.
        
        Args:
            message: User message
            space_id: Which space to chat with (uses current if not specified)
            temperature: Override temperature (0.0-2.0)
            max_tokens: Override max tokens
            
        Returns:
            ChatResponse with AI message
            
        Example:
            >>> response = client.chat("I'm feeling anxious today")
            >>> print(response.message)
        """
        if not self.current_space and not space_id:
            raise ChatNotInitializedError("Chat not initialized. Call initialize() first.")
        
        try:
            response = self._session.post(
                f"{self.api_url}/chat",
                json={
                    "app_id": self.user_id,
                    "space_id": space_id or self.current_space,
                    "messages": [{"role": "user", "content": message}],
                    "llm_type": "openai",
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return ChatResponse(**data)
        except requests.RequestException as e:
            raise APIError(f"Failed to send message: {e}")
    
    def stream_chat(
        self,
        message: str,
        space_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Send a message and stream the response in real-time.
        
        Args:
            message: User message
            space_id: Which space to chat with
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Yields:
            Text chunks as they arrive
            
        Example:
            >>> for chunk in client.stream_chat("Tell me a story"):
            ...     print(chunk, end='', flush=True)
        """
        if not self.current_space and not space_id:
            raise ChatNotInitializedError("Chat not initialized. Call initialize() first.")
        
        try:
            response = self._session.post(
                f"{self.api_url}/chat/stream",
                json={
                    "app_id": self.user_id,
                    "space_id": space_id or self.current_space,
                    "messages": [{"role": "user", "content": message}],
                    "llm_type": "openai",
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                },
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = json.loads(line_text[6:])
                        
                        if 'error' in data and data['error']:
                            raise APIError(f"Streaming error: {data['error']}")
                        
                        if 'content' in data:
                            yield data['content']
                        
                        if data.get('done'):
                            break
        except requests.RequestException as e:
            raise APIError(f"Failed to stream message: {e}")
    
    def close(self, space_id: Optional[str] = None):
        """
        Close chat session and save conversation.
        
        Args:
            space_id: Which space to close (current if not specified)
            
        Example:
            >>> client.close()
        """
        try:
            response = self._session.post(
                f"{self.api_url}/close_chat",
                json={
                    "app_id": self.user_id,
                    "space_id": space_id or self.current_space
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise APIError(f"Failed to close chat: {e}")
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-close on context exit."""
        if self.current_space:
            try:
                self.close()
            except:
                pass

