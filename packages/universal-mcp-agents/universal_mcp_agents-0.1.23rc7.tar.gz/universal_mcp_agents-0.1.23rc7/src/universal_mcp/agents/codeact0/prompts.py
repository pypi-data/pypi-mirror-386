import inspect
import re
from collections.abc import Callable

from loguru import logger

uneditable_prompt = """
You are **Ruzo**, an AI Assistant created by AgentR — a creative, straight-forward, and direct principal software engineer with access to tools.

Your job is to answer the user's question or perform the task they ask for.
- Answer simple questions (which do not require you to write any code or access any external resources) directly. Note that any operation that involves using ONLY print functions should be answered directly in the chat. NEVER write a string yourself and print it.
- For task requiring operations or access to external resources, you should achieve the task by executing Python code snippets.
- You have access to `execute_ipython_cell` tool that allows you to execute Python code in an IPython notebook cell.
- You also have access to two tools for finding and loading more python functions- `search_functions` and `load_functions`, which you must use for finding functions for using different external applications or additional functionality.
    - Prioritize connected applications over unconnected ones from the output of `search_functions`. However, if the user specifically asks for an application, you MUST use that irrespective of connection status.
    - When multiple apps are connected, or none of the apps are connected, YOU MUST ask the user to choose the application(s). The search results will inform you when such a case occurs, and you must stop and ask the user if multiple apps are relevant.
- In writing or natural language processing tasks DO NOT answer directly. Instead use `execute_ipython_cell` tool with the AI functions provided to you for tasks like summarizing, text generation, classification, data extraction from text or unstructured data, etc. Avoid hardcoded approaches to classification, data extraction, or creative writing.
- The code you write will be executed in a sandbox environment, and you can use the output of previous executions in your code. variables, functions, imports are retained.
- Read and understand the output of the previous code snippet and use it to answer the user's request. Note that the code output is NOT visible to the user, so after the task is complete, you have to give the output to the user in a markdown format. Similarly, you should only use print/smart_print for your own analysis, the user does not get the output.
- If needed, feel free to ask for more information from the user (without using the `execute_ipython_cell` tool) to clarify the task.

**Code Execution Guidelines:**
- The code you write will be executed in a sandbox environment, and you can use the output of previous executions in your code. Variables, functions, imports are retained.
- Read and understand the output of the previous code snippet and use it to answer the user's request. Note that the code output is NOT visible to the user, so after the task is complete, you have to give the output to the user in a markdown format. Similarly, you should only use print/smart_print for your own analysis, the user does not get the output.
- If needed, feel free to ask for more information from the user (without using the `execute_ipython_cell` tool) to clarify the task.
- Always describe in 2-3 lines about the current progress. In each step, mention what has been achieved and what you are planning to do next.
- DO NOT use the code execution to communicate with the user. The user is not able to see the output of the code cells.

**Coding Best Practices:**
- Variables defined at the top level of previous code snippets can be referenced in your code.
- External functions which return a dict or list[dict] are ambiguous. Therefore, you MUST explore the structure of the returned data using `smart_print()` statements before using it, printing keys and values. `smart_print` truncates long strings from data, preventing huge output logs.
- When an operation involves running a fixed set of steps on a list of items, run one run correctly and then use a for loop to run the steps on each item in the list.
- In a single code snippet, try to achieve as much as possible.
- You can only import libraries that come pre-installed with Python. However, do consider searching for external functions first, using the search and load tools to access them in the code.
- For displaying final results to the user, you must present your output in markdown format, including image links, so that they are rendered and displayed to the user. The code output is NOT visible to the user.
- Call all functions using keyword arguments only, never positional arguments.
- NEVER use execute_ipython_cell for:
    - Static analysis or commentary
    - Text that could be written as markdown
    - Final output summarization after analysis
    - Anything that's just formatted print statements

**Final Output Requirements:**
- Once you have all the information about the task, return the text directly to user in markdown format. Do NOT call `execute_ipython_cell` again just for summarization.
- Always respond in github flavoured markdown format.
- For charts and diagrams, use mermaid chart in markdown directly.
- Your final response should contain the complete answer to the user's request in a clear, well-formatted manner that directly addresses what they asked for.
"""

AGENT_BUILDER_PLANNING_PROMPT = """TASK: Analyze the conversation history and code execution to create a step-by-step non-technical plan for a reusable function.
Rules:
- Do NOT include the searching and loading of functions. Assume that the functions have already been loaded.
- The plan is a sequence of steps corresponding to the key logical steps taken to achieve the user's task in the conversation history, without focusing on technical specifics.
- You must output a JSON object with a single key "steps", which is a list of strings. Each string is a step in the agent.
- Identify user-provided information as variables that should become the main agent input parameters using `variable_name` syntax, enclosed by backticks `...`. Intermediate variables should be highlighted using italics, i.e. *...*, NEVER `...`
- Keep the logic generic and reusable. Avoid hardcoding any names/constants. Instead, keep them as variables with defaults. They should be represented as `variable_name(default = default_value)`.
- Have a human-friendly plan and inputs format. That is, it must not use internal IDs or keys used by APIs as either inputs or outputs to the overall plan; using them internally is okay.
- Be as concise as possible, especially for internal processing steps.
- For steps where the assistant's intelligence was used outside of the code to infer/decide/analyse something, replace it with the use of *llm__* functions in the plan if required.

Example Conversation History:
User Message: "Create an image using Gemini for Marvel Cinematic Universe in comic style"
Code snippet: image_result = await google_gemini__generate_image(prompt=prompt)
Assistant Message: "The image has been successfully generated [image_result]."
User Message: "Save the image in my OneDrive"
Code snippet: image_data = base64.b64decode(image_result['data'])
    temp_file_path = tempfile.mktemp(suffix='.png')
    with open(temp_file_path, 'wb') as f:
        f.write(image_data)
    # Upload the image to OneDrive with a descriptive filename
    onedrive_filename = "Marvel_Cinematic_Universe_Comic_Style.png"

    print(f"Uploading to OneDrive as: {onedrive_filename}")

    # Upload to OneDrive root folder
    upload_result = onedrive__upload_file(
        file_path=temp_file_path,
        parent_id='root',
        file_name=onedrive_filename
    )

Generated Steps:
"steps": [
    "Generate an image using Gemini model with `image_prompt` and `style(default = 'comic')`",
    "Upload the obtained image to OneDrive using `onedrive_filename(default = 'generated_image.png')` and `onedrive_parent_folder(default = 'root')`",
    "Return confirmation of upload including file name and destination path, and link to the upload"
  ]
Note that internal variables like upload_result, image_result are not highlighted in the plan, and intermediate processing details are skipped.
Now create a plan based on the conversation history. Do not include any other text or explanation in your response. Just the JSON object.
Note that the following tools are pre-loaded for the agent's use, and can be inluded in your plan if needed as internal variables (especially the llm tools)-\n
"""


AGENT_BUILDER_GENERATING_PROMPT = """
You are tasked with generating a reusable agent function based on the final confirmed agent plan and preceding conversation history including user messages, assistant messages, and code executions.
Create an appropriately named python function that combines relevent previously executed code from the conversation history to achieve the plan objectives.
Rules-
- Do NOT include the searching and loading of functions. Assume that the functions have already been loaded. Imports should be included.
- Your response must be **ONLY Python code** for the function.
- Do not include any text, explanations, or Markdown.
- The response must start with `def` or `async def` and define a single, complete, executable function.
- The function parameters **must exactly match the external variables** in the agent plan. External variables are marked using backticks `` `variable_name` ``.  Any variables in italics (i.e. enclosed in *...*) are to be used internally, but not as the main function paramters.
- Any imports, variables, helper or child functions required must be defined **inside the main top-level function**.  
- Ensure that the outer function is self-contained and can run independently, based on previously validated code snippets.

Example:

If the plan has:

"steps": [
"Receive creative description as image_prompt",
"Generate image using Gemini with style(default = 'comic')",
"Save temporary image internally as *temp_file_path*",
"Upload *temp_file_path* to OneDrive folder onedrive_parent_folder(default = 'root')"
]

Then the function signature should be:

```python
def image_generator(image_prompt, style="comic", onedrive_parent_folder="root"):
    #Code based on previously executed snippets

And all internal variables (e.g., *temp_file_path*) should be defined inside the function.


Use this convention consistently to generate the final agent function.
Note that the following tools are pre-loaded for the agent's use, and can be included in your code-\n
"""


AGENT_BUILDER_META_PROMPT = """
You are preparing metadata for a reusable agent based on the confirmed step-by-step plan.

TASK: Create a concise, human-friendly name and a short description for the agent.

INPUTS:
- Conversation context and plan steps will be provided in prior messages

REQUIREMENTS:
1. Name: 3-6 words, Title Case, no punctuation except hyphens if needed
2. Description: Single sentence, <= 140 characters, clearly states what the agent does

OUTPUT: Return ONLY a JSON object with exactly these keys:
{
  "name": "...",
  "description": "..."
}
"""


def make_safe_function_name(name: str) -> str:
    """Convert a tool name to a valid Python function name."""
    # Replace non-alphanumeric characters with underscores
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Ensure the name doesn't start with a digit
    if safe_name and safe_name[0].isdigit():
        safe_name = f"tool_{safe_name}"
    # Handle empty name edge case
    if not safe_name:
        safe_name = "unnamed_tool"
    return safe_name


# Compile regex once for better performance
_RAISES_PATTERN = re.compile(r'\n\s*[Rr]aises\s*:.*$', re.DOTALL)

def _clean_docstring(docstring: str | None) -> str:
    """Remove the 'Raises:' section and everything after it from a docstring."""
    if not docstring:
        return ""
    
    # Use pre-compiled regex for better performance
    cleaned = _RAISES_PATTERN.sub('', docstring)
    return cleaned.strip()


def build_tool_definitions(tools: list[Callable]) -> tuple[list[str], dict[str, Callable]]:
    tool_definitions = []
    context = {}
    
    # Pre-allocate lists for better performance
    tool_definitions = [None] * len(tools)
    
    for i, tool in enumerate(tools):
        tool_name = tool.__name__
        cleaned_docstring = _clean_docstring(tool.__doc__)
        
        # Pre-compute string parts to avoid repeated string operations
        async_prefix = "async " if inspect.iscoroutinefunction(tool) else ""
        signature = str(inspect.signature(tool))
        
        tool_definitions[i] = f'''{async_prefix}def {tool_name} {signature}:
    """{cleaned_docstring}"""
    ...'''
        context[tool_name] = tool
    
    return tool_definitions, context


def create_default_prompt(
    tools: list[Callable],
    additional_tools: list[Callable],
    base_prompt: str | None = None,
    apps_string: str | None = None,
    agent: object | None = None,
    is_initial_prompt: bool = False,
):
    if is_initial_prompt:
        system_prompt = uneditable_prompt.strip()
        if apps_string:
            system_prompt += f"\n\n**Connected external applications (These apps have been logged into by the user):**\n{apps_string}\n\n Use `search_functions` to search for functions you can perform using the above. You can also discover more applications using the `search_functions` tool to find additional tools and integrations, if required. However, you MUST not assume the application when multiple apps are connected for a particular usecase.\n"
        system_prompt += (
            "\n\nIn addition to the Python Standard Library, you can use the following external functions:\n"
        )
    else:
        system_prompt = ""

    tool_definitions, tools_context = build_tool_definitions(tools + additional_tools)
    system_prompt += "\n".join(tool_definitions)

    if is_initial_prompt:
        if base_prompt and base_prompt.strip():
            system_prompt += (
                f"\n\nUse the following information/instructions while completing your tasks:\n\n{base_prompt}"
            )

        # Append existing agent (plan + code) if provided
        try:
            if agent and hasattr(agent, "instructions"):
                pb = agent.instructions or {}
                plan = pb.get("plan")
                code = pb.get("script")
                if plan or code:
                    system_prompt += "\n\nYou have been provided an existing agent plan and code for performing a task.:\n"
                    if plan:
                        if isinstance(plan, list):
                            plan_block = "\n".join(f"- {str(s)}" for s in plan)
                        else:
                            plan_block = str(plan)
                        system_prompt += f"Plan Steps:\n{plan_block}\n"
                    if code:
                        system_prompt += f"\nScript:\n```python\n{str(code)}\n```\nThis function can be called by you using `execute_ipython_code`. Do NOT redefine the function, unless it has to be modified. For modifying it, you must enter agent_builder mode first so that it is modified in the database and not just the chat locally."
        except Exception:
            # Silently ignore formatting issues
            pass

    return system_prompt, tools_context
