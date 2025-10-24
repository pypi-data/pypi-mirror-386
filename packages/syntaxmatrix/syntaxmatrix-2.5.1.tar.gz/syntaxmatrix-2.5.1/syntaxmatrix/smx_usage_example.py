
from smx_task_runner import run_task_and_capture_code, show_text
task_text = 'Example task: regression on target Y'
ai_code = run_task_and_capture_code(task_text, DATA_PATH='/path/to/your.csv')
