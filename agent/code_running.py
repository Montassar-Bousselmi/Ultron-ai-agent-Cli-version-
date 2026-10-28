import io
import traceback
from contextlib import redirect_stdout

def execute_python_code(code: str) -> str:
    """
    runs python code and returns the output or error message.
    """
    output_buffer = io.StringIO()
    
    try:
        with redirect_stdout(output_buffer):
            exec(code, {})
        
        result = output_buffer.getvalue()
        
        if not result.strip():
            return "Code executed successfully, but nothing was printed. Did you forget to use print()?"
            
        return result
        
    except Exception as e:
        error_msg = traceback.format_exc()
        return f"Execution failed with the following error:\n{error_msg}"