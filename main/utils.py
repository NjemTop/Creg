import json
import logging


logger = logging.getLogger('json_loader')

CONFIG_FILE = "./Main.config"

def load_json(file_path):
    logger.info(f"Opening config file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            logger.info("Opened config file successfully")
            if 'json' in globals():
                config = json.load(file)
                logger.info(f"Config loaded!")
                return config
            else:
                logger.error("JSON module is not available")
                raise ImportError("JSON module is not available")
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

def load_config():
    return load_json(CONFIG_FILE)
