import openai
import google.generativeai as genai
import requests
import json


def parse_ai_response(response_text):
    """
    Parse AI response and return (response_type, content, description).
    Handles single commands, multiple commands, and text responses.
    """
    response_text = response_text.strip()
    
    if response_text.startswith("COMMAND:"):
        lines = response_text.split("\n")
        command = lines[0].replace("COMMAND:", "").strip()
        description = None
        
        for line in lines[1:]:
            if line.startswith("DESCRIPTION:"):
                description = line.replace("DESCRIPTION:", "").strip()
                break
        
        return "command", command, description
        
    elif response_text.startswith("COMMANDS:"):
        # Parse multiple commands
        lines = response_text.split("\n")
        commands = []
        current_command = None
        current_description = None
        
        for line in lines[1:]:  # Skip the "COMMANDS:" line
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a numbered command
            if line.startswith(tuple(f"{i}." for i in range(1, 20))):
                # Save previous command if exists
                if current_command:
                    commands.append({
                        "command": current_command,
                        "description": current_description or "No description provided"
                    })
                
                # Extract new command (remove number prefix)
                current_command = line.split(".", 1)[1].strip()
                current_description = None
                
            elif line.startswith("DESCRIPTION:"):
                current_description = line.replace("DESCRIPTION:", "").strip()
        
        # Add the last command
        if current_command:
            commands.append({
                "command": current_command,
                "description": current_description or "No description provided"
            })
        
        return "commands", commands, None
        
    elif response_text.startswith("TEXT:"):
        text_response = response_text.replace("TEXT:", "").strip()
        return "text", text_response, None
        
    else:
        # Fallback - treat as text response
        return "text", response_text, None


def build_multi_command_prompt(context_text, history_text, message, os_fullname, shell):
    """Build a prompt that supports both single and multiple commands."""
    return f"""{context_text}{history_text}You are Star Shell, an AI assistant that helps users with command line tasks. 

The user said: "{message}"

Analyze this message and respond appropriately:

1. If the user is asking for a SINGLE command to be executed, respond with:
   COMMAND: <the_command_here>
   DESCRIPTION: <explanation_of_what_it_does>

2. If the user is asking for MULTIPLE commands to be executed in sequence, respond with:
   COMMANDS:
   1. <first_command_here>
   DESCRIPTION: <explanation_of_first_command>
   2. <second_command_here>
   DESCRIPTION: <explanation_of_second_command>
   (continue for more commands...)

3. If the user is asking a question, having a conversation, or needs information, respond with:
   TEXT: <your_natural_language_response>

4. If the user says "help", respond with information about Star Shell capabilities.

Examples of multi-command requests:
- "create a new directory and navigate to it"
- "install dependencies and run the project"
- "backup my files and then clean up temporary files"

Make sure commands work on {os_fullname} using {shell}. Be helpful and conversational."""


class BaseGenie:
    def __init__(self):
        pass

    def ask(self, wish: str, explain: bool = False, context: dict = None):
        raise NotImplementedError
    
    def chat(self, message: str, context: dict = None):
        """
        Generate a conversational response that can be either a command or natural language.
        Returns (response_type, content, description) where:
        - response_type: 'command', 'commands', or 'text'
        - content: the command(s) or natural language response
        - description: explanation (for commands) or None (for text)
        
        For multiple commands, content will be a list of command dictionaries:
        [{"command": "cmd1", "description": "desc1"}, {"command": "cmd2", "description": "desc2"}]
        """
        raise NotImplementedError

    def post_execute(
        self, wish: str, explain: bool, command: str, description: str, feedback: bool
    ):
        pass


class OpenAIGenie(BaseGenie):
    def __init__(self, api_key: str, os_fullname: str, shell: str):
        self.os_fullname = os_fullname
        self.shell = shell
        openai.api_key = api_key

    def _build_prompt(self, wish: str, explain: bool = False, context: dict = None):
        explain_text = ""
        format_text = "Command: <insert_command_here>"

        if explain:
            explain_text = (
                "Also, provide a detailed description of how the command works."
            )
            format_text += "\nDescription: <insert_description_here>\nThe description should be in the same language the user is using."
        format_text += "\nDon't enclose the command with extra quotes or backticks."

        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        # Add conversation history if available
        history_text = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            history_lines = ["Recent conversation:"]
            for msg in context["conversation_history"][-6:]:  # Last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines) + "\n\n"

        prompt_list = [
            context_text,
            history_text,
            f"Instructions: Write a CLI command that does the following: {wish}. Make sure the command is correct and works on {self.os_fullname} using {self.shell}. {explain_text}",
            "Format:",
            format_text,
            "Make sure you use the format exactly as it is shown above.",
        ]
        prompt = "\n\n".join([p for p in prompt_list if p])  # Filter out empty strings
        return prompt

    def ask(self, wish: str, explain: bool = False, context: dict = None):
        prompt = self._build_prompt(wish, explain, context)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You're a command line tool that generates CLI commands for the user.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300 if explain else 180,
            temperature=0,
        )
        responses_processed = (
            response["choices"][0]["message"]["content"].strip().split("\n")
        )
        responses_processed = [
            x.strip() for x in responses_processed if len(x.strip()) > 0
        ]
        command = responses_processed[0].replace("Command:", "").strip()

        if command[0] == command[-1] and command[0] in ["'", '"', "`"]:
            command = command[1:-1]

        description = None
        if explain:
            description = responses_processed[1].split("Description: ")[1]

        return command, description
    
    def chat(self, message: str, context: dict = None):
        """Generate conversational response for OpenAI."""
        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        # Add conversation history if available
        history_text = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            history_lines = ["Recent conversation:"]
            for msg in context["conversation_history"][-6:]:  # Last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines) + "\n\n"

        prompt = f"""{context_text}{history_text}You are Star Shell, an AI assistant that helps users with command line tasks. 

The user said: "{message}"

Analyze this message and respond appropriately:

1. If the user is asking for a command to be executed, respond with:
   COMMAND: <the_command_here>
   DESCRIPTION: <explanation_of_what_it_does>

2. If the user is asking a question, having a conversation, or needs information, respond with:
   TEXT: <your_natural_language_response>

3. If the user says "help", respond with information about Star Shell capabilities.

Make sure commands work on {self.os_fullname} using {self.shell}. Be helpful and conversational."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are Star Shell, a helpful AI assistant for command line tasks. Respond naturally and be helpful.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        
        response_text = response["choices"][0]["message"]["content"].strip()
        
        # Use the helper function to parse the response
        return parse_ai_response(response_text)





class GeminiGenie(BaseGenie):
    def __init__(self, api_key: str, os_fullname: str, shell: str, backend_type: str = "gemini-pro"):
        self.os_fullname = os_fullname
        self.shell = shell
        self.api_key = api_key
        self.backend_type = backend_type
        genai.configure(api_key=api_key)
        
        # Choose model based on backend type
        if backend_type == "gemini-flash":
            model_name = 'gemini-2.0-flash-exp'
        elif backend_type == "gemini-thinking":
            model_name = 'gemini-2.5-pro'  # Use Pro for thinking mode
        else:
            model_name = 'gemini-2.5-pro'
            
        self.model = genai.GenerativeModel(model_name)

    def validate_credentials(self) -> bool:
        """Validate the Gemini API key by making a test request."""
        try:
            # Make a simple test request to validate the API key
            test_response = self.model.generate_content("Hello")
            return test_response is not None
        except Exception as e:
            # API key is invalid or there's a connection issue
            return False

    def _build_prompt(self, wish: str, explain: bool = False, context: dict = None):
        explain_text = ""
        format_text = "Command: <insert_command_here>"

        if explain:
            explain_text = (
                "Also, provide a detailed description of how the command works."
            )
            format_text += "\nDescription: <insert_description_here>\nThe description should be in the same language the user is using."
        format_text += "\nDon't enclose the command with extra quotes or backticks."

        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        # Add conversation history if available
        history_text = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            history_lines = ["Recent conversation:"]
            for msg in context["conversation_history"][-6:]:  # Last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines) + "\n\n"

        prompt_list = [
            context_text,
            history_text,
            f"Instructions: Write a CLI command that does the following: {wish}. Make sure the command is correct and works on {self.os_fullname} using {self.shell}. {explain_text}",
            "Format:",
            format_text,
            "Make sure you use the format exactly as it is shown above.",
        ]
        prompt = "\n\n".join([p for p in prompt_list if p])  # Filter out empty strings
        return prompt

    def _make_api_request(self, prompt: str) -> str:
        """Make API request to Gemini Pro and return the response text."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise ValueError(f"Error communicating with Gemini API: {str(e)}")

    def ask(self, wish: str, explain: bool = False, context: dict = None):
        prompt = self._build_prompt(wish, explain, context)
        
        try:
            response_text = self._make_api_request(prompt)
            
            # Parse the response similar to OpenAI implementation
            responses_processed = response_text.strip().split("\n")
            responses_processed = [
                x.strip() for x in responses_processed if len(x.strip()) > 0
            ]
            
            if not responses_processed:
                raise ValueError("Empty response from Gemini API")
            
            command = responses_processed[0].replace("Command:", "").strip()

            # Remove quotes if they wrap the entire command
            if command and command[0] == command[-1] and command[0] in ["'", '"', "`"]:
                command = command[1:-1]

            description = None
            if explain and len(responses_processed) > 1:
                for line in responses_processed[1:]:
                    if "Description:" in line:
                        description = line.split("Description:", 1)[1].strip()
                        break

            return command, description
            
        except Exception as e:
            raise ValueError(f"Error processing Gemini response: {str(e)}")
    
    def chat(self, message: str, context: dict = None):
        """Generate conversational response for Gemini."""
        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        # Add conversation history if available
        history_text = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            history_lines = ["Recent conversation:"]
            for msg in context["conversation_history"][-6:]:  # Last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines) + "\n\n"

        prompt = f"""{context_text}{history_text}You are Star Shell, an AI assistant that helps users with command line tasks. 

The user said: "{message}"

Analyze this message and respond appropriately:

1. If the user is asking for a command to be executed, respond with:
   COMMAND: <the_command_here>
   DESCRIPTION: <explanation_of_what_it_does>

2. If the user is asking a question, having a conversation, or needs information, respond with:
   TEXT: <your_natural_language_response>

3. If the user says "help", respond with information about Star Shell capabilities.

Make sure commands work on {self.os_fullname} using {self.shell}. Be helpful and conversational."""

        try:
            response_text = self._make_api_request(prompt)
            
            # Parse the response
            if response_text.startswith("COMMAND:"):
                lines = response_text.split("\n")
                command = lines[0].replace("COMMAND:", "").strip()
                description = None
                
                for line in lines[1:]:
                    if line.startswith("DESCRIPTION:"):
                        description = line.replace("DESCRIPTION:", "").strip()
                        break
                
                return "command", command, description
            elif response_text.startswith("TEXT:"):
                text_response = response_text.replace("TEXT:", "").strip()
                return "text", text_response, None
            else:
                # Fallback - treat as text response
                return "text", response_text, None
                
        except Exception as e:
            raise ValueError(f"Error processing Gemini chat response: {str(e)}")


class GeminiThinkingGenie(BaseGenie):
    """Gemini with adaptive thinking - creates plans and executes step by step"""
    
    def __init__(self, api_key: str, os_fullname: str, shell: str):
        self.os_fullname = os_fullname
        self.shell = shell
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.current_plan = None
        self.current_step = 0
        self.execution_history = []
    
    def validate_credentials(self) -> bool:
        """Validate the Gemini API key by making a test request."""
        try:
            test_response = self.model.generate_content("Hello")
            return test_response is not None
        except Exception:
            return False
    
    def _make_api_request(self, prompt: str) -> str:
        """Make API request to Gemini Pro and return the response text."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise ValueError(f"Error communicating with Gemini API: {str(e)}")
    
    def create_plan(self, user_request: str, context: dict = None) -> list:
        """Create a step-by-step plan for the user's request."""
        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        planning_prompt = f"""{context_text}You are Star Shell, an AI assistant that creates step-by-step execution plans.

User Request: "{user_request}"

Create a detailed step-by-step plan to fulfill this request. Each step should be a single, specific action that can be executed independently.

Respond with a numbered list in this format:
PLAN:
1. [Brief description of step 1]
2. [Brief description of step 2]
3. [Brief description of step 3]
...

Guidelines:
- Each step should be atomic and executable
- Steps should build on previous steps
- Consider the current context and environment
- Be specific about what each step accomplishes
- Maximum 10 steps for clarity

Make sure all steps work on {self.os_fullname} using {self.shell}."""

        try:
            response = self._make_api_request(planning_prompt)
            
            # Parse the plan
            if "PLAN:" in response:
                plan_text = response.split("PLAN:")[1].strip()
                steps = []
                
                for line in plan_text.split("\n"):
                    line = line.strip()
                    if line and line[0].isdigit() and "." in line:
                        step_desc = line.split(".", 1)[1].strip()
                        steps.append(step_desc)
                
                return steps
            else:
                # Fallback parsing
                lines = response.strip().split("\n")
                steps = []
                for line in lines:
                    line = line.strip()
                    if line and line[0].isdigit() and "." in line:
                        step_desc = line.split(".", 1)[1].strip()
                        steps.append(step_desc)
                return steps
                
        except Exception as e:
            raise ValueError(f"Error creating plan: {str(e)}")
    
    def execute_next_step(self, context: dict = None) -> tuple:
        """Execute the next step in the plan based on current context and history."""
        if not self.current_plan or self.current_step >= len(self.current_plan):
            return "text", "Plan completed or no plan available.", None
        
        current_step_desc = self.current_plan[self.current_step]
        
        # Build context with execution history
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"
        
        # Add execution history
        history_text = ""
        if self.execution_history:
            history_text = "Previous Steps Executed:\n"
            for i, hist in enumerate(self.execution_history, 1):
                history_text += f"{i}. Command: {hist['command']}\n"
                if hist['success']:
                    history_text += f"   Result: Success - {hist['output'][:100]}...\n"
                else:
                    history_text += f"   Result: Failed - {hist['error'][:100]}...\n"
            history_text += "\n"
        
        execution_prompt = f"""{context_text}{history_text}You are executing step {self.current_step + 1} of a plan.

Current Step: "{current_step_desc}"

Full Plan Context:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(self.current_plan)])}

Based on the current context and previous execution results, generate the specific command to execute this step.

Respond with:
COMMAND: <the_specific_command_to_run>
DESCRIPTION: <brief explanation of what this command does>

Make sure the command works on {self.os_fullname} using {self.shell} and considers the current state."""

        try:
            response = self._make_api_request(execution_prompt)
            response_type, content, description = parse_ai_response(response)
            
            if response_type == "command":
                return response_type, content, description
            else:
                # If AI doesn't return a command, treat as completion
                return "text", f"Step {self.current_step + 1} completed: {current_step_desc}", None
                
        except Exception as e:
            raise ValueError(f"Error executing step: {str(e)}")
    
    def record_execution(self, command: str, success: bool, output: str = "", error: str = ""):
        """Record the result of command execution."""
        self.execution_history.append({
            'step': self.current_step,
            'command': command,
            'success': success,
            'output': output,
            'error': error
        })
        self.current_step += 1
    
    def reset_plan(self):
        """Reset the current plan and execution state."""
        self.current_plan = None
        self.current_step = 0
        self.execution_history = []
    
    def ask(self, wish: str, explain: bool = False, context: dict = None):
        """For compatibility - delegates to regular Gemini behavior."""
        # Use regular Gemini logic for simple ask requests
        return super().ask(wish, explain, context)
    
    def chat(self, message: str, context: dict = None):
        """Enhanced chat that can create plans and execute them step by step."""
        # Check if this is a request that needs planning
        if self._needs_planning(message):
            # Create a new plan
            self.reset_plan()
            try:
                self.current_plan = self.create_plan(message, context)
                if self.current_plan:
                    plan_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(self.current_plan)])
                    return "plan", {
                        "plan": self.current_plan,
                        "description": f"Created execution plan with {len(self.current_plan)} steps:\n{plan_text}"
                    }, None
                else:
                    return "text", "I couldn't create a plan for that request. Could you be more specific?", None
            except Exception as e:
                return "text", f"Error creating plan: {str(e)}", None
        else:
            # Use regular chat for simple questions/conversations
            return parse_ai_response(self._make_api_request(
                build_multi_command_prompt("", "", message, self.os_fullname, self.shell)
            ))
    
    def _needs_planning(self, message: str) -> bool:
        """Determine if a message needs multi-step planning."""
        planning_keywords = [
            "create", "setup", "install", "build", "deploy", "configure", 
            "initialize", "prepare", "organize", "clean up", "backup",
            "and then", "after that", "next", "followed by", "step by step"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in planning_keywords) or len(message.split()) > 8


class ProxyGenie(BaseGenie):
    """Genie that uses the Star Shell backend proxy service"""
    
    def __init__(self, backend_url: str, secret_token: str, os_fullname: str, shell: str, model_type: str = "gemini-pro"):
        self.backend_url = backend_url.rstrip('/')
        self.secret_token = secret_token
        self.os_fullname = os_fullname
        self.shell = shell
        self.model_type = model_type
        
        # Map model types to actual model names
        self.model_map = {
            "gemini-pro": "gemini-2.5-pro",
            "gemini-flash": "gemini-2.0-flash-exp"
        }
    
    def validate_credentials(self) -> bool:
        """Validate connection to the proxy service."""
        try:
            response = requests.get(
                f"{self.backend_url}/health",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _make_proxy_request(self, prompt: str, max_tokens: int = 400, temperature: float = 0.3) -> str:
        """Make a request to the proxy service."""
        model_name = self.model_map.get(self.model_type, "gemini-2.5-pro")
        
        headers = {
            'Authorization': f'Bearer {self.secret_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'prompt': prompt,
            'model': model_name,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/generate",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'error': response.text}
                raise ValueError(f"Proxy service error: {error_data.get('error', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to proxy service: {str(e)}")
    
    def ask(self, wish: str, explain: bool = False, context: dict = None):
        """Generate command using the proxy service."""
        # Build the same prompt structure as GeminiGenie
        explain_text = ""
        format_text = "Command: <insert_command_here>"

        if explain:
            explain_text = (
                "Also, provide a detailed description of how the command works."
            )
            format_text += "\nDescription: <insert_description_here>\nThe description should be in the same language the user is using."
        format_text += "\nDon't enclose the command with extra quotes or backticks."

        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        # Add conversation history if available
        history_text = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            history_lines = ["Recent conversation:"]
            for msg in context["conversation_history"][-6:]:  # Last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines) + "\n\n"

        prompt_list = [
            context_text,
            history_text,
            f"Instructions: Write a CLI command that does the following: {wish}. Make sure the command is correct and works on {self.os_fullname} using {self.shell}. {explain_text}",
            "Format:",
            format_text,
            "Make sure you use the format exactly as it is shown above.",
        ]
        prompt = "\n\n".join([p for p in prompt_list if p])  # Filter out empty strings
        
        try:
            response_text = self._make_proxy_request(prompt, max_tokens=300 if explain else 180)
            
            # Parse the response similar to GeminiGenie implementation
            responses_processed = response_text.strip().split("\n")
            responses_processed = [
                x.strip() for x in responses_processed if len(x.strip()) > 0
            ]
            
            if not responses_processed:
                raise ValueError("Empty response from proxy service")
            
            command = responses_processed[0].replace("Command:", "").strip()

            # Remove quotes if they wrap the entire command
            if command and command[0] == command[-1] and command[0] in ["'", '"', "`"]:
                command = command[1:-1]

            description = None
            if explain and len(responses_processed) > 1:
                for line in responses_processed[1:]:
                    if "Description:" in line:
                        description = line.split("Description:", 1)[1].strip()
                        break

            return command, description
            
        except Exception as e:
            raise ValueError(f"Error processing proxy response: {str(e)}")
    
    def chat(self, message: str, context: dict = None):
        """Generate conversational response using the proxy service."""
        # Build context information
        context_text = ""
        if context:
            context_lines = [
                "Current Context:",
                f"- Working Directory: {context.get('current_directory', 'Unknown')}",
                f"- OS: {context.get('system_info', {}).get('os', self.os_fullname)}",
                f"- Shell: {context.get('system_info', {}).get('shell_name', self.shell)}",
            ]
            
            if "directory_contents" in context and context["directory_contents"]:
                contents_preview = ", ".join(context["directory_contents"][:10])
                if len(context["directory_contents"]) > 10:
                    contents_preview += "..."
                context_lines.append(f"- Directory Contents: {contents_preview}")
            
            context_text = "\n".join(context_lines) + "\n\n"

        # Add conversation history if available
        history_text = ""
        if context and "conversation_history" in context and context["conversation_history"]:
            history_lines = ["Recent conversation:"]
            for msg in context["conversation_history"][-6:]:  # Last 3 exchanges
                role_label = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg['content']}")
            history_text = "\n".join(history_lines) + "\n\n"

        prompt = f"""{context_text}{history_text}You are Star Shell, an AI assistant that helps users with command line tasks. 

The user said: "{message}"

Analyze this message and respond appropriately:

1. If the user is asking for a command to be executed, respond with:
   COMMAND: <the_command_here>
   DESCRIPTION: <explanation_of_what_it_does>

2. If the user is asking a question, having a conversation, or needs information, respond with:
   TEXT: <your_natural_language_response>

3. If the user says "help", respond with information about Star Shell capabilities.

Make sure commands work on {self.os_fullname} using {self.shell}. Be helpful and conversational."""

        try:
            response_text = self._make_proxy_request(prompt, max_tokens=400, temperature=0.3)
            
            # Parse the response
            if response_text.startswith("COMMAND:"):
                lines = response_text.split("\n")
                command = lines[0].replace("COMMAND:", "").strip()
                description = None
                
                for line in lines[1:]:
                    if line.startswith("DESCRIPTION:"):
                        description = line.replace("DESCRIPTION:", "").strip()
                        break
                
                return "command", command, description
            elif response_text.startswith("TEXT:"):
                text_response = response_text.replace("TEXT:", "").strip()
                return "text", text_response, None
            else:
                # Fallback - treat as text response
                return "text", response_text, None
                
        except Exception as e:
            raise ValueError(f"Error processing proxy chat response: {str(e)}")