import re

def deterministic_scrub(raw_log: str) -> str:
    """
    Runs a strict, deterministic regex pass over the raw text to redact credentials,
    API keys, JWT tokens, and PII before any LLM execution occurs to guarantee enterprise safety.
    Also normalizes timestamps and paths to reduce token size.
    """
    if not raw_log:
        return ""
        
    clean_log = raw_log

    # 1. Redact JWT tokens
    jwt_pattern = r'\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
    clean_log = re.sub(jwt_pattern, '[REDACTED_JWT]', clean_log)

    # 2. Redact specific API keys / Tokens (e.g. Groq, Slack webhooks)
    groq_key_pattern = r'\bgsk_[A-Za-z0-9_]{40,}'
    clean_log = re.sub(groq_key_pattern, '[REDACTED_GROQ_API_KEY]', clean_log)
    
    slack_webhook_pattern = r'https://hooks\.slack\.com/services/[A-Za-z0-9_/]+'
    clean_log = re.sub(slack_webhook_pattern, '[REDACTED_SLACK_WEBHOOK]', clean_log)

    # 3. General credentials, passwords, tokens and secrets matching key-value formats
    # Case-insensitive matching for pattern: password=xyz, api_key="xyz", etc.
    cred_pattern = (
        r'(?i)\b(api_key|apikey|secret|password|passwd|auth_token|token|access_token|private_key|client_secret)'
        r'(?:\s*[:=]\s*|\s+is\s+)'
        r'(?:["\']?([a-zA-Z0-9_\-\.\=\+\/\@]{12,})["\']?)'
    )
    # We substitute only the secret value portion while preserving the key name
    def redact_cred(match):
        key = match.group(1)
        val = match.group(2)
        # Preserve key structure, e.g. api_key=[REDACTED_CREDENTIAL]
        return match.group(0).replace(val, '[REDACTED_CREDENTIAL]')
        
    clean_log = re.sub(cred_pattern, redact_cred, clean_log)

    # 4. Redact PII (Emails, SSNs)
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    clean_log = re.sub(email_pattern, '[REDACTED_EMAIL]', clean_log)

    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    clean_log = re.sub(ssn_pattern, '[REDACTED_SSN]', clean_log)

    # 5. Normalize timestamps down to static tokens
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
    clean_log = re.sub(timestamp_pattern, '[TIMESTAMP]', clean_log)
    
    # 6. Strip explicit system or local environment storage paths
    path_pattern = r'([A-Z]:\\[^\s]+|/[^\s]+)'
    clean_log = re.sub(path_pattern, '[PATH]', clean_log)
    
    # 7. Clean up extra structural whitespaces
    clean_log = " ".join(clean_log.split())
    
    return clean_log