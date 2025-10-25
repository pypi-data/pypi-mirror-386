# logging.py
import logging
from datetime import datetime

# Set up logging configuration
def setup_logging(log_file: str = 'pipeline.log'):
    """
    Set up logging configuration to log the activities of the pipeline.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Optional: print log to console
        ]
    )

def log_pipeline_step(step_name: str, data: str, result: str, benchmark: float = None):
    """
    Log each step of the pipeline transformation.
    Args:
        step_name (str): Name of the pipeline step
        data (str): Input data before transformation
        result (str): Output data after transformation
        benchmark (float, optional): Time taken for the step if benchmark=True
    """
    if benchmark:
        logging.info(f"{step_name}: Took {benchmark:.4f}s | Input: {data} | Output: {result}")
    else:
        logging.info(f"{step_name}: Input: {data} | Output: {result}")