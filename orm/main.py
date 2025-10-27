import logging

"""
Logger Config Brief

level: Sets the minimum severity to be logged. 
       Order: DEBUG < INFO < WARNING < ERROR < CRITICAL

format: A string defining the log's layout using placeholders:
    %(asctime)s: Timestamp
    %(name)s: Logger name (often the file/module name)
    %(levelname)s: Severity level (e.g., "INFO", "ERROR")
    %(message)s: The actual log message
"""

logging.basicConfig(
    level=logging.INFO,
    # filename='app.log',                         # Tell it to write to a file
    # filemode='w',                               # 'w' for overwrite, 'a' for append (default)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' # message format
) 

logger = logging.getLogger(__name__)

logger.info("Logger Configuration has Set.")