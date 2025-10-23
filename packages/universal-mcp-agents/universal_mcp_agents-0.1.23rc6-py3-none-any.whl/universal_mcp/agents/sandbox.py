import ast
import base64
import contextlib
import io
import traceback

import cloudpickle as pickle


class Sandbox:
    """
    A simulated environment for executing Python code cells with context
    maintained across multiple runs.
    """

    def __init__(self):
        # Dictionary to store variables (context) across runs
        self.context = {}

    def add_context(self, context: dict[str, any]):
        """
        Adds a dictionary of context to the sandbox.
        """
        self.context.update(context)

    def save_context(self) -> str:
        """
        Saves the context to a base64 string.
        """
        pickled_data = pickle.dumps(self.context)
        base64_encoded = base64.b64encode(pickled_data).decode("utf-8")
        return base64_encoded

    def load_context(self, context: str):
        """
        Loads the context from a base64 string.
        """
        pickled_data = base64.b64decode(context)
        self.context = pickle.loads(pickled_data)

    def run(self, code: str) -> dict[str, any]:
        """
        Executes the provided Python code string in the maintained context.

        Args:
            code (str): The Python code to execute.

        Returns:
            dict: A dictionary containing the execution results.
        """
        # Prepare the execution environment:
        # Use a copy of the context for execution locals/globals
        exec_scope = self.context.copy()

        stdout_capture = io.StringIO()
        stderr_output = ""

        # Use a true context manager for robust stdout capture
        try:
            with contextlib.redirect_stdout(stdout_capture):
                # Execute the code. Using the same dictionary for globals and locals
                # allows newly created variables to be visible immediately.
                exec(code, exec_scope, exec_scope)

            # Update the context with any new/modified variables
            # Filter out dunder methods/system keys that might be introduced by exec
            new_context = {k: v for k, v in exec_scope.items() if not k.startswith("__")}
            self.context.update(new_context)

        except Exception:
            # Capture the traceback for better error reporting (simulated stderr)
            stderr_output = traceback.format_exc()

            # The execution scope might contain partially defined variables,
            # but we continue to maintain the *previous* valid context.
            # We don't update self.context on failure to avoid polluting it.

        return {"stdout": stdout_capture.getvalue(), "stderr": stderr_output, "success": stderr_output == ""}

    def get_context(self) -> dict[str, any]:
        """
        Returns a copy of the current execution context.

        Returns:
            dict: A copy of the context dictionary.
        """
        return self.context.copy()

    def reset(self):
        """
        Resets the sandbox's context, clearing all defined variables.
        """
        self.context = {}

    async def arun(self, code: str) -> dict[str, any]:
        """
        Asynchronously executes Python code, supporting top-level await.
        """
        # Use a copy of the context for execution
        exec_scope = self.context.copy()
        stdout_capture = io.StringIO()
        stderr_output = ""

        try:
            # Compile the code with the special flag to allow top-level await
            compiled_code = compile(code, "<string>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

            with contextlib.redirect_stdout(stdout_capture):
                # Eval the compiled code to get a coroutine
                coroutine = eval(compiled_code, exec_scope, exec_scope)

                # Await the coroutine to run the code if it's async
                if coroutine:
                    await coroutine

            # Update the context with any new/modified variables
            new_context = {k: v for k, v in exec_scope.items() if not k.startswith("__")}
            self.context.update(new_context)

        except Exception:
            stderr_output = traceback.format_exc()

        return {"stdout": stdout_capture.getvalue(), "stderr": stderr_output, "success": stderr_output == ""}
