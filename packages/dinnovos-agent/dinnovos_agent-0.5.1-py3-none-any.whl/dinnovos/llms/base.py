"""Base LLM interface for Dinnovos Agent"""

from typing import List, Dict, Iterator, Optional, Any, Callable
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for all LLMs"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    def call(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        manage_context: bool = True,
        format: str = 'text',
        schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Abstract method that all interfaces must implement.
        
        Args:
            messages: List of messages in format [{"role": "user/assistant/system", "content": "..."}]
            temperature: Temperature for generation (0-1)
            manage_context: If True, applies context management to messages before sending
            format: Response format - 'text', 'json_object', or 'json_schema' (default: 'text')
            schema: Optional schema for JSON response (only used with 'json_schema' format)
        
        Returns:
            LLM response as string
        """
        pass
    
    @abstractmethod
    def call_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        manage_context: bool = True,
        format: str = 'text'
    ) -> Iterator[str]:
        """
        Abstract method for streaming responses.
        
        Args:
            messages: List of messages in format [{"role": "user/assistant/system", "content": "..."}]
            temperature: Temperature for generation (0-1)
            manage_context: If True, applies context management to messages before sending
            format: Response format - 'text', 'json_object', or 'json_schema' (default: 'text')
        
        Yields:
            Chunks of the LLM response as strings
        """
        pass
    
    @abstractmethod
    def call_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        temperature: float = 0.7,
        manage_context: bool = False,
        format: str = 'text'
    ) -> Dict[str, Any]:
        """
        Calls LLM API with function calling (tools) support.
        
        Args:
            messages: List of messages in format [{"role": "user/assistant/system", "content": "..."}]
            tools: List of tool definitions in OpenAI format
            tool_choice: "auto", "none", "required", or {"type": "function", "name": "function_name"}
            temperature: Temperature for generation (0-1)
            manage_context: If True, applies context management to messages before sending (default: False)
            format: Response format - 'text', 'json_object', or 'json_schema' (default: 'text')
        
        Returns:
            Dict with:
                - 'content': Text response (str or None)
                - 'tool_calls': List of tool calls or None
                - 'output': Raw output array from API
                - 'finish_reason': Completion status
        """
        pass
    
    @abstractmethod
    def call_stream_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        temperature: float = 0.7,
        manage_context: bool = False,
        format: str = 'text'
    ) -> Iterator[Dict[str, Any]]:
        """
        Streams LLM API response with function calling (tools) support.
        
        Args:
            messages: List of messages
            tools: List of tool definitions in OpenAI format
            tool_choice: "auto", "none", "required", or specific tool
            temperature: Temperature for generation (0-1)
            manage_context: If True, applies context management to messages before sending (default: False)
            format: Response format - 'text', 'json_object', or 'json_schema' (default: 'text')
        
        Yields:
            Dict with streaming events:
                - 'type': Event type ('text_delta', 'tool_call_start', 'tool_call_delta', 'tool_call_done', 'final', 'error')
                - 'delta': Content delta for text or arguments
                - 'output_index': Index of the output item
                - 'tool_call': Complete tool call info (for 'tool_call_done')
                - 'content'/'tool_calls': Final accumulated data (for 'final')
        """
        pass
    
    @abstractmethod
    def call_with_function_execution(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        available_functions: Dict[str, Callable],
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_iterations: int = 5,
        verbose: bool = False,
        manage_context: bool = True
    ) -> Dict[str, Any]:
        """
        Automatically handles the complete function calling cycle.
        
        1. Calls the LLM with tools
        2. Executes the requested functions
        3. Sends the results back to the LLM
        4. Repeats until getting a final response or reaching max_iterations
        
        Args:
            messages: Initial list of messages
            tools: Tool definitions in OpenAI format
            available_functions: Dict mapping function names to callables
            tool_choice: "auto", "none", "required", or specific tool
            temperature: Temperature for generation
            max_iterations: Maximum number of iterations to prevent infinite loops
            verbose: If True, prints debug information
            manage_context: If True, applies context management
        
        Returns:
            Dict with:
                - 'content': Final LLM response
                - 'messages': Complete message history
                - 'function_calls': List of all functions called
                - 'iterations': Number of iterations performed
                - 'context_stats': Context usage statistics (if manage_context=True)
        """
        pass
    
    @abstractmethod
    def call_stream_with_function_execution(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        available_functions: Dict[str, Callable],
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_iterations: int = 5,
        verbose: bool = False,
        manage_context: bool = True
    ) -> Iterator[Dict[str, Any]]:
        """
        Streams responses while automatically handling the complete function calling cycle.
        
        This method:
        1. Streams LLM responses in real-time
        2. Detects and executes function calls
        3. Sends function results back to the LLM
        4. Continues streaming until a final response or max_iterations
        
        Args:
            messages: Initial list of messages
            tools: Tool definitions in OpenAI format
            available_functions: Dict mapping function names to callables
            tool_choice: "auto", "none", "required", or specific tool
            temperature: Temperature for generation
            max_iterations: Maximum number of iterations to prevent infinite loops
            verbose: If True, prints debug information
            manage_context: If True, applies context management
        
        Yields:
            Dict with:
                - 'type': 'text_delta' | 'function_call_start' | 'function_call_result' | 'iteration_start' | 'final' | 'error'
                - 'content': The content based on type
                - 'iteration': Current iteration number
                - Additional fields depending on type:
                    - For 'function_call_start': 'function_name', 'arguments'
                    - For 'function_call_result': 'function_name', 'result'
                    - For 'final': 'messages', 'function_calls', 'iterations', 'context_stats'
        """
        pass