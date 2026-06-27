import logging

logger = logging.getLogger("DevMemoryIngestion")

def ingest_raw_log(raw_payload: str) -> str:
    """
    Accepts a raw, unstructured server log or CI/CD exception text payload.
    Performs basic validation, filters empty payloads, and prepares it for processing.
    """
    if not isinstance(raw_payload, str):
        logger.warning("Received log payload that is not a string. Attempting conversion.")
        try:
            raw_payload = str(raw_payload)
        except Exception as e:
            logger.error(f"Failed to convert raw payload to string: {e}")
            raise ValueError("Invalid raw log payload type: must be convertible to string.")

    cleaned_payload = raw_payload.strip()
    if not cleaned_payload:
        logger.warning("Ingested payload is empty.")
        return ""

    logger.info(f"Successfully ingested raw log payload (Length: {len(cleaned_payload)} characters).")
    return cleaned_payload
