import json
from typing import Optional, List, Dict, Callable


class LLMService:
    """
    Provider-agnostic LLM interface with tool support.
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        tools: Optional[List[dict]] = None,
        tool_map: Optional[Dict[str, Callable]] = None,
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.tools = tools or []
        self.tool_map = tool_map or {}

    async def generate(self, prompt: str) -> str:
        if not self.client:
            return "LLM_GENERATED_TEXT"

        messages = [
            {"role": "system", "content": "You are a compliance intelligence system."},
            {"role": "user", "content": prompt},
        ]

        while True:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else "none",
            )

            choice = completion.choices[0]
            finish_reason = choice.finish_reason

            # Tool execution loop
            if finish_reason == "tool_calls":
                messages.append(choice.message)

                for tool_call in choice.message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if name not in self.tool_map:
                        raise RuntimeError(f"Unknown tool: {name}")

                    # NOTE: Assuming tools are synchronous for now, 
                    # can be updated to async if tools become async
                    result = self.tool_map[name](**args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(result),
                    })

                continue

            # Final answer
            return choice.message.content.strip()

    def _extract_json_from_text(self, text: str) -> dict:
        """Extract JSON from text that might be wrapped in markdown code blocks."""
        import re
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Try multiple patterns for code blocks
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
            r'(\{[\s\S]*\})',                # Direct JSON object
            r'(\[[\s\S]*\])',                # Direct JSON array
        ]
        
        all_matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                all_matches.append(match.group(1).strip())
        
        # Sort by length descending - try biggest block first
        all_matches.sort(key=len, reverse=True)
        
        for json_str in all_matches:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
        
        raise ValueError(f"No valid JSON found in text: {text[:500]}")

    def _create_empty_instance(self, response_model: type) -> dict:
        """Create an empty instance dict with proper types for nested models."""
        from pydantic import BaseModel
        
        result = {}
        schema = response_model.model_json_schema()
        
        for field_name, field_info in schema.get("properties", {}).items():
            field_type = field_info.get("type")
            
            if field_type == "array":
                result[field_name] = []
            elif field_type == "object":
                # Check if it's a nested Pydantic model
                if "$ref" in field_info or "properties" in field_info:
                    result[field_name] = {}
                else:
                    result[field_name] = {}
            elif field_type == "string":
                result[field_name] = ""
            elif field_type in ("integer", "number"):
                result[field_name] = 0
            elif field_type == "boolean":
                result[field_name] = False
            else:
                result[field_name] = None
        
        return result

    async def generate_structured(self, prompt: str, response_model: type) -> object:
        """
        Generates a structured response strictly adhering to the given Pydantic model.
        Uses function calling with robust text-based fallback for Groq compatibility.
        """
        if not self.client:
            raise RuntimeError("LLM client not initialized")

        # Create a tool definition from the Pydantic model
        schema = response_model.model_json_schema()
        tool_name = f"generate_{response_model.__name__.lower()}"
        
        tools = [{
            "type": "function",
            "function": {
                "name": tool_name,
                "description": f"Generates a structured {response_model.__name__}",
                "parameters": schema
            }
        }]

        # Create example JSON from schema
        example_fields = self._create_empty_instance(response_model)
        example_json = json.dumps(example_fields, indent=2)

        # Enhanced prompt for Groq compatibility
        enhanced_prompt = f"""{prompt}

CRITICAL OUTPUT FORMAT - Use EXACTLY these field names:
{example_json}

Requirements:
- Output ONLY raw JSON
- NO markdown code blocks
- NO explanatory text
- Match field names EXACTLY as shown above"""

        messages = [
            {"role": "system", "content": "You are a compliance intelligence system. Output ONLY valid JSON matching the exact schema provided. Never use markdown formatting or additional text."},
            {"role": "user", "content": enhanced_prompt}
        ]

        try:
            # Primary: Try function calling
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": tool_name}}
            )

            choice = completion.choices[0]
            
            if choice.message.tool_calls:
                tool_call = choice.message.tool_calls[0]
                arguments = json.loads(tool_call.function.arguments)
                return response_model(**arguments)
            
            raise ValueError("No tool call in response")
            
        except Exception as e:
            # Secondary: Text-based parsing with improved error handling
            try:
                completion = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0
                )
                
                text = completion.choices[0].message.content.strip()
                data = self._extract_json_from_text(text)
                
                # Handle array responses for models expecting 'items' field
                if isinstance(data, list) and hasattr(response_model, 'model_fields'):
                    if 'items' in response_model.model_fields:
                        data = {"items": data}
                
                # Deep cleansing and auto-correction for complex models
                if isinstance(data, dict):
                    import inspect
                    
                    # 1. Cleanse stringified JSON inside dict
                    for key, value in list(data.items()):
                        if isinstance(value, str) and value.strip().startswith("{"):
                            try:
                                data[key] = json.loads(value)
                            except:
                                pass
                    
                    # 2. Field-level auto-correction based on Pydantic fields
                    if hasattr(response_model, "model_fields"):
                         from typing import get_args, get_origin, Union
                         from pydantic import BaseModel
                         
                         for field_name, field_info in response_model.model_fields.items():
                            val = data.get(field_name)
                            annotation = field_info.annotation
                            
                            # Helper to find BaseModel in Optional/Union
                            def find_base_model(typ):
                                if inspect.isclass(typ) and issubclass(typ, BaseModel):
                                    return typ
                                origin = get_origin(typ)
                                if origin is Union or (hasattr(Union, "__pydantic_generic_metadata__") and origin is Union): # Handle Union/Optional
                                    for arg in get_args(typ):
                                        res = find_base_model(arg)
                                        if res: return res
                                return None

                            target_model = find_base_model(annotation)
                                
                            if target_model and isinstance(val, str) and val.strip():
                                # Wrap string in a dict for the nested model (assuming 'url' or 'degree' or 'value' is primary)
                                nested_fields = target_model.model_fields
                                primary_keys = ["url", "degree", "name", "value"]
                                for pk in primary_keys:
                                    if pk in nested_fields:
                                        data[field_name] = {pk: val.strip()}
                                        break
                                    
                            # Case: List[Model] but got a list of strings (e.g. items=["1979..."])
                            elif isinstance(val, list) and val:
                                origin = get_origin(annotation)
                                args = get_args(annotation)
                                
                                if origin is list and args:
                                    inner_type = args[0]
                                    inner_model = find_base_model(inner_type)
                                    
                                    if inner_model:
                                        new_list = []
                                        nested_fields = inner_model.model_fields
                                        primary_keys = ["degree", "name", "value", "url"]
                                        
                                        for item in val:
                                            if isinstance(item, str):
                                                # Find a primary key to map this string to
                                                mapped = False
                                                for pk in primary_keys:
                                                    if pk in nested_fields:
                                                        new_list.append({pk: item})
                                                        mapped = True
                                                        break
                                                if not mapped:
                                                    # Try to use any required string field
                                                    for fn, fi in nested_fields.items():
                                                        if fi.is_required() and fi.annotation is str:
                                                            new_list.append({fn: item})
                                                            mapped = True
                                                            break
                                            else:
                                                new_list.append(item)
                                        data[field_name] = new_list

                                # Case: List[str] but got a list of dicts (e.g. items=[{"name": "..."}])
                                elif origin is list and str in args:
                                    new_list = []
                                    for item in val:
                                        if isinstance(item, str):
                                            new_list.append(item)
                                        elif isinstance(item, dict):
                                            v = item.get("name") or item.get("value") or next(iter(item.values()), str(item))
                                            new_list.append(str(v))
                                    data[field_name] = new_list

                return response_model(**data)
                
            except Exception as fallback_error:
                # Tertiary: Graceful degradation with logging
                import logging
                logger = logging.getLogger(__name__)
                
                # Log raw text for debugging if available
                raw_text_snippet = str(text)[:1000] if 'text' in locals() else "No text received"
                
                logger.warning(
                    f"[LLM] Complete failure for {response_model.__name__}.\n"
                    f"Function calling error: {str(e)[:100]}\n"
                    f"Text parsing error: {str(fallback_error)[:100]}\n"
                    f"RAW TEXT FROM LLM:\n{raw_text_snippet}\n"
                    f"--- END RAW TEXT ---"
                )
                
                # Return valid empty instance
                return response_model(**example_fields)
