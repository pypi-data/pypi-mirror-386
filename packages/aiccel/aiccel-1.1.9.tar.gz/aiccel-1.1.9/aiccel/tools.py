from abc import ABC, abstractmethod
import json
import re
import requests
import asyncio
from typing import Dict, Any, Callable, List, Optional, Union, Tuple
from urllib.parse import quote_plus
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import contextmanager
import time

from .providers import LLMProvider
from .embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import PyPDF2
from textsplitter import TextSplitter

# Constants
DEFAULT_REQUEST_TIMEOUT = 15
DEFAULT_DETECTION_THRESHOLD = 0.5
MAX_SEARCH_RESULTS = 5
MAX_FORECAST_PERIODS = 3
MAX_RETRY_ATTEMPTS = 3

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ToolError(Exception):
    """Base exception for tool-related errors"""
    pass

class ToolExecutionError(ToolError):
    """Raised when tool execution fails"""
    pass

class ToolValidationError(ToolError):
    """Raised when tool input validation fails"""
    pass

@dataclass
class ToolResult:
    """Structured result from tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class Tool:
    """Enhanced base class for tools with improved error handling and consistency"""
    
    def __init__(self, 
                 name: str, 
                 description: str, 
                 function: Callable,
                 llm_provider: Optional[LLMProvider] = None,
                 detection_threshold: float = DEFAULT_DETECTION_THRESHOLD,
                 timeout: float = DEFAULT_REQUEST_TIMEOUT):
        self.name = self._validate_name(name)
        self.description = description
        self.function = function
        self.llm_provider = llm_provider
        self.detection_threshold = detection_threshold
        self.timeout = timeout
        self.example_usages = []
        
    def _validate_name(self, name: str) -> str:
        """Validate tool name format"""
        if not name or not isinstance(name, str):
            raise ToolValidationError("Tool name must be a non-empty string")
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            raise ToolValidationError("Tool name must start with a letter and contain only letters, numbers, and underscores")
        return name.lower()
    
    def set_llm_provider(self, provider: LLMProvider) -> 'Tool':
        """Set LLM provider for relevance assessment"""
        self.llm_provider = provider
        return self
    
    def add_example(self, example: Dict[str, Any]) -> 'Tool':
        """Add usage example for the tool"""
        if not isinstance(example, dict):
            raise ToolValidationError("Example must be a dictionary")
        self.example_usages.append(example)
        return self
        
    def execute(self, args: Dict[str, Any]) -> str:
        """Execute tool with improved error handling and timing"""
        start_time = time.time()
        logger.debug(f"Executing tool '{self.name}' with args: {args}")
        
        try:
            # Validate inputs
            self._validate_args(args)
            
            # Execute with timeout
            result = self._execute_with_timeout(args)
            
            execution_time = time.time() - start_time
            logger.debug(f"Tool '{self.name}' executed successfully in {execution_time:.2f}s, result: {str(result)[:100]}...")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing tool '{self.name}' after {execution_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _validate_args(self, args: Dict[str, Any]) -> None:
        """Validate tool arguments - override in subclasses"""
        if not isinstance(args, dict):
            raise ToolValidationError("Arguments must be a dictionary")
    
    def _execute_with_timeout(self, args: Dict[str, Any]) -> str:
        """Execute function with timeout handling"""
        try:
            return self.function(args)
        except Exception as e:
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
        
    async def execute_async(self, args: Dict[str, Any]) -> str:
        """Async execution with proper error handling"""
        start_time = time.time()
        logger.debug(f"Executing tool '{self.name}' async with args: {args}")
        
        try:
            self._validate_args(args)
            
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self.execute, args),
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            logger.debug(f"Tool '{self.name}' async executed successfully in {execution_time:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Tool '{self.name}' timed out after {execution_time:.2f}s"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing tool '{self.name}' async after {execution_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def assess_relevance(self, query: str) -> float:
        """Assess tool relevance with improved error handling"""
        if not self.llm_provider:
            logger.warning(f"No LLM provider set for tool '{self.name}', returning default relevance score 0.0")
            return 0.0

        if not query or not query.strip():
            logger.warning(f"Empty query provided for relevance assessment of tool '{self.name}'")
            return 0.0

        relevance_prompt = (
            f"Query: {query}\n\n"
            f"Tool: {self.name}\n"
            f"Description: {self.description}\n\n"
            "Determine how relevant this tool is for the query on a scale from 0 to 1, where 0 is not relevant and 1 is highly relevant. "
            "Consider the tool's description and the query's intent. "
            "Return ONLY a single float value between 0 and 1, no additional text."
        )
        
        try:
            response = self.llm_provider.generate(relevance_prompt)
            # Extract numeric value from response
            score_match = re.search(r'([0-1](?:\.\d+)?)', response.strip())
            if score_match:
                score = float(score_match.group(1))
            else:
                score = float(response.strip())
            
            score = min(max(score, 0.0), 1.0)
            logger.debug(f"LLM relevance score for tool '{self.name}' on query '{query[:50]}...': {score}")
            return score
            
        except (ValueError, Exception) as e:
            logger.error(f"Error assessing relevance for tool '{self.name}' with LLM: {str(e)}")
            return 0.0
    
    def is_relevant(self, query: str) -> bool:
        """Check if tool is relevant for query"""
        score = self.assess_relevance(query)
        is_relevant = score >= self.detection_threshold
        logger.debug(f"Tool '{self.name}' relevance for query '{query[:50]}...': {score}, is_relevant: {is_relevant}")
        return is_relevant
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    def get_format_instructions(self) -> str:
        """Generate format instructions for tool usage"""
        instructions = f"To use the {self.name} tool, format like this:\n"
        instructions += f'[TOOL]{{"name": "{self.name}", "args": {{...}}}}[/TOOL]\n\n'
        
        if self.example_usages:
            instructions += "Examples:\n"
            for example in self.example_usages:
                instructions += f"[TOOL]{json.dumps(example)}[/TOOL]\n"
                
        return instructions

class SearchTool(Tool):
    """Enhanced search tool with better error handling and caching"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = DEFAULT_REQUEST_TIMEOUT):
        if not api_key:
            logger.warning("SearchTool initialized without API key. Functionality will be limited.")
        
        self.api_key = api_key
        self._session = requests.Session()
        
        super().__init__(
            name="search",
            description="Search the web for current information on a topic",
            function=self._search,
            detection_threshold=0.3,
            timeout=timeout
        )
        
        self.add_example({"name": "search", "args": {"query": "current climate news"}})
        self.add_example({"name": "search", "args": {"query": "who is the CEO of OpenAI"}})
    
    def _validate_args(self, args: Dict[str, Any]) -> None:
        """Validate search arguments"""
        super()._validate_args(args)
        
        query = self._extract_query(args)
        if not query:
            raise ToolValidationError("No search query provided. Please specify what you want to search for.")
    
    def _extract_query(self, args: Dict[str, Any]) -> Optional[str]:
        """Extract query from various possible parameter names"""
        for param_name in ["query", "q", "search", "text", "input", "searchQuery"]:
            if param_name in args and args[param_name]:
                return str(args[param_name]).strip()
        return None
    
    def _search(self, args: Dict[str, Any]) -> str:
        """Perform web search with improved error handling"""
        query = self._extract_query(args)
        
        if not self.api_key:
            raise ToolExecutionError("Search API key is not configured")
            
        try:
            result = self._search_with_serper(query)
            logger.debug(f"SearchTool returned results for query '{query}': {result[:100]}...")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ToolExecutionError("Invalid API key or authentication failed")
            elif e.response.status_code == 429:
                raise ToolExecutionError("API rate limit exceeded. Please try again later.")
            else:
                raise ToolExecutionError(f"HTTP error {e.response.status_code}: {e.response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ToolExecutionError(f"Network error during search: {str(e)}")
        except Exception as e:
            raise ToolExecutionError(f"Unexpected error during search: {str(e)}")
    
    def _search_with_serper(self, query: str) -> str:
        """Search using Serper API with improved response handling"""
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query,
            'num': 15
        }
        
        response = self._session.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        return self._format_search_results(query, data)
    
    def _format_search_results(self, query: str, data: Dict[str, Any]) -> str:
        """Format search results into readable text"""
        result_parts = [f"Search results for '{query}':\n"]
        
        # Add organic results
        if 'organic' in data and data['organic']:
            for i, item in enumerate(data['organic'][:MAX_SEARCH_RESULTS], 1):
                title = item.get('title', 'No title')
                link = item.get('link', 'No link')
                snippet = item.get('snippet', 'No description available')
                result_parts.append(f"{i}. {title}\nURL: {link}\nDescription: {snippet}\n")
        
        # Add knowledge graph if available
        if 'knowledgeGraph' in data:
            kg = data['knowledgeGraph']
            title = kg.get('title', '')
            description = kg.get('description', '')
            if title and description:
                result_parts.append(f"Knowledge Graph: {title} - {description}\n")
        
        return "\n".join(result_parts).strip()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }

class WeatherTool(Tool):
    """Enhanced weather tool with better error handling and validation"""
    
    def __init__(self, api_key: str, timeout: float = DEFAULT_REQUEST_TIMEOUT):
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required for the WeatherTool")
        
        self.api_key = api_key
        self._session = requests.Session()
        
        super().__init__(
            name="get_weather",
            description="Get current weather and forecast for a location",
            function=self._get_weather,
            timeout=timeout
        )
        
        self.add_example({"name": "get_weather", "args": {"location": "New York"}})
        self.add_example({"name": "get_weather", "args": {"location": "London, UK"}})
    
    def _validate_args(self, args: Dict[str, Any]) -> None:
        """Validate weather arguments"""
        super()._validate_args(args)
        
        location = self._extract_location(args)
        if not location:
            raise ToolValidationError("No location provided. Please specify a city or location.")
    
    def _extract_location(self, args: Dict[str, Any]) -> Optional[str]:
        """Extract location from various possible parameter names"""
        for param_name in ["location", "city", "place", "loc"]:
            if param_name in args and args[param_name]:
                return str(args[param_name]).strip()
        return None
    
    def _get_weather(self, args: Dict[str, Any]) -> str:
        """Get weather information with improved error handling"""
        logger.debug(f"WeatherTool._get_weather called with args: {args}")
        
        location = self._extract_location(args)
        locations = self._parse_locations(location)
        
        if len(locations) > 1:
            weather_results = []
            for loc in locations:
                try:
                    result = self._fetch_weather_for_location(loc)
                    weather_results.append(result)
                except Exception as e:
                    weather_results.append(f"Error getting weather for {loc}: {str(e)}")
            return "\n\n".join(weather_results)
        else:
            return self._fetch_weather_for_location(locations[0])
    
    def _parse_locations(self, location_str: str) -> List[str]:
        """Parse multiple locations from input string"""
        if not isinstance(location_str, str):
            logger.warning(f"Invalid location type: {type(location_str)}, converting to string")
            location_str = str(location_str)
        
        # Split on common delimiters
        if " and " in location_str.lower():
            locations = [loc.strip() for loc in location_str.lower().split(" and ")]
        elif "," in location_str and " and " not in location_str.lower():
            # Only split on comma if it's not part of "City, Country" format
            parts = location_str.split(",")
            if len(parts) == 2:
                locations = [location_str.strip()]  # Keep as single location
            else:
                locations = [loc.strip() for loc in parts]
        else:
            locations = [location_str.strip()]
        
        valid_locations = [loc for loc in locations if loc]
        logger.debug(f"Parsed locations: {valid_locations}")
        return valid_locations
    
    def _fetch_weather_for_location(self, location: str) -> str:
        """Fetch weather data for a single location"""
        logger.debug(f"Fetching weather for location: {location}")
        
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={quote_plus(location)}&appid={self.api_key}&units=imperial"
        
        try:
            response = self._session.get(current_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            weather_report = self._format_weather_data(data)
            
            # Try to get forecast
            try:
                forecast_data = self._fetch_forecast(location)
                if forecast_data:
                    weather_report += f"\n\n{forecast_data}"
            except Exception as e:
                logger.warning(f"Failed to fetch forecast for {location}: {str(e)}")
            
            logger.debug(f"Weather report for {location}: {weather_report[:100]}...")
            return weather_report
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ToolExecutionError(f"Location '{location}' not found. Please check the spelling or try a different location.")
            elif e.response.status_code == 401:
                raise ToolExecutionError("Invalid API key. Please check your OpenWeatherMap API key.")
            else:
                raise ToolExecutionError(f"HTTP error {e.response.status_code} for location {location}")
                
        except requests.exceptions.RequestException as e:
            raise ToolExecutionError(f"Network error fetching weather for {location}: {str(e)}")
        except KeyError as e:
            raise ToolExecutionError(f"Could not parse weather data for {location}. Missing data: {str(e)}")
        except Exception as e:
            raise ToolExecutionError(f"Unexpected error getting weather for {location}: {str(e)}")
    
    def _format_weather_data(self, data: Dict[str, Any]) -> str:
        """Format weather data into readable text"""
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        weather_desc = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        city_name = data["name"]
        country = data["sys"]["country"]
        
        weather_report = (
            f"Weather in {city_name}, {country}:\n"
            f"• Temperature: {temp}°F (feels like {feels_like}°F)\n"
            f"• Conditions: {weather_desc.capitalize()}\n"
            f"• Humidity: {humidity}%\n"
            f"• Wind Speed: {wind_speed} mph"
        )
        
        # Add optional data if available
        if "clouds" in data:
            weather_report += f"\n• Cloud Cover: {data['clouds']['all']}%"
        if "rain" in data and "1h" in data["rain"]:
            weather_report += f"\n• Rainfall (last hour): {data['rain']['1h']} mm"
        if "snow" in data and "1h" in data["snow"]:
            weather_report += f"\n• Snowfall (last hour): {data['snow']['1h']} mm"
        
        return weather_report
    
    def _fetch_forecast(self, location: str) -> Optional[str]:
        """Fetch forecast data for location"""
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={quote_plus(location)}&appid={self.api_key}&units=imperial&cnt=8"
        
        response = self._session.get(forecast_url, timeout=self.timeout)
        response.raise_for_status()
        forecast_data = response.json()
        
        if "list" not in forecast_data or not forecast_data["list"]:
            return None
        
        forecast_parts = ["Forecast:"]
        for period in forecast_data["list"][:MAX_FORECAST_PERIODS]:
            time_str = period["dt_txt"].split(" ")[1][:5]
            temp = period["main"]["temp"]
            conditions = period["weather"][0]["description"].capitalize()
            forecast_parts.append(f"• {time_str}: {temp}°F, {conditions}")
        
        return "\n".join(forecast_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country (e.g., 'London, UK' or multiple locations like 'Tokyo and New York')"
                    }
                },
                "required": ["location"]
            }
        }

class ToolRegistry:
    """Enhanced tool registry with improved JSON parsing and error handling"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.tools = {}
        self.llm_provider = llm_provider
    
    def register(self, tool: Tool) -> 'ToolRegistry':
        """Register a single tool"""
        if not isinstance(tool, Tool):
            raise ToolValidationError("Only Tool instances can be registered")
        
        self.tools[tool.name] = tool
        if self.llm_provider:
            tool.set_llm_provider(self.llm_provider)
        
        logger.debug(f"Registered tool: {tool.name}")
        return self
    
    def register_all(self, tools: List[Tool]) -> 'ToolRegistry':
        """Register multiple tools"""
        for tool in tools:
            self.register(tool)
        return self
    
    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(name.lower() if name else None)
    
    def get_all(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def find_relevant_tools(self, query: str) -> List[Tool]:
        """Find relevant tools with improved JSON parsing"""
        if not self.llm_provider or not self.tools:
            logger.warning("No LLM provider or tools available, returning empty tool list")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty query provided for tool selection")
            return []
        
        tool_descriptions = "\n".join(
            [f"- {tool.name}: {tool.description}" for tool in self.tools.values()]
        )
        
        selection_prompt = (
            f"Query: {query}\n\n"
            f"Available tools:\n{tool_descriptions}\n\n"
            "Select the most relevant tools for this query. Return a list of tool names in JSON format:\n"
            "[\"tool1\", \"tool2\"]\n"
            "Do not wrap in markdown code blocks. Return only the JSON array."
        )
        
        try:
            response = self.llm_provider.generate(selection_prompt)
            logger.debug(f"LLM response for tool selection: {response[:200]}...")
            
            # Clean and parse JSON response
            tool_names = self._parse_tool_selection_response(response)
            relevant_tools = [self.tools[name] for name in tool_names if name in self.tools]
            
            logger.debug(f"Selected tools for query '{query[:50]}...': {[tool.name for tool in relevant_tools]}")
            return relevant_tools
            
        except Exception as e:
            logger.error(f"Error selecting tools with LLM: {str(e)}, Response: {response}")
            return []
    
    def _parse_tool_selection_response(self, response: str) -> List[str]:
        """Parse tool selection response with robust JSON handling"""
        if not response:
            return []
        
        # Clean the response
        cleaned_response = response.strip()
        
        # Remove markdown code blocks
        cleaned_response = re.sub(r'^```(?:json)?\n?|\n?```$', '', cleaned_response, flags=re.MULTILINE)
        cleaned_response = cleaned_response.strip()
        
        # Try direct JSON parsing
        try:
            tool_names = json.loads(cleaned_response)
            if isinstance(tool_names, list):
                return [str(name) for name in tool_names if isinstance(name, str)]
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON array pattern
        json_pattern = r'\[(?:["\'][^"\']*["\'](?:,\s*)?)*\]'
        match = re.search(json_pattern, cleaned_response)
        if match:
            try:
                tool_names = json.loads(match.group(0))
                if isinstance(tool_names, list):
                    return [str(name) for name in tool_names if isinstance(name, str)]
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract quoted strings
        quoted_strings = re.findall(r'["\']([^"\']+)["\']', cleaned_response)
        if quoted_strings:
            return [name for name in quoted_strings if name in self.tools]
        
        logger.warning(f"Could not parse tool selection response: {response}")
        return []
    
    def find_most_relevant_tool(self, query: str) -> Optional[Tool]:
        """Find the single most relevant tool"""
        tools = self.find_relevant_tools(query)
        if not tools:
            return None
        return max(tools, key=lambda tool: tool.assess_relevance(query))
    
    def get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all tools"""
        if not self.tools:
            return "No tools available."
        
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)
    
    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """Get specification dictionaries for all tools"""
        return [tool.to_dict() for tool in self.tools.values()]

# Keep the existing custom tool import and class for backward compatibility
from aiccel.base_custom_tool import BaseCustomTool

class CustomTool(BaseCustomTool):
    """Example custom tool implementation"""
    
    def __init__(self, llm_provider, custom_param="default_value"):
        super().__init__(
            name="custom_tool",
            description="A custom tool for testing purposes",
            parameters={"type": "object", "properties": {"input": {"type": "string"}}},
            examples=[{"name": "custom_tool", "args": {"input": "test input"}}],
            detection_threshold=0.5,
            llm_provider=llm_provider
        )
        self.custom_param = custom_param

    def _execute(self, args: Dict[str, Any]) -> str:
        input_value = args.get("input", "No input provided")
        return f"Custom tool executed with input: {input_value}, param: {self.custom_param}"