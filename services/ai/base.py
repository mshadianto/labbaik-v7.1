"""
LABBAIK AI v6.0 - Base AI Service Interface
===========================================
Abstract base classes for AI services with common functionality.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class MessageRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to API-compatible dictionary."""
        return {"role": self.role.value, "content": self.content}
    
    @classmethod
    def system(cls, content: str) -> "ChatMessage":
        """Create system message."""
        return cls(role=MessageRole.SYSTEM, content=content)
    
    @classmethod
    def user(cls, content: str) -> "ChatMessage":
        """Create user message."""
        return cls(role=MessageRole.USER, content=content)
    
    @classmethod
    def assistant(cls, content: str) -> "ChatMessage":
        """Create assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)


@dataclass
class ChatCompletionRequest:
    """Request for chat completion."""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    top_p: float = 1.0
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatCompletionResponse:
    """Response from chat completion."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    latency_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.usage.get("total_tokens", 0)
    
    @property
    def prompt_tokens(self) -> int:
        """Get prompt token count."""
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        """Get completion token count."""
        return self.usage.get("completion_tokens", 0)


@dataclass
class EmbeddingRequest:
    """Request for text embedding."""
    texts: List[str]
    model: Optional[str] = None


@dataclass
class EmbeddingResponse:
    """Response from embedding service."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]
    latency_ms: float


# =============================================================================
# ABSTRACT BASE CLASSES
# =============================================================================

class BaseAIService(ABC):
    """Abstract base class for AI services."""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self._initialized = False
        self._config = kwargs
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service."""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
    
    def _ensure_initialized(self):
        """Ensure service is initialized before use."""
        if not self._initialized:
            self.initialize()


class BaseChatService(BaseAIService):
    """Abstract base class for chat completion services."""
    
    @abstractmethod
    def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Generate chat completion."""
        pass
    
    @abstractmethod
    def stream(self, request: ChatCompletionRequest) -> Generator[str, None, None]:
        """Generate streaming chat completion."""
        pass
    
    @abstractmethod
    async def acomplete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Async chat completion."""
        pass
    
    @abstractmethod
    async def astream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """Async streaming chat completion."""
        pass
    
    def simple_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Simple interface for chat completion."""
        messages = []
        if system_prompt:
            messages.append(ChatMessage.system(system_prompt))
        messages.append(ChatMessage.user(prompt))
        
        request = ChatCompletionRequest(messages=messages, **kwargs)
        response = self.complete(request)
        return response.content


class BaseEmbeddingService(BaseAIService):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    async def aembed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Async embedding generation."""
        pass
    
    def embed_text(self, text: str) -> List[float]:
        """Simple interface for single text embedding."""
        request = EmbeddingRequest(texts=[text])
        response = self.embed(request)
        return response.embeddings[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Simple interface for multiple text embeddings."""
        request = EmbeddingRequest(texts=texts)
        response = self.embed(request)
        return response.embeddings


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        requests_per_minute: int = 30,
        tokens_per_minute: int = 100000
    ):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self._request_timestamps: List[datetime] = []
        self._token_usage: List[tuple] = []  # (timestamp, tokens)
    
    def can_proceed(self, estimated_tokens: int = 0) -> tuple[bool, float]:
        """
        Check if request can proceed.
        
        Returns:
            Tuple of (can_proceed, wait_seconds)
        """
        now = datetime.utcnow()
        
        # Clean old entries (older than 1 minute)
        cutoff = now.timestamp() - 60
        self._request_timestamps = [
            ts for ts in self._request_timestamps 
            if ts.timestamp() > cutoff
        ]
        self._token_usage = [
            (ts, tokens) for ts, tokens in self._token_usage 
            if ts.timestamp() > cutoff
        ]
        
        # Check request limit
        if len(self._request_timestamps) >= self.requests_per_minute:
            oldest = min(self._request_timestamps)
            wait_time = 60 - (now.timestamp() - oldest.timestamp())
            return False, max(0, wait_time)
        
        # Check token limit
        total_tokens = sum(tokens for _, tokens in self._token_usage)
        if total_tokens + estimated_tokens > self.tokens_per_minute:
            oldest_ts, _ = min(self._token_usage, key=lambda x: x[0])
            wait_time = 60 - (now.timestamp() - oldest_ts.timestamp())
            return False, max(0, wait_time)
        
        return True, 0
    
    def record_request(self, tokens_used: int = 0):
        """Record a completed request."""
        now = datetime.utcnow()
        self._request_timestamps.append(now)
        if tokens_used > 0:
            self._token_usage.append((now, tokens_used))


# =============================================================================
# SERVICE FACTORY
# =============================================================================

class AIServiceFactory:
    """Factory for creating AI service instances with caching for performance."""

    _chat_services: Dict[str, type] = {}
    _embedding_services: Dict[str, type] = {}
    # PERFORMANCE: Cache service instances to avoid recreation
    _chat_instances: Dict[str, "BaseChatService"] = {}
    _embedding_instances: Dict[str, "BaseEmbeddingService"] = {}

    @classmethod
    def register_chat_service(cls, provider: str, service_class: type):
        """Register a chat service implementation."""
        cls._chat_services[provider.lower()] = service_class

    @classmethod
    def register_embedding_service(cls, provider: str, service_class: type):
        """Register an embedding service implementation."""
        cls._embedding_services[provider.lower()] = service_class

    @classmethod
    def create_chat_service(
        cls,
        provider: str,
        api_key: str,
        use_cache: bool = True,
        **kwargs
    ) -> BaseChatService:
        """Create a chat service instance (cached by default for performance)."""
        provider = provider.lower()
        if provider not in cls._chat_services:
            raise ValueError(f"Unknown chat service provider: {provider}")

        # Return cached instance if available and caching enabled
        cache_key = f"{provider}:{api_key[:8] if api_key else 'none'}"
        if use_cache and cache_key in cls._chat_instances:
            return cls._chat_instances[cache_key]

        service_class = cls._chat_services[provider]
        instance = service_class(api_key=api_key, **kwargs)

        if use_cache:
            cls._chat_instances[cache_key] = instance

        return instance

    @classmethod
    def create_embedding_service(
        cls,
        provider: str,
        api_key: str = "",
        use_cache: bool = True,
        **kwargs
    ) -> BaseEmbeddingService:
        """Create an embedding service instance (cached by default for performance)."""
        provider = provider.lower()
        if provider not in cls._embedding_services:
            raise ValueError(f"Unknown embedding service provider: {provider}")

        # Return cached instance if available and caching enabled
        cache_key = f"{provider}:{api_key[:8] if api_key else 'none'}"
        if use_cache and cache_key in cls._embedding_instances:
            return cls._embedding_instances[cache_key]

        service_class = cls._embedding_services[provider]
        instance = service_class(api_key=api_key, **kwargs)

        if use_cache:
            cls._embedding_instances[cache_key] = instance

        return instance

    @classmethod
    def clear_cache(cls):
        """Clear all cached service instances."""
        cls._chat_instances.clear()
        cls._embedding_instances.clear()
    
    @classmethod
    def available_chat_providers(cls) -> List[str]:
        """List available chat service providers."""
        return list(cls._chat_services.keys())
    
    @classmethod
    def available_embedding_providers(cls) -> List[str]:
        """List available embedding service providers."""
        return list(cls._embedding_services.keys())
