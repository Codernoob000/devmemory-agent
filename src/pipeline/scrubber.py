import re

def deterministic_scrub(raw_log: str) -> str:
    """
    Sanitizes raw system application logs by normalizing dates, 
    stripping system paths, and reducing token footprint.
    """
    if not raw_log:
        return ""
        
    # 1. Normalize timestamps down to static tokens
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
    clean_log = re.sub(timestamp_pattern, '[TIMESTAMP]', raw_log)
    
    # 2. Strip explicit system or local environment storage paths
    path_pattern = r'([A-Z]:\\[^\s]+|/[^\s]+)'
    clean_log = re.sub(path_pattern, '[PATH]', clean_log)
    
    # 3. Clean up extra structural whitespaces
    clean_log = " ".join(clean_log.split())
    
    return clean_log