# smx_task_runner.py (stub for retry demo)
from syntaxmatrix.display import show
def show_text(x): show(x)
def run_task_and_capture_code(task_text, df=None, DATA_PATH=None, **kwargs):
    ai_code = f"""from smx_task_runner import get_dataframe, run_task
df = get_dataframe(DATA_PATH={repr(DATA_PATH)})
task_text = {repr(task_text)}
run_task(task_text, df)"""
    show_text("## AI-generated code (stub)")
    show_text(f"```python\n{ai_code}\n```")
    show_text("_Stub: run_task would be executed here in the full module._")
    return ai_code
