from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Protocol, runtime_checkable
from dataclasses import dataclass
from enum import Enum
import asyncio

@dataclass
class ToolResult:
    """Standardized tool execution result"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def __str__(self) -> str:
        return str(self.data) if self.success else f"Error: {self.error}"

@dataclass
class AgentResponse:
    """Standardized agent response"""
    content: str
    tools_used: List[str] = None
    tool_outputs: List[tuple] = None
    thinking: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.tool_outputs is None:
            self.tool_outputs = []
        if self.metadata is None:
            self.metadata = {}

@runtime_checkable
class LLMProvider(Protocol):
    """Interface for LLM providers"""
    def generate(self, prompt: str, **kwargs) -> str: ...
    async def generate_async(self, prompt: str, **kwargs) -> str: ...
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str: ...
    async def chat_async(self, messages: List[Dict[str, str]], **kwargs) -> str: ...

@runtime_checkable
class EmbeddingProvider(Protocol):
    """Interface for embedding providers"""
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]: ...
    def get_dimension(self) -> int: ...

@runtime_checkable
class Tool(Protocol):
    """Interface for tools"""
    name: str
    description: str
    
    def execute(self, args: Dict[str, Any]) -> ToolResult: ...
    async def execute_async(self, args: Dict[str, Any]) -> ToolResult: ...
    def to_dict(self) -> Dict[str, Any]: ...

@runtime_checkable
class Memory(Protocol):
    """Interface for memory management"""
    def add_turn(self, query: str, response: str, tool_used: Optional[str] = None, 
                tool_output: Optional[str] = None) -> None: ...
    def get_context(self, max_context_turns: Optional[int] = None) -> str: ...
    def clear(self) -> None: ...
    def get_history(self) -> List[Dict[str, Any]]: ...

# Exceptions
class AiccelError(Exception):
    """Base exception for aiccel framework"""
    pass

class AgentError(AiccelError):
    """Agent execution errors"""
    pass

class ToolExecutionError(AiccelError):
    """Tool execution errors"""
    pass

class LLMError(AiccelError):
    """LLM provider errors"""
    pass

class MemoryError(AiccelError):
    """Memory management errors"""
    pass