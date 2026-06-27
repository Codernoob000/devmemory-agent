def synthesize_post_mortem(session, log: str, context: str) -> str:
    return f"# 🚨 MOCK INCIDENT POST-MORTEM REPORT\n\n**Log:** {log}\n\n**History:** {context}"