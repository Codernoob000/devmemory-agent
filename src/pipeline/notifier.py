import os
import httpx

def send_slack_notification(markdown_report: str) -> bool:
    """
    Dispatches the synthesized SRE post-mortem report to an external
    Slack channel via an Incoming Webhook URL.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print("⚠️ [Notifier Warning] SLACK_WEBHOOK_URL not found in environment. Skipping transmission.")
        return False
        
    # Construct a structured payload block for Slack markdown layout formatting
    payload = {
        "text": "🚨 *New DevMemory Agent Incident Resolution Generated*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": markdown_report if markdown_report else "No report payload generated."
                }
            }
        ]
    }
    
    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        if response.status_code == 200:
            print("🚀 [Notification Successful] Report broadcasted to Slack channel.")
            return True
        else:
            print(f"❌ [Notification Failed] Slack API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ [Notification Error] Failed to connect to delivery target: {e}")
        return False