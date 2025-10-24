"""Google LLM interface for Dinnovos Agent"""

from typing import List, Dict, Iterator, Optional, Any, Callable
from .base import BaseLLM
from ..utils.context_manager import ContextManager


class GoogleLLM(BaseLLM):
    """Interface for Google models (Gemini)"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro", max_tokens: int = 100000, context_strategy: str = "smart"):
        super().__init__(api_key, model)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("Install package: pip install google-generativeai")
        
        self.context_manager = ContextManager(
            max_tokens=max_tokens,
            strategy=context_strategy,
            reserve_tokens=4096
        )
    
    def call(self, messages: List[Dict[str, str]], temperature: float = 0.7, manage_context: bool = True, verbose: bool = False) -> str:
        """Calls Google Gemini API"""
        try:
            if manage_context:
                messages = self.context_manager.manage(messages, verbose=verbose)
            
            chat_history = []
            
            for msg in messages[:-1]:  # All except the last one
                role = "user" if msg["role"] in ["user", "system"] else "model"
                chat_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            # Start chat with history
            chat = self.client.start_chat(history=chat_history)
            
            # Send the last message
            last_message = messages[-1]["content"]
            response = chat.send_message(
                last_message,
                generation_config={"temperature": temperature}
            )
            
            return response.text
        except Exception as e:
            return f"Error in Google: {str(e)}"
    
    def call_stream(self, messages: List[Dict[str, str]], temperature: float = 0.7, manage_context: bool = True, verbose: bool = False) -> Iterator[str]:
        """Streams Google Gemini API response"""
        try:
            if manage_context:
                messages = self.context_manager.manage(messages, verbose=verbose)
            
            chat_history = []
            
            for msg in messages[:-1]:  # All except the last one
                role = "user" if msg["role"] in ["user", "system"] else "model"
                chat_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            # Start chat with history
            chat = self.client.start_chat(history=chat_history)
            
            # Send the last message with streaming
            last_message = messages[-1]["content"]
            response = chat.send_message(
                last_message,
                generation_config={"temperature": temperature},
                stream=True
            )
            
            # Yield chunks as they arrive
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error in Google: {str(e)}"
    
    def call_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        temperature: float = 0.7,
        manage_context: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Calls Google Gemini API with function calling (tools) support.
        
        Args:
            messages: List of messages in format [{"role": "user/assistant/system", "content": "..."}]
            tools: List of tool definitions in Google format
            tool_choice: "auto", "none", or specific (note: Google has limited support)
            temperature: Temperature for generation (0-1)
        
        Returns:
            Dict with 'content' (str or None), 'tool_calls' (list or None), and 'finish_reason'
        """
        try:
            import google.generativeai as genai
            
            if manage_context:
                messages = self.context_manager.manage(messages, verbose=verbose)
            
            # Convert tools to Google format
            google_tools = self._convert_tools_to_google_format(tools)
            
            # Convert messages to Gemini format
            chat_history = self._convert_messages_to_google_format(messages[:-1])
            
            # Create model with tools
            model = genai.GenerativeModel(
                model_name=self.model,
                tools=google_tools if google_tools else None
            )
            
            # Start chat
            chat = model.start_chat(history=chat_history)
            
            # Send message
            last_message = messages[-1]
            if last_message["role"] == "tool":
                # For tool responses, we need to use a special format
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=last_message["name"],
                                response={"result": last_message["content"]}
                            )
                        )]
                    ),
                    generation_config={"temperature": temperature}
                )
            else:
                response = chat.send_message(
                    last_message["content"],
                    generation_config={"temperature": temperature}
                )
            
            result = {
                "content": None,
                "tool_calls": None,
                "finish_reason": "stop"
            }
            
            # Check for function calls
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Check if there are function calls
                if candidate.content.parts:
                    tool_calls = []
                    content_parts = []
                    
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Extract function call
                            fc = part.function_call
                            tool_calls.append({
                                "id": f"call_{hash(fc.name)}",
                                "type": "function",
                                "function": {
                                    "name": fc.name,
                                    "arguments": self._convert_google_args_to_json(fc.args)
                                }
                            })
                        elif hasattr(part, 'text') and part.text:
                            content_parts.append(part.text)
                    
                    if tool_calls:
                        result["tool_calls"] = tool_calls
                        result["finish_reason"] = "tool_calls"
                    
                    if content_parts:
                        result["content"] = "".join(content_parts)
                else:
                    result["content"] = response.text if hasattr(response, 'text') else None
            
            return result
        except Exception as e:
            return {
                "content": f"Error in Google: {str(e)}",
                "tool_calls": None,
                "finish_reason": "error"
            }
    
    def call_stream_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        temperature: float = 0.7,
        manage_context: bool = True,
        verbose: bool = False
    ) -> Iterator[Dict[str, Any]]:
        """
        Streams Google Gemini API response with function calling (tools) support.
        
        Args:
            messages: List of messages
            tools: List of tool definitions in Google format
            tool_choice: "auto", "none", or specific tool
            temperature: Temperature for generation (0-1)
        
        Yields:
            Dict chunks with 'type' ('content' or 'tool_call'), 'delta' (content chunk),
            'tool_call_id', 'function_name', 'function_arguments'
        """
        try:
            import google.generativeai as genai
            
            if manage_context:
                messages = self.context_manager.manage(messages, verbose=verbose)
            
            # Convert tools to Google format
            google_tools = self._convert_tools_to_google_format(tools)
            
            # Convert messages to Gemini format
            chat_history = self._convert_messages_to_google_format(messages[:-1])
            
            # Create model with tools
            model = genai.GenerativeModel(
                model_name=self.model,
                tools=google_tools if google_tools else None
            )
            
            # Start chat
            chat = model.start_chat(history=chat_history)
            
            # Send message with streaming
            last_message = messages[-1]
            if last_message["role"] == "tool":
                # For tool responses, we need to use a special format
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=last_message["name"],
                                response={"result": last_message["content"]}
                            )
                        )]
                    ),
                    generation_config={"temperature": temperature},
                    stream=True
                )
            else:
                response = chat.send_message(
                    last_message["content"],
                    generation_config={"temperature": temperature},
                    stream=True
                )
            
            # Process chunks
            # Track unique function calls with a counter
            import time
            call_counter = 0
            
            for chunk in response:
                if chunk.candidates and len(chunk.candidates) > 0:
                    candidate = chunk.candidates[0]
                    
                    if candidate.content.parts:
                        for part in candidate.content.parts:
                            # Text content
                            if hasattr(part, 'text') and part.text:
                                yield {
                                    "type": "content",
                                    "delta": part.text,
                                    "finish_reason": None
                                }
                            
                            # Function call
                            elif hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                call_counter += 1
                                # Generate unique ID for each function call
                                unique_id = f"call_{fc.name}_{call_counter}_{int(time.time() * 1000000)}"
                                yield {
                                    "type": "tool_call",
                                    "index": call_counter - 1,
                                    "tool_call_id": unique_id,
                                    "function_name": fc.name,
                                    "function_arguments": self._convert_google_args_to_json(fc.args),
                                    "finish_reason": "tool_calls"
                                }
        except Exception as e:
            yield {
                "type": "error",
                "delta": f"Error in Google: {str(e)}",
                "finish_reason": "error"
            }
    
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
        Flexible method that automatically handles the complete function calling cycle:
        1. Calls the LLM with tools
        2. Executes the requested functions
        3. Sends the results back to the LLM
        4. Repeats until getting a final response or reaching max_iterations
        
        Args:
            messages: Initial list of messages
            tools: Tool definitions in Google/OpenAI format
            available_functions: Dict mapping function names to callables
            tool_choice: "auto", "none", or specific tool
            temperature: Temperature for generation
            max_iterations: Maximum number of iterations to prevent infinite loops
            verbose: If True, prints debug information
        
        Returns:
            Dict with:
                - 'content': Final LLM response
                - 'messages': Complete message history
                - 'function_calls': List of all functions called
                - 'iterations': Number of iterations performed
        """
        import json
        
        conversation_messages = messages.copy()
        all_function_calls = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"\n{'='*60}")
                print(f"Iteration {iteration}")
                print(f"{'='*60}")
            
            # Call the LLM with tools
            response = self.call_with_tools(
                messages=conversation_messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                manage_context=manage_context,
                verbose=verbose
            )
            
            # If there's content and no tool calls, we're done
            if response["content"] and not response["tool_calls"]:
                if verbose:
                    print(f"\n✅ Final response: {response['content']}")
                
                result = {
                    "content": response["content"],
                    "messages": conversation_messages,
                    "function_calls": all_function_calls,
                    "iterations": iteration,
                    "finish_reason": response["finish_reason"]
                }
                
                if manage_context:
                    result["context_stats"] = self.context_manager.get_stats(conversation_messages)
                
                return result
            
            # If there are no tool calls, something went wrong
            if not response["tool_calls"]:
                if verbose:
                    print("⚠️ No tool calls or content")
                
                result = {
                    "content": response.get("content") or "No response generated",
                    "messages": conversation_messages,
                    "function_calls": all_function_calls,
                    "iterations": iteration,
                    "finish_reason": response["finish_reason"]
                }
                
                if manage_context:
                    result["context_stats"] = self.context_manager.get_stats(conversation_messages)
                
                return result
            
            # Add assistant message with tool calls
            conversation_messages.append({
                "role": "assistant",
                "content": response.get("content"),
                "tool_calls": response["tool_calls"]
            })
            
            # Execute each tool call
            for tool_call in response["tool_calls"]:
                function_name = tool_call["function"]["name"]
                function_args_str = tool_call["function"]["arguments"]
                
                try:
                    function_args = json.loads(function_args_str)
                except json.JSONDecodeError as e:
                    function_args = {}
                    if verbose:
                        print(f"⚠️ Error parsing arguments: {e}")
                
                if verbose:
                    print(f"\n🔧 Calling function: {function_name}")
                    print(f"📋 Arguments: {function_args}")
                
                # Verify that the function exists
                if function_name not in available_functions:
                    error_msg = f"Function '{function_name}' not found in available_functions"
                    if verbose:
                        print(f"❌ {error_msg}")
                    
                    function_response = json.dumps({"error": error_msg})
                else:
                    # Execute the function
                    try:
                        function_to_call = available_functions[function_name]
                        result = function_to_call(**function_args)
                        
                        # Ensure the result is a string
                        if isinstance(result, str):
                            function_response = result
                        else:
                            function_response = json.dumps(result)
                        
                        if verbose:
                            print(f"✅ Result: {function_response}")
                        
                    except Exception as e:
                        error_msg = f"Error executing function: {str(e)}"
                        if verbose:
                            print(f"❌ {error_msg}")
                        function_response = json.dumps({"error": error_msg})
                
                # Register the call
                all_function_calls.append({
                    "name": function_name,
                    "arguments": function_args,
                    "result": function_response
                })
                
                # Add the function result to messages
                conversation_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": function_response
                })
        
        # If we get here, we reached max_iterations
        if verbose:
            print(f"\n⚠️ Maximum iterations reached ({max_iterations})")
        
        result = {
            "content": "Maximum iterations reached without final response",
            "messages": conversation_messages,
            "function_calls": all_function_calls,
            "iterations": iteration,
            "finish_reason": "max_iterations"
        }
        
        if manage_context:
            result["context_stats"] = self.context_manager.get_stats(conversation_messages)
        
        return result
    
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
            tools: Tool definitions in Google/OpenAI format
            available_functions: Dict mapping function names to callables
            tool_choice: "auto", "none", or specific tool
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
        import json
        
        conversation_messages = messages.copy()
        all_function_calls = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                print(f"\n{'='*60}")
                print(f"Iteration {iteration}")
                print(f"{'='*60}")
            
            # Notify iteration start
            yield {
                "type": "iteration_start",
                "iteration": iteration,
                "content": f"Starting iteration {iteration}"
            }
            
            # Call the LLM with tools using streaming
            try:
                # Stream the response and accumulate content/tool calls
                accumulated_content = []
                accumulated_tool_calls = {}  # Dict indexed by tool_call_id
                has_content = False
                has_tool_calls = False
                
                for chunk in self.call_stream_with_tools(
                    messages=conversation_messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=temperature,
                    manage_context=manage_context,
                    verbose=verbose
                ):
                    chunk_type = chunk.get("type")
                    
                    if chunk_type == "content":
                        has_content = True
                        text_delta = chunk.get("delta", "")
                        accumulated_content.append(text_delta)
                        # Forward text deltas to the caller
                        yield {
                            "type": "text_delta",
                            "content": text_delta,
                            "iteration": iteration
                        }
                    
                    elif chunk_type == "tool_call":
                        has_tool_calls = True
                        tool_call_id = chunk.get("tool_call_id")
                        function_name = chunk.get("function_name")
                        function_args = chunk.get("function_arguments", "")
                        
                        if verbose:
                            print(f"\n[DEBUG] Tool call chunk - id: {tool_call_id}, name: {function_name}, args: {function_args}")
                        
                        # For Google, each tool call comes complete in one chunk
                        # Use tool_call_id as the key to handle multiple function calls
                        if tool_call_id not in accumulated_tool_calls:
                            accumulated_tool_calls[tool_call_id] = {
                                "id": tool_call_id,
                                "name": function_name,
                                "arguments": function_args
                            }
                        else:
                            # Update with new data (in case of incremental streaming)
                            if function_name:
                                accumulated_tool_calls[tool_call_id]["name"] = function_name
                            if function_args:
                                # For Google, args come complete, so replace instead of append
                                accumulated_tool_calls[tool_call_id]["arguments"] = function_args
                
                # If we have content but no tool calls, we're done
                if has_content and not has_tool_calls:
                    final_content = "".join(accumulated_content)
                    if verbose:
                        print(f"\n✅ Final response: {final_content}")
                    
                    result = {
                        "type": "final",
                        "content": final_content,
                        "messages": conversation_messages,
                        "function_calls": all_function_calls,
                        "iterations": iteration
                    }
                    
                    if manage_context:
                        result["context_stats"] = self.context_manager.get_stats(conversation_messages)
                    
                    yield result
                    return
                
                # If there are no tool calls, something went wrong
                if not accumulated_tool_calls:
                    if verbose:
                        print("⚠️ No tool calls or content")
                    
                    result = {
                        "type": "final",
                        "content": "".join(accumulated_content) if accumulated_content else "No response generated",
                        "messages": conversation_messages,
                        "function_calls": all_function_calls,
                        "iterations": iteration
                    }
                    
                    if manage_context:
                        result["context_stats"] = self.context_manager.get_stats(conversation_messages)
                    
                    yield result
                    return
                
                # Convert accumulated tool calls to list format
                tool_calls_list = []
                for tool_call_id, tool_data in accumulated_tool_calls.items():
                    tool_calls_list.append({
                        "id": tool_data["id"],
                        "type": "function",
                        "function": {
                            "name": tool_data["name"],
                            "arguments": tool_data["arguments"]
                        }
                    })
                
                # Add assistant message with tool calls to conversation
                conversation_messages.append({
                    "role": "assistant",
                    "content": "".join(accumulated_content) if accumulated_content else None,
                    "tool_calls": tool_calls_list
                })
                
                # Execute each tool call
                for tool_call in tool_calls_list:
                    function_name = tool_call["function"]["name"]
                    function_args_str = tool_call["function"]["arguments"]
                    call_id = tool_call["id"]
                    
                    try:
                        function_args = json.loads(function_args_str)
                    except json.JSONDecodeError as e:
                        function_args = {}
                        if verbose:
                            print(f"⚠️ Error parsing arguments: {e}")
                    
                    if verbose:
                        print(f"\n🔧 Calling function: {function_name}")
                        print(f"📋 Arguments: {function_args}")
                    
                    # Notify function call start
                    yield {
                        "type": "function_call_start",
                        "function_name": function_name,
                        "arguments": function_args,
                        "iteration": iteration,
                        "content": f"Calling {function_name}"
                    }
                    
                    # Verify that the function exists
                    if function_name not in available_functions:
                        error_msg = f"Function '{function_name}' not found in available_functions"
                        if verbose:
                            print(f"❌ {error_msg}")
                        
                        function_response = json.dumps({"error": error_msg})
                    else:
                        # Execute the function
                        try:
                            function_to_call = available_functions[function_name]
                            result = function_to_call(**function_args)
                            
                            # Ensure the result is a string
                            if isinstance(result, str):
                                function_response = result
                            else:
                                function_response = json.dumps(result)
                            
                            if verbose:
                                print(f"✅ Result: {function_response}")
                            
                        except Exception as e:
                            error_msg = f"Error executing function: {str(e)}"
                            if verbose:
                                print(f"❌ {error_msg}")
                            function_response = json.dumps({"error": error_msg})
                    
                    # Register the call
                    all_function_calls.append({
                        "name": function_name,
                        "arguments": function_args,
                        "result": function_response
                    })
                    
                    # Notify function result
                    yield {
                        "type": "function_call_result",
                        "function_name": function_name,
                        "result": function_response,
                        "iteration": iteration,
                        "content": function_response
                    }
                    
                    # Add function result to conversation
                    conversation_messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": function_name,
                        "content": function_response
                    })
                
            except Exception as e:
                if verbose:
                    print(f"❌ Error in iteration: {str(e)}")
                
                yield {
                    "type": "error",
                    "content": str(e),
                    "iteration": iteration
                }
                return
        
        # If we get here, we reached max_iterations
        if verbose:
            print(f"\n⚠️ Maximum iterations reached ({max_iterations})")
        
        result = {
            "type": "final",
            "content": "Maximum iterations reached without final response",
            "messages": conversation_messages,
            "function_calls": all_function_calls,
            "iterations": iteration
        }
        
        if manage_context:
            result["context_stats"] = self.context_manager.get_stats(conversation_messages)
        
        yield result
    
    def _convert_messages_to_google_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert OpenAI format messages to Google Gemini format"""
        import google.generativeai as genai
        
        chat_history = []
        
        for msg in messages:
            role = msg.get("role", "user")
            
            if role == "tool":
                # Tool response message
                chat_history.append({
                    "role": "function",
                    "parts": [genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=msg.get("name", ""),
                            response={"result": msg.get("content", "")}
                        )
                    )]
                })
            elif role == "assistant" and msg.get("tool_calls"):
                # Assistant message with tool calls
                parts = []
                for tool_call in msg["tool_calls"]:
                    import json
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])
                    parts.append(genai.protos.Part(
                        function_call=genai.protos.FunctionCall(
                            name=func_name,
                            args=func_args
                        )
                    ))
                chat_history.append({
                    "role": "model",
                    "parts": parts
                })
            else:
                # Regular user or assistant message
                if msg.get("content"):
                    gemini_role = "user" if role in ["user", "system"] else "model"
                    chat_history.append({
                        "role": gemini_role,
                        "parts": [msg["content"]]
                    })
        
        return chat_history
    
    def _convert_tools_to_google_format(self, tools: List[Dict[str, Any]]) -> List[Any]:
        """Convert OpenAI format tools to Google Gemini format"""
        try:
            # Google Gemini accepts tools in a simple dict format
            google_functions = []
            
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    params = func.get("parameters", {})
                    
                    # Build properties dict with correct Schema format
                    properties = {}
                    if "properties" in params:
                        for key, prop in params["properties"].items():
                            prop_type = self._get_google_type(prop.get("type", "string"))
                            prop_schema = {
                                "type": prop_type,
                                "description": prop.get("description", "")
                            }
                            # Add enum if present
                            if "enum" in prop:
                                prop_schema["enum"] = prop["enum"]
                            properties[key] = prop_schema
                    
                    # Create the function declaration in Google format
                    google_func = {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "parameters": {
                            "type": self._get_google_type(params.get("type", "object")),
                            "properties": properties,
                            "required": params.get("required", [])
                        }
                    }
                    google_functions.append(google_func)
            
            return google_functions if google_functions else []
        except Exception as e:
            print(f"Warning: Could not convert tools to Google format: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_google_type(self, openai_type: str):
        """Convert OpenAI type to Google type"""
        type_mapping = {
            "string": "STRING",
            "number": "NUMBER",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "array": "ARRAY",
            "object": "OBJECT"
        }
        return type_mapping.get(openai_type.lower(), "STRING")
    
    def _convert_google_args_to_json(self, args) -> str:
        """Convert Google function arguments to JSON string"""
        import json
        try:
            # Google returns a dict-like object
            if args is None:
                return "{}"
            args_dict = dict(args)
            return json.dumps(args_dict)
        except Exception as e:
            print(f"Warning: Error converting Google args to JSON: {e}, args type: {type(args)}, args: {args}")
            return "{}"