from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dinnovos import Agent
from dinnovos.llms import OpenAILLM
from dinnovos.llms.base import BaseLLM

import os
import json

@dataclass
class Message:
    role: str
    content: str
    timestamp: str

@dataclass
class Thread:
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Dict]
    keywords: List[str] #["keyword1", "keyword2", ...]

class ThreadManager:
    def __init__(self, llm_search: BaseLLM = None, llm: BaseLLM = None, verbose: bool = False):
        
        self.llm = llm
        
        self.threads: Dict[str, Thread] = {}
        
        self.active_thread_id: Optional[str] = None
        self.active_thread: Optional[Thread] = None

        self.verbose: bool = verbose

    def load_threads(self, data: Dict, max_threads: Optional[int] = None, max_messages_per_thread: Optional[int] = None):
        """Load threads with optional limits
        
        Args:
            data: Dictionary containing threads data and active_thread_id
            max_threads: Maximum number of threads to load (most recent first). None = load all
            max_messages_per_thread: Maximum number of messages per thread (most recent first). None = load all
        
        Note:
            The active thread is always loaded, even if it's not among the most recent threads.
        """

        _active_thread_id = data.get('active_thread_id')

        if _active_thread_id:
            self.active_thread_id = _active_thread_id
            self.active_thread = data.get('threads').get(_active_thread_id)

        all_threads = data.get('threads', {})

        # Get all threads and sort by updated_at (most recent first)
        threads_list = list(all_threads.items())
        threads_list.sort(key=lambda x: x[1].get('updated_at', ''), reverse=True)

        # Limit number of threads if specified
        if max_threads is not None:
            threads_list = threads_list[:max_threads]
            
            # Ensure active thread is always included
            if self.active_thread_id and self.active_thread_id in all_threads:
                
                # Check if active thread is not in the limited list
                thread_ids_in_list = {tid for tid, _ in threads_list}

                if self.active_thread_id not in thread_ids_in_list:

                    # Add active thread to the list
                    threads_list.append((self.active_thread_id, all_threads[self.active_thread_id]))

        # Load threads with limited messages
        for tid, thread_data in threads_list:
            
            # Sort messages by timestamp (most recent first) and limit if specified
            messages = thread_data.get('messages', [])

            if messages:

                #messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

                if max_messages_per_thread is not None:
                    messages = messages[:max_messages_per_thread]

                thread_data['messages'] = messages
            
            self.threads[tid] = Thread(**thread_data)

    def add_thread(self, thread_id: str, title: str, messages: List[Dict[str, str]], keywords: List[str], created_at: str, updated_at: str):
        """Add a new thread"""
        
        self.threads[thread_id] = Thread(
            id=thread_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            keywords=keywords
        )

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID"""
        return self.threads.get(thread_id)
    
    def delete_thread(self, thread_id: str):
        """Delete a thread by ID"""
        if thread_id in self.threads:
            del self.threads[thread_id]
            return True
    
        return False
    
    def switch_thread(self, thread_id: str) -> bool:
        """Change to another thread"""

        for tid, thread in self.threads.items():
            if tid == thread_id:
                self.active_thread_id = thread_id
                self.active_thread = thread
                return True
            
        return False

    def get_thread_messages(self, thread_id: str, for_agent: bool = False) -> Optional[List[Dict[str, str]]]:
        """Get messages from a thread by ID"""
        thread = self.get_thread(thread_id)

        if thread:

            if for_agent:

                messages = []

                for message in thread.messages:
                    messages.append({
                        "role": message.get('role'),
                        "content": message.get('content')
                    })

                return messages
            
            return thread.messages

        return None

    def add_message(self, thread_id: str, role: str, content: str, timestamp: str):
        """Add a message to a thread"""

        thread = self.get_thread(thread_id)

        if thread:
            thread.messages.append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })

            return True
        
        return False

    def get_last_messages(self, thread_id: str, n: int = 1, for_agent: bool = False) -> Optional[List[Dict[str, str]]]:
        """Get last n messages from a thread by ID"""
        thread = self.get_thread(thread_id)

        if thread:

            if for_agent:

                messages = []

                for message in thread.messages[-n:]:
                    messages.append({
                        "role": message.get('role'),
                        "content": message.get('content')
                    })

                return messages

            return thread.messages[-n:]
        
        return None

    def replace_messages(self, thread_id: str, messages: List[Dict[str, str]]):
        """Replace all messages in a thread"""
        thread = self.get_thread(thread_id)

        if thread:
            thread.messages = messages
            return True
        
        return False
    
    def search_thread(self, message: str) -> Dict:
        """Search threads based on message keywords
        
        Args:
            message: User message to search for
            
        Returns:
            List of tuples (thread_id, score) sorted by relevance
        """
        if not self.threads:

            return {
                "action": "create_thread",
                "thread_id": None,
            }
        
        thread_str = f"# Current thread: {self.active_thread_id}\n"
        thread_str += "# Existing threads\n"

        _content = ""

        for thread_id, thread in self.threads.items():

            _content = ""
            _current = "No"

            # Check title matches
            _title = thread.title.lower()

            # Check keyword matches
            _thread_keywords = set(kw.lower() for kw in thread.keywords)

            if self.active_thread_id == thread_id:
                _current = "Yes"

            # Check message content matches
            for msg in thread.messages:
                _content += f"- {msg['role'].lower()}: {msg['content'].lower()}\n"
            
            thread_str += f"Thread title: {_title}\n"
            thread_str += f"Thread id: {thread_id}\n"
            thread_str += f"Thread keywords: {_thread_keywords}\n"
            thread_str += f"Thread Current: {_current}\n"
            thread_str += f"Thread messages:\n"
            thread_str += f"{_content}\n"
        
        instructions = """You are an agent specialized in conversation thread management. 
            Your function is to analyze the current context and existing threads to determine the most appropriate action.

            You must evaluate and decide between the following options:

            1. Keep the current thread: when the conversation continues on the same topic.
            2. Switch to another existing thread: when the current topic better matches another already created thread.
            3. Search for a specific thread: when the user mentions, references, asks you to remember or search for a topic that is not among the current threads, but could exist in previous threads or conversations.
            4. Thread not found: when there is no thread related to the request and it cannot be inferred which one it should be.

            Your response must be in valid JSON format, without additional text, explanations, or comments.

            ### Output examples:

            1. Keep the current thread
            {
                "action": "keep_thread",
                "thread_id": "thread_4343553"
            }

            2. Switch to another existing thread
            {
                "action": "switch_thread",
                "thread_id": "thread_123456789"
            }

            3. Search for a specific thread
            {
                "action": "search_thread",
                "thread_id": ""
            }

            4. Thread not found
            {
                "action": "thread_not_found",
                "thread_id": ""
            }

            Make sure the JSON is completely valid and only contains the action and thread_id keys.
        """

        messages = [
            {"role": "system", "content": instructions},
            {"role": "system", "content": thread_str},
            {"role": "user", "content": message}
        ]

        # content=message, format="json_object", history=[{"role": "system", "content": thread_str}]

        # call agent router
        response = self.llm.call(messages=messages, format="json_object")

        response_json = json.loads(response)

        if response_json.get("action") == "keep_thread":
            return {
                "action": "keep_thread",
                "thread_id": f"{self.active_thread_id}",
            }
        elif response_json.get("action") == "switch_thread":
            return {
                "action": "switch_thread",
                "thread_id": response_json.get("thread_id"),
            }
        elif response_json.get("action") == "search_thread":
            return {
                "action": "search_thread",
                "thread_id": None,
            }

        return {
                "action": "threadnot_found",
                "thread_id": None,
            }