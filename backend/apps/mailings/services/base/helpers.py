def log_updates(logger, message, updates, language):
    log_message = f"{message} на {language}:\n"
    for module in updates:
        if ':' in module:
            log_message += f"  - {module.split(':')[0]}:\n"
            for update in module.split(':')[1].split('.'):
                if update.strip():
                    log_message += f"      - {update.strip()}.\n"
        else:
            log_message += f"  - {module}.\n"
    logger.info(log_message.strip())