import logging, os, sys, pathlib

LOG_DIR = pathlib.Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str):
    """Sets up a custom, reusable logging system"""
    logger = logging.getLogger(name)     #Returns an existing logger with given name (if one was already created), or creates a new logger if it doesn’t exist yet
    if logger.handlers:     #handler decides where your log messages go. If they are already present, just return as it is, don't add new ones
        return logger
    logger.setLevel(logging.INFO if os.getenv("APP_ENV")=="prod" else logging.DEBUG)    #decides how much detail we need in logs
    
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")     #Defines the log message format
    fh = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")     #Creates a file handler
    fh.setFormatter(fmt); fh.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)      #Creates a stream handler that prints logs directly to the terminal (stdout)
    sh.setFormatter(fmt); sh.setLevel(logging.DEBUG)
    logger.addHandler(fh); logger.addHandler(sh)
    
    return logger
