import ast
import importlib
import re
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from universal_mcp.types import ToolConfig

MAX_CHARS = 5000


def build_anthropic_cache_message(text: str, role: str = "system", ttl: str = "1h") -> list[dict[str, Any]]:
    """Build a complete Anthropic cache messages array from text.

    Returns a list with a single cache message whose content is the
    cached Anthropic content array with ephemeral cache control and TTL.
    """
    return [
        {
            "role": role,
            "content": [
                {
                    "type": "text",
                    "text": text,
                    "cache_control": {"type": "ephemeral", "ttl": ttl},
                }
            ],
        }
    ]


def add_tools(tool_config: ToolConfig, tools_to_add: ToolConfig):
    for app_id, new_tools in tools_to_add.items():
        all_tools = tool_config.get(app_id, []) + new_tools
        tool_config[app_id] = list(set(all_tools))
    return tool_config


def light_copy(data):
    """
    Deep copy a dict[str, any] or Sequence[any] with string truncation.

    Args:
        data: Either a dictionary with string keys, or a sequence of such dictionaries

    Returns:
        A deep copy where all string values are truncated to MAX_CHARS characters
    """

    def truncate_string(value):
        """Truncate string to MAX_CHARS chars, preserve other types"""
        if isinstance(value, str) and len(value) > MAX_CHARS:
            return value[:MAX_CHARS] + "..."
        return value

    def copy_dict(d):
        """Recursively copy a dictionary, truncating strings"""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = copy_dict(value)
            elif isinstance(value, Sequence) and not isinstance(value, str):
                result[key] = [
                    copy_dict(item) if isinstance(item, dict) else truncate_string(item) for item in value[:20]
                ]  # Limit to first 20 items
            else:
                result[key] = truncate_string(value)
        return result

    # Handle the two main cases
    if isinstance(data, dict):
        return copy_dict(data)
    elif isinstance(data, Sequence) and not isinstance(data, str):
        return [
            copy_dict(item) if isinstance(item, dict) else truncate_string(item) for item in data[:20]
        ]  # Limit to first 20 items
    else:
        # For completeness, handle other types
        return truncate_string(data)


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


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


def derive_context(code: str, context: dict[str, Any]) -> dict[str, Any]:
    """
    Derive context from code by extracting classes, functions, and import statements.

    Args:
        code: Python code as a string
        context: Existing context dictionary to append to

    Returns:
        Updated context dictionary with extracted entities
    """

    # Initialize context keys if they don't exist
    if "imports" not in context:
        context["imports"] = []
    if "classes" not in context:
        context["classes"] = []
    if "functions" not in context:
        context["functions"] = []

    try:
        # Parse the code into an AST
        tree = ast.parse(code)

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        import_stmt = f"import {alias.name} as {alias.asname}"
                    else:
                        import_stmt = f"import {alias.name}"
                    if import_stmt not in context["imports"]:
                        context["imports"].append(import_stmt)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                # Handle multiple imports in a single from statement
                import_names = []
                for alias in node.names:
                    if alias.asname:
                        import_names.append(f"{alias.name} as {alias.asname}")
                    else:
                        import_names.append(alias.name)

                import_stmt = f"from {module} import {', '.join(import_names)}"
                if import_stmt not in context["imports"]:
                    context["imports"].append(import_stmt)

        # Extract class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get the class definition as a string
                class_lines = code.split("\n")[node.lineno - 1 : node.end_lineno]
                class_def = "\n".join(class_lines)

                # Clean up the class definition (remove leading/trailing whitespace)
                class_def = class_def.strip()

                if class_def not in context["classes"]:
                    context["classes"].append(class_def)

        # Extract function definitions (including async)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = code.split("\n")[node.lineno - 1 : node.end_lineno]
                func_def = "\n".join(func_lines)

                # Only top-level functions (col_offset == 0)
                if node.col_offset == 0:
                    func_def = func_def.strip()
                    if func_def not in context["functions"]:
                        context["functions"].append(func_def)

    except SyntaxError:
        # If the code has syntax errors, try a simpler regex-based approach

        # Extract import statements using regex
        import_patterns = [
            r"import\s+(\w+(?:\.\w+)*)(?:\s+as\s+(\w+))?",
            r"from\s+(\w+(?:\.\w+)*)\s+import\s+(\w+(?:\s+as\s+\w+)?)",
        ]

        for pattern in import_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                if "from" in pattern:
                    module = match.group(1)
                    imports = match.group(2).split(",")
                    for import_name in imports:
                        imp = import_name.strip()
                        if " as " in imp:
                            name, alias = imp.split(" as ")
                            import_stmt = f"from {module} import {name.strip()} as {alias.strip()}"
                        else:
                            import_stmt = f"from {module} import {imp}"
                        if import_stmt not in context["imports"]:
                            context["imports"].append(import_stmt)
                else:
                    module = match.group(1)
                    alias = match.group(2)
                    if alias:
                        import_stmt = f"import {module} as {alias}"
                    else:
                        import_stmt = f"import {module}"
                    if import_stmt not in context["imports"]:
                        context["imports"].append(import_stmt)

        # Extract class definitions using regex
        class_pattern = r"class\s+(\w+).*?(?=class\s+\w+|def\s+\w+|$)"
        class_matches = re.finditer(class_pattern, code, re.DOTALL)
        for match in class_matches:
            class_def = match.group(0).strip()
            if class_def not in context["classes"]:
                context["classes"].append(class_def)

        # Extract function definitions using regex
        func_pattern = r"def\s+(\w+).*?(?=class\s+\w+|def\s+\w+|$)"
        func_matches = re.finditer(func_pattern, code, re.DOTALL)
        for match in func_matches:
            func_def = match.group(0).strip()
            if func_def not in context["functions"]:
                context["functions"].append(func_def)

    return context


def inject_context(
    context_dict: dict[str, list[str]], existing_namespace: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Inject Python entities from a dictionary into a namespace.

    This function takes a dictionary where keys represent entity types (imports, classes, functions, etc.)
    and values are lists of entity definitions. It attempts to import or create these entities and returns
    them in a namespace dictionary. Can optionally build upon an existing namespace and apply additional aliases.

    Args:
        context_dict: Dictionary with entity types as keys and lists of entity definitions as values.
                     Supported keys: 'imports', 'classes', 'functions'
                     - 'imports': List of import statements as strings (e.g., ['import pandas', 'import numpy as np'])
                     - 'classes': List of class definitions as strings
                     - 'functions': List of function definitions as strings
        existing_namespace: Optional existing namespace to build upon. If provided, new entities
                          will be added to this namespace rather than creating a new one.

    Returns:
        Dictionary containing the injected entities as key-value pairs

    Example:
        context = {
            'imports': ['import pandas as pd', 'import numpy as np'],
            'classes': ['class MyClass:\n    def __init__(self, x):\n        self.x = x'],
            'functions': ['def my_function(x):\n    return x * 2']
        }
        existing_ns = {'math': <math module>, 'data': [1, 2, 3]}
        namespace = inject_context(context, existing_ns)
        # namespace will contain: {'math': <math module>, 'data': [1, 2, 3], 'pandas': <module>, 'pd': <module>, 'numpy': <module>, 'np': <module>, 'MyClass': <class>, 'MC': <class>, 'my_function': <function>, ...}
    """

    # Start with existing namespace or create new one
    namespace: dict[str, Any] = existing_namespace.copy() if existing_namespace is not None else {}

    # Handle imports (execute import statements as strings)
    if "imports" in context_dict:
        for import_statement in context_dict["imports"]:
            try:
                # Execute the import statement in the current namespace
                exec(import_statement, namespace)
            except Exception as e:
                # If execution fails, try to extract module name and create placeholder

                # Handle different import patterns
                import_match = re.search(r"import\s+(\w+)(?:\s+as\s+(\w+))?", import_statement)
                if import_match:
                    module_name = import_match.group(1)
                    alias_name = import_match.group(2)

                    try:
                        # Try to import the module manually
                        module = importlib.import_module(module_name)
                        namespace[module_name] = module
                        if alias_name:
                            namespace[alias_name] = module
                    except ImportError:
                        # Create placeholders for missing imports
                        namespace[module_name] = f"<import '{module_name}' not available>"
                        if alias_name:
                            namespace[alias_name] = f"<import '{module_name}' as '{alias_name}' not available>"
                else:
                    # If we can't parse the import statement, create a generic placeholder
                    namespace[f"import_{len(namespace)}"] = f"<import statement failed: {str(e)}>"

    # Handle classes - execute class definitions as strings
    if "classes" in context_dict:
        for class_definition in context_dict["classes"]:
            try:
                # Execute the class definition in the current namespace
                exec(class_definition, namespace)
            except Exception:
                # If execution fails, try to extract class name and create placeholder

                class_match = re.search(r"class\s+(\w+)", class_definition)
                if class_match:
                    class_name = class_match.group(1)

                    # Create a placeholder class
                    class PlaceholderClass:
                        def __init__(self, *args, **kwargs):
                            raise NotImplementedError("Class '{class_name}' failed to load")

                    namespace[class_name] = PlaceholderClass
                else:
                    # If we can't extract class name, create a generic placeholder
                    class GenericPlaceholderClass:
                        def __init__(self, *args, **kwargs):
                            raise NotImplementedError("Class definition failed to load")

                    namespace[f"class_{len(namespace)}"] = GenericPlaceholderClass

    # Handle functions - execute function definitions as strings
    if "functions" in context_dict:
        for function_definition in context_dict["functions"]:
            try:
                # Execute the function definition in the current namespace
                exec(function_definition, namespace)
            except Exception:
                # If execution fails, try to extract function name and create placeholder
                func_match = re.search(r"(async\s+)?def\s+(\w+)", function_definition)
                if func_match:
                    func_name = func_match.group(2)
                    is_async = bool(func_match.group(1))

                    if is_async:

                        async def placeholder_func(*args, **kwargs):
                            raise NotImplementedError(f"Async function '{func_name}' failed to load")
                    else:

                        def placeholder_func(*args, **kwargs):
                            raise NotImplementedError(f"Function '{func_name}' failed to load")

                    placeholder_func.__name__ = func_name
                    namespace[func_name] = placeholder_func

    return namespace


def schema_to_signature(schema: dict, func_name: str = "my_function") -> str:
    """
    Convert a JSON schema into a Python-style function signature string.
    Handles fields with `type`, `anyOf`, defaults, and missing metadata safely.
    """
    type_map = {
        "integer": "int",
        "string": "str",
        "boolean": "bool",
        "null": "None",
        "number": "float",
        "array": "list",
        "object": "dict",
    }

    params = []
    for name, meta in schema.items():
        if not isinstance(meta, dict):
            typ = "Any"
        elif "type" in meta:
            typ = type_map.get(meta["type"], "Any")
        elif "anyOf" in meta:
            types = []
            for t in meta["anyOf"]:
                if not isinstance(t, dict):
                    continue
                t_type = t.get("type")
                types.append(type_map.get(t_type, "Any") if t_type else "Any")
            typ = " | ".join(sorted(set(types))) if types else "Any"
        else:
            typ = "Any"

        # Handle defaults gracefully
        default = meta.get("default")
        if default is None:
            params.append(f"{name}: {typ}")
        else:
            params.append(f"{name}: {typ} = {repr(default)}")

    param_str = ",\n    ".join(params)
    return f"def {func_name}(\n    {param_str},\n):"


def smart_truncate(
    output: str, max_chars_full: int = 2000, max_lines_headtail: int = 20, summary_threshold: int = 10000
) -> str:
    """
    Truncates or summarizes output intelligently to avoid filling the context too fast.

    Args:
        output (str): The string output from code execution.
        max_chars_full (int): Max characters to keep full output.
        max_lines_headtail (int): Number of lines to keep from head and tail for medium outputs.
        summary_threshold (int): If truncated output exceeds this, hard-truncate.

    Returns:
        str: Truncated or summarized output.
    """
    if len(output) <= max_chars_full:
        return output  # Small output, include fully

    lines = output.splitlines()
    if len(lines) <= 2 * max_lines_headtail:
        return output  # Medium output, include fully

    # Medium-large output: take head + tail
    head = "\n".join(lines[:max_lines_headtail])
    tail = "\n".join(lines[-max_lines_headtail:])
    truncated = f"{head}\n... [truncated {len(lines) - 2 * max_lines_headtail} lines] ...\n{tail}"

    # If still too big, cut to summary threshold
    if len(truncated) > summary_threshold:
        truncated = truncated[:summary_threshold] + "\n... [output truncated to fit context] ..."

    return truncated


async def get_connected_apps_string(registry) -> str:
    """Get a formatted string of connected applications from the registry."""
    if not registry:
        return ""

    try:
        # Get connected apps from registry
        connections = await registry.list_connected_apps()
        if not connections:
            return "No applications are currently connected."

        # Extract app names from connections
        connected_app_ids = {connection["app_id"] for connection in connections}

        # Format the apps list
        apps_list = []
        for app_id in connected_app_ids:
            apps_list.append(f"- {app_id}")

        return "\n".join(apps_list)
    except Exception:
        return "Unable to retrieve connected applications."
