# agent.py

"""
Educational RAG Agent with Detailed Logging
Shows students exactly what happens at each step
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

from config import (
    MODEL_ID,
    TEMPERATURE,
    MAX_TOKENS,
    MAX_ITERATIONS,
    SYSTEM_PROMPT,
    SHOW_USAGE_STATS,
    SHOW_TOOL_EXECUTION
)
from tools import (
    get_calculator_tool_spec,
    execute_calculator,
    get_retrieve_tool_spec,
    retrieve_documents
)

# Load environment
load_dotenv()

MODEL_API_URL = os.getenv("MODEL_API_URL")
MODEL_API_KEY = os.getenv("MODEL_API_KEY")


def print_section(title: str, symbol: str = "="):
    """Print a formatted section header"""
    width = 80
    print(f"\n{symbol * width}")
    print(f"{title.center(width)}")
    print(f"{symbol * width}")


def print_json(data: Any, title: str = None, max_length: int = None):
    """Pretty print JSON data"""
    if title:
        print(f"\n📄 {title}:")
        print("-" * 80)
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    if max_length and len(json_str) > max_length:
        print(json_str[:max_length])
        print(f"\n... (truncated, {len(json_str) - max_length} more characters)")
    else:
        print(json_str)
    print("-" * 80)


class EducationalRAGAgent:
    """RAG Agent with detailed educational logging"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize educational agent
        
        Args:
            verbose: If True, shows all details. If False, shows minimal info.
        """
        if not MODEL_API_URL or not MODEL_API_KEY:
            raise ValueError(
                "MODEL_API_URL and MODEL_API_KEY must be set in .env file"
            )
        
        self.conversation_history: List[Dict] = []
        self.total_cost = 0.0
        self.verbose = verbose
        self.request_count = 0
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "TOOL": "🔧",
            "API": "🌐",
            "DATA": "📊"
        }.get(level, "  ")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    def _call_model(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Call Bedrock model via API Gateway with detailed logging"""
        
        self.request_count += 1
        
        print_section(f"🌐 API REQUEST #{self.request_count}", "=")
        
        # Build payload
        payload = {
            "model_id": MODEL_ID,
            "messages": messages,
            "system": [{"text": SYSTEM_PROMPT}],
            "inference_config": {
                "maxTokens": MAX_TOKENS,
                "temperature": TEMPERATURE
            }
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = {"auto": {}}
        
        # Show what we're sending
        self._log(f"Endpoint: {MODEL_API_URL}", "API")
        self._log(f"Model: {MODEL_ID}", "API")
        self._log(f"Temperature: {TEMPERATURE}", "API")
        self._log(f"Max Tokens: {MAX_TOKENS}", "API")
        
        if self.verbose:
            print_json(
                {"messages": messages[-1] if messages else None},
                "Last Message Being Sent",
                max_length=500
            )
            
            if tools:
                print(f"\n🔧 Tools Available: {len(tools)}")
                for tool in tools:
                    print(f"   - {tool['toolSpec']['name']}")
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": MODEL_API_KEY
        }
        
        self._log("Sending request to Bedrock...", "API")
        
        try:
            # Make request
            import time
            start_time = time.time()
            
            response = requests.post(
                MODEL_API_URL,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            # Check response
            response.raise_for_status()
            data = response.json()
            
            self._log(f"Response received in {elapsed:.2f}s", "SUCCESS")
            
            # Show response details
            print_section("📥 API RESPONSE", "-")
            
            if self.verbose:
                print_json(data, "Full Response", max_length=1000)
            
            # Extract key info
            stop_reason = data.get("stop_reason")
            usage = data.get("usage", {})
            output = data.get("output", {})
            
            self._log(f"Stop Reason: {stop_reason}", "DATA")
            self._log(
                f"Tokens: {usage.get('input_tokens', 0)} in, "
                f"{usage.get('output_tokens', 0)} out",
                "DATA"
            )
            self._log(f"Cost: ${usage.get('total_cost', 0):.6f}", "DATA")
            
            # Show monthly usage
            monthly_usage = data.get("monthly_usage", {})
            if monthly_usage:
                used = monthly_usage.get('used', 0)
                limit = monthly_usage.get('limit', 0)
                remaining = monthly_usage.get('remaining', 0)
                percentage = (used / limit * 100) if limit > 0 else 0
                
                self._log(
                    f"Monthly: ${used:.2f} / ${limit:.2f} ({percentage:.1f}% used, ${remaining:.2f} remaining)",
                    "DATA"
                )
            
            # Show message content
            message_content = output.get("message", {}).get("content", [])
            
            print("\n📝 Response Content Blocks:")
            for i, block in enumerate(message_content, 1):
                if "text" in block:
                    print(f"\n   Block {i} [TEXT]:")
                    text = block["text"]
                    if len(text) > 200:
                        print(f"   {text[:200]}...")
                    else:
                        print(f"   {text}")
                
                elif "toolUse" in block:
                    tool_use = block["toolUse"]
                    print(f"\n   Block {i} [TOOL USE]:")
                    print(f"   Tool: {tool_use['name']}")
                    print(f"   Tool Use ID: {tool_use['toolUseId']}")
                    print(f"   Input: {json.dumps(tool_use.get('input', {}), ensure_ascii=False)}")
            
            return data
            
        except requests.exceptions.HTTPError as e:
            self._log(f"HTTP Error: {e.response.status_code}", "ERROR")
            if self.verbose:
                print(f"Response: {e.response.text}")
            
            # Check for monthly limit error
            if e.response.status_code == 429:
                try:
                    error_data = e.response.json()
                    if "Monthly limit exceeded" in error_data.get("error", ""):
                        print_section("⚠️  MONTHLY LIMIT EXCEEDED", "!")
                        print(f"\n   Used: ${error_data.get('monthly_usage', 0):.2f}")
                        print(f"   Limit: ${error_data.get('monthly_limit', 0):.2f}")
                        print(f"   Please wait until next month or contact support.\n")
                except:
                    pass
            
            raise Exception(f"Model API error: {e.response.status_code}")
        except Exception as e:
            self._log(f"Error: {str(e)}", "ERROR")
            raise Exception(f"Failed to call model: {str(e)}")
    
    def _execute_tool(self, tool_use: Dict) -> str:
        """Execute a tool and return result with detailed logging"""
        
        tool_name = tool_use.get("name")
        tool_input = tool_use.get("input", {})
        
        print_section(f"🔧 TOOL EXECUTION: {tool_name}", "=")
        
        self._log(f"Tool: {tool_name}", "TOOL")
        self._log(f"Tool Use ID: {tool_use.get('toolUseId')}", "TOOL")
        
        print_json(tool_input, "Tool Input")
        
        # Route to appropriate tool
        self._log("Executing tool...", "TOOL")
        
        if tool_name == "calculator":
            result = execute_calculator(**tool_input)
        
        elif tool_name == "retrieve_documents":
            result = retrieve_documents(**tool_input)
        
        else:
            result = {
                "status": "error",
                "error": f"Unknown tool: {tool_name}"
            }
        
        # Show result
        print_section("📤 TOOL RESULT", "-")
        
        self._log(f"Status: {result.get('status', 'unknown')}", "DATA")
        
        if self.verbose:
            print_json(result, "Full Tool Result", max_length=2000)
        else:
            # Show summary
            if tool_name == "retrieve_documents":
                print(f"   Results: {result.get('results_count', 0)} documents")
                print(f"   Query: {result.get('query', 'N/A')}")
            elif tool_name == "calculator":
                print(f"   Result: {result.get('result', 'N/A')}")
        
        result_text = json.dumps(result, indent=2, ensure_ascii=False)
        
        return result_text
    
    def chat(self, user_message: str) -> str:
        """
        Send message and get response with full educational logging
        
        Args:
            user_message: User's question
            
        Returns:
            Assistant's response
        """
        
        print_section(f"💬 NEW CHAT REQUEST", "═")
        self._log(f"User: {user_message}", "INFO")
        
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": [{"text": user_message}]
        })
        
        self._log(f"Conversation history: {len(self.conversation_history)} messages", "DATA")
        
        # Tool specifications
        tools = [
            get_calculator_tool_spec(),
            get_retrieve_tool_spec()
        ]
        
        iteration = 0
        request_cost = 0.0
        
        while iteration < MAX_ITERATIONS:
            iteration += 1
            
            print_section(f"🔄 ITERATION {iteration}/{MAX_ITERATIONS}", "─")
            
            # Call model
            response = self._call_model(
                messages=self.conversation_history,
                tools=tools
            )
            
            # Track usage
            usage = response.get("usage", {})
            cost = usage.get("total_cost", 0)
            request_cost += cost
            self.total_cost += cost
            
            # Extract response
            output = response.get("output", {})
            message_content = output.get("message", {}).get("content", [])
            stop_reason = response.get("stop_reason")
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": message_content
            })
            
            # Handle tool use
            if stop_reason == "tool_use":
                self._log("Model requested tool use", "INFO")
                
                tool_results = []
                
                for block in message_content:
                    if "toolUse" in block:
                        tool_use = block["toolUse"]
                        result_text = self._execute_tool(tool_use)
                        
                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_use["toolUseId"],
                                "content": [{"text": result_text}]
                            }
                        })
                
                # Add tool results
                print_section("📨 SENDING TOOL RESULTS BACK TO MODEL", "-")
                self._log(f"Sending {len(tool_results)} tool result(s)", "INFO")
                
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
                
                self._log("Continuing to next iteration...", "INFO")
                continue  # Next iteration
            
            else:
                # Extract final response
                final_text = ""
                for block in message_content:
                    if "text" in block:
                        final_text += block["text"]
                
                print_section("✨ FINAL RESPONSE", "═")
                print(f"\n{final_text}\n")
                
                print_section("💰 COST SUMMARY", "-")
                print(f"   This request: ${request_cost:.6f}")
                print(f"   Session total: ${self.total_cost:.6f}")
                print(f"   Total iterations: {iteration}")
                
                # Show monthly usage in summary
                monthly_usage = response.get("monthly_usage", {})
                if monthly_usage:
                    used = monthly_usage.get('used', 0)
                    limit = monthly_usage.get('limit', 0)
                    remaining = monthly_usage.get('remaining', 0)
                    print(f"\n   Monthly usage: ${used:.2f} / ${limit:.2f} (${remaining:.2f} remaining)")
                
                print()
                
                return final_text
        
        return "⚠️ Maximum iterations reached"
    
    def reset(self):
        """Clear conversation history"""
        print_section("🔄 CONVERSATION RESET", "-")
        self._log(f"Cleared {len(self.conversation_history)} messages", "INFO")
        self._log(f"Session cost was: ${self.total_cost:.6f}", "DATA")
        
        self.conversation_history = []
        self.request_count = 0
        # Don't reset total_cost to track session total


def main():
    """Interactive chat interface with educational mode"""
    
    print("=" * 80)
    print("🎓 EDUCATIONAL RAG AGENT WITH DETAILED LOGGING".center(80))
    print("=" * 80)
    print(f"\nModel: {MODEL_ID}")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print(f"Verbose mode: ON (shows all API details)")
    print("\nCommands:")
    print("  - Type your question to chat")
    print("  - 'reset' to clear history")
    print("  - 'verbose on/off' to toggle detailed logging")
    print("  - 'quit' to exit")
    print("=" * 80)
    
    agent = EducationalRAGAgent(verbose=True)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("\n👋 Goodbye!")
                print(f"Total session cost: ${agent.total_cost:.6f}")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                continue
            
            if user_input.lower().startswith('verbose'):
                if 'off' in user_input.lower():
                    agent.verbose = False
                    print("📢 Verbose mode: OFF (minimal output)")
                else:
                    agent.verbose = True
                    print("📢 Verbose mode: ON (detailed output)")
                continue
            
            response = agent.chat(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            print(f"Total session cost: ${agent.total_cost:.6f}")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
# """
# Educational RAG Agent with Detailed Logging
# Shows students exactly what happens at each step
# """

# import os
# import json
# import requests
# from typing import List, Dict, Any, Optional
# from dotenv import load_dotenv
# from datetime import datetime

# from config import (
#     MODEL_ID,
#     TEMPERATURE,
#     MAX_TOKENS,
#     MAX_ITERATIONS,
#     SYSTEM_PROMPT,
#     SHOW_USAGE_STATS,
#     SHOW_TOOL_EXECUTION
# )
# from tools import (
#     get_calculator_tool_spec,
#     execute_calculator,
#     get_retrieve_tool_spec,
#     retrieve_documents
# )

# # Load environment
# load_dotenv()

# MODEL_API_URL = os.getenv("MODEL_API_URL")
# MODEL_API_KEY = os.getenv("MODEL_API_KEY")


# def print_section(title: str, symbol: str = "="):
#     """Print a formatted section header"""
#     width = 80
#     print(f"\n{symbol * width}")
#     print(f"{title.center(width)}")
#     print(f"{symbol * width}")


# def print_json(data: Any, title: str = None, max_length: int = None):
#     """Pretty print JSON data"""
#     if title:
#         print(f"\n📄 {title}:")
#         print("-" * 80)
    
#     json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
#     if max_length and len(json_str) > max_length:
#         print(json_str[:max_length])
#         print(f"\n... (truncated, {len(json_str) - max_length} more characters)")
#     else:
#         print(json_str)
#     print("-" * 80)


# class EducationalRAGAgent:
#     """RAG Agent with detailed educational logging"""
    
#     def __init__(self, verbose: bool = True):
#         """
#         Initialize educational agent
        
#         Args:
#             verbose: If True, shows all details. If False, shows minimal info.
#         """
#         if not MODEL_API_URL or not MODEL_API_KEY:
#             raise ValueError(
#                 "MODEL_API_URL and MODEL_API_KEY must be set in .env file"
#             )
        
#         self.conversation_history: List[Dict] = []
#         self.total_cost = 0.0
#         self.verbose = verbose
#         self.request_count = 0
    
#     def _log(self, message: str, level: str = "INFO"):
#         """Log a message with timestamp"""
#         timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
#         prefix = {
#             "INFO": "ℹ️ ",
#             "SUCCESS": "✅",
#             "ERROR": "❌",
#             "TOOL": "🔧",
#             "API": "🌐",
#             "DATA": "📊"
#         }.get(level, "  ")
        
#         print(f"[{timestamp}] {prefix} {message}")
    
#     def _call_model(
#         self,
#         messages: List[Dict],
#         tools: Optional[List[Dict]] = None
#     ) -> Dict[str, Any]:
#         """Call Bedrock model via API Gateway with detailed logging"""
        
#         self.request_count += 1
        
#         print_section(f"🌐 API REQUEST #{self.request_count}", "=")
        
#         # Build payload
#         payload = {
#             "model_id": MODEL_ID,
#             "messages": messages,
#             "system": [{"text": SYSTEM_PROMPT}],
#             "inference_config": {
#                 "maxTokens": MAX_TOKENS,
#                 "temperature": TEMPERATURE
#             }
#         }
        
#         if tools:
#             payload["tools"] = tools
#             payload["tool_choice"] = {"auto": {}}
        
#         # Show what we're sending
#         self._log(f"Endpoint: {MODEL_API_URL}", "API")
#         self._log(f"Model: {MODEL_ID}", "API")
#         self._log(f"Temperature: {TEMPERATURE}", "API")
#         self._log(f"Max Tokens: {MAX_TOKENS}", "API")
        
#         if self.verbose:
#             print_json(
#                 {"messages": messages[-1] if messages else None},
#                 "Last Message Being Sent",
#                 max_length=500
#             )
            
#             if tools:
#                 print(f"\n🔧 Tools Available: {len(tools)}")
#                 for tool in tools:
#                     print(f"   - {tool['toolSpec']['name']}")
        
#         # Prepare request
#         headers = {
#             "Content-Type": "application/json",
#             "x-api-key": MODEL_API_KEY
#         }
        
#         self._log("Sending request to Bedrock...", "API")
        
#         try:
#             # Make request
#             import time
#             start_time = time.time()
            
#             response = requests.post(
#                 MODEL_API_URL,
#                 json=payload,
#                 headers=headers,
#                 timeout=60
#             )
            
#             elapsed = time.time() - start_time
            
#             # Check response
#             response.raise_for_status()
#             data = response.json()
            
#             self._log(f"Response received in {elapsed:.2f}s", "SUCCESS")
            
#             # Show response details
#             print_section("📥 API RESPONSE", "-")
            
#             if self.verbose:
#                 print_json(data, "Full Response", max_length=1000)
            
#             # Extract key info
#             stop_reason = data.get("stop_reason")
#             usage = data.get("usage", {})
#             output = data.get("output", {})
            
#             self._log(f"Stop Reason: {stop_reason}", "DATA")
#             self._log(
#                 f"Tokens: {usage.get('input_tokens', 0)} in, "
#                 f"{usage.get('output_tokens', 0)} out",
#                 "DATA"
#             )
#             self._log(f"Cost: ${usage.get('total_cost', 0):.6f}", "DATA")
            
#             # Show message content
#             message_content = output.get("message", {}).get("content", [])
            
#             print("\n📝 Response Content Blocks:")
#             for i, block in enumerate(message_content, 1):
#                 if "text" in block:
#                     print(f"\n   Block {i} [TEXT]:")
#                     text = block["text"]
#                     if len(text) > 200:
#                         print(f"   {text[:200]}...")
#                     else:
#                         print(f"   {text}")
                
#                 elif "toolUse" in block:
#                     tool_use = block["toolUse"]
#                     print(f"\n   Block {i} [TOOL USE]:")
#                     print(f"   Tool: {tool_use['name']}")
#                     print(f"   Tool Use ID: {tool_use['toolUseId']}")
#                     print(f"   Input: {json.dumps(tool_use.get('input', {}), ensure_ascii=False)}")
            
#             return data
            
#         except requests.exceptions.HTTPError as e:
#             self._log(f"HTTP Error: {e.response.status_code}", "ERROR")
#             if self.verbose:
#                 print(f"Response: {e.response.text}")
#             raise Exception(f"Model API error: {e.response.status_code}")
#         except Exception as e:
#             self._log(f"Error: {str(e)}", "ERROR")
#             raise Exception(f"Failed to call model: {str(e)}")
    
#     def _execute_tool(self, tool_use: Dict) -> str:
#         """Execute a tool and return result with detailed logging"""
        
#         tool_name = tool_use.get("name")
#         tool_input = tool_use.get("input", {})
        
#         print_section(f"🔧 TOOL EXECUTION: {tool_name}", "=")
        
#         self._log(f"Tool: {tool_name}", "TOOL")
#         self._log(f"Tool Use ID: {tool_use.get('toolUseId')}", "TOOL")
        
#         print_json(tool_input, "Tool Input")
        
#         # Route to appropriate tool
#         self._log("Executing tool...", "TOOL")
        
#         if tool_name == "calculator":
#             result = execute_calculator(**tool_input)
        
#         elif tool_name == "retrieve_documents":
#             result = retrieve_documents(**tool_input)
        
#         else:
#             result = {
#                 "status": "error",
#                 "error": f"Unknown tool: {tool_name}"
#             }
        
#         # Show result
#         print_section("📤 TOOL RESULT", "-")
        
#         self._log(f"Status: {result.get('status', 'unknown')}", "DATA")
        
#         if self.verbose:
#             print_json(result, "Full Tool Result", max_length=2000)
#         else:
#             # Show summary
#             if tool_name == "retrieve_documents":
#                 print(f"   Results: {result.get('results_count', 0)} documents")
#                 print(f"   Query: {result.get('query', 'N/A')}")
#             elif tool_name == "calculator":
#                 print(f"   Result: {result.get('result', 'N/A')}")
        
#         result_text = json.dumps(result, indent=2, ensure_ascii=False)
        
#         return result_text
    
#     def chat(self, user_message: str) -> str:
#         """
#         Send message and get response with full educational logging
        
#         Args:
#             user_message: User's question
            
#         Returns:
#             Assistant's response
#         """
        
#         print_section(f"💬 NEW CHAT REQUEST", "═")
#         self._log(f"User: {user_message}", "INFO")
        
#         # Add user message
#         self.conversation_history.append({
#             "role": "user",
#             "content": [{"text": user_message}]
#         })
        
#         self._log(f"Conversation history: {len(self.conversation_history)} messages", "DATA")
        
#         # Tool specifications
#         tools = [
#             get_calculator_tool_spec(),
#             get_retrieve_tool_spec()
#         ]
        
#         iteration = 0
#         request_cost = 0.0
        
#         while iteration < MAX_ITERATIONS:
#             iteration += 1
            
#             print_section(f"🔄 ITERATION {iteration}/{MAX_ITERATIONS}", "─")
            
#             # Call model
#             response = self._call_model(
#                 messages=self.conversation_history,
#                 tools=tools
#             )
            
#             # Track usage
#             usage = response.get("usage", {})
#             cost = usage.get("total_cost", 0)
#             request_cost += cost
#             self.total_cost += cost
            
#             # Extract response
#             output = response.get("output", {})
#             message_content = output.get("message", {}).get("content", [])
#             stop_reason = response.get("stop_reason")
            
#             # Add to history
#             self.conversation_history.append({
#                 "role": "assistant",
#                 "content": message_content
#             })
            
#             self._log(
#                 f"Iteration cost: ${cost:.6f} | "
#                 f"Request total: ${request_cost:.6f} | "
#                 f"Session total: ${self.total_cost:.6f}",
#                 "DATA"
#             )
            
#             # Handle tool use
#             if stop_reason == "tool_use":
#                 self._log("Model requested tool use", "INFO")
                
#                 tool_results = []
                
#                 for block in message_content:
#                     if "toolUse" in block:
#                         tool_use = block["toolUse"]
#                         result_text = self._execute_tool(tool_use)
                        
#                         tool_results.append({
#                             "toolResult": {
#                                 "toolUseId": tool_use["toolUseId"],
#                                 "content": [{"text": result_text}]
#                             }
#                         })
                
#                 # Add tool results
#                 print_section("📨 SENDING TOOL RESULTS BACK TO MODEL", "-")
#                 self._log(f"Sending {len(tool_results)} tool result(s)", "INFO")
                
#                 self.conversation_history.append({
#                     "role": "user",
#                     "content": tool_results
#                 })
                
#                 self._log("Continuing to next iteration...", "INFO")
#                 continue  # Next iteration
            
#             else:
#                 # Extract final response
#                 final_text = ""
#                 for block in message_content:
#                     if "text" in block:
#                         final_text += block["text"]
                
#                 print_section("✨ FINAL RESPONSE", "═")
#                 print(f"\n{final_text}\n")
                
#                 print_section("💰 COST SUMMARY", "-")
#                 print(f"   This request: ${request_cost:.6f}")
#                 print(f"   Session total: ${self.total_cost:.6f}")
#                 print(f"   Total iterations: {iteration}")
#                 print()
                
#                 return final_text
        
#         return "⚠️ Maximum iterations reached"
    
#     def reset(self):
#         """Clear conversation history"""
#         print_section("🔄 CONVERSATION RESET", "-")
#         self._log(f"Cleared {len(self.conversation_history)} messages", "INFO")
#         self._log(f"Session cost was: ${self.total_cost:.6f}", "DATA")
        
#         self.conversation_history = []
#         self.request_count = 0
#         # Don't reset total_cost to track session total


# def main():
#     """Interactive chat interface with educational mode"""
    
#     print("=" * 80)
#     print("🎓 EDUCATIONAL RAG AGENT WITH DETAILED LOGGING".center(80))
#     print("=" * 80)
#     print(f"\nModel: {MODEL_ID}")
#     print(f"Max iterations: {MAX_ITERATIONS}")
#     print(f"Verbose mode: ON (shows all API details)")
#     print("\nCommands:")
#     print("  - Type your question to chat")
#     print("  - 'reset' to clear history")
#     print("  - 'verbose on/off' to toggle detailed logging")
#     print("  - 'quit' to exit")
#     print("=" * 80)
    
#     agent = EducationalRAGAgent(verbose=True)
    
#     while True:
#         try:
#             user_input = input("\n👤 You: ").strip()
            
#             if not user_input:
#                 continue
            
#             if user_input.lower() == 'quit':
#                 print("\n👋 Goodbye!")
#                 print(f"Total session cost: ${agent.total_cost:.6f}")
#                 break
            
#             if user_input.lower() == 'reset':
#                 agent.reset()
#                 continue
            
#             if user_input.lower().startswith('verbose'):
#                 if 'off' in user_input.lower():
#                     agent.verbose = False
#                     print("📢 Verbose mode: OFF (minimal output)")
#                 else:
#                     agent.verbose = True
#                     print("📢 Verbose mode: ON (detailed output)")
#                 continue
            
#             response = agent.chat(user_input)
            
#         except KeyboardInterrupt:
#             print("\n\n👋 Goodbye!")
#             print(f"Total session cost: ${agent.total_cost:.6f}")
#             break
#         except Exception as e:
#             print(f"\n❌ Error: {str(e)}")


# if __name__ == "__main__":
#     main()