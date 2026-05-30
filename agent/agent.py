import os
import json
from datetime import datetime, timezone
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION")

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are the AI operations manager for a World Cup 2026 venue with 90,000 fans.
Your job is to analyze incoming alerts and decide the best course of action.

You have access to these actions:
- OPEN_GATE: Open additional entry/exit gates to reduce crowd density
- PA_ANNOUNCEMENT: Send a public address announcement to redirect fans
- ALERT_SECURITY: Alert security team to a specific location
- RESTART_SERVICE: Restart a degraded infrastructure service
- ESCALATE_HUMAN: Escalate to human operator for approval

For each alert you receive, you must:
1. Assess the severity and immediate risk
2. Consider the context (match time, gate location, service type)
3. Recommend the most appropriate action
4. Explain your reasoning clearly
5. Indicate if human approval is required

Severity guidelines:
- HIGH (95%+ density or 95%+ CPU): Immediate action required, escalate to human
- MEDIUM (85-95% density or 85-95% CPU): Take automated action, notify operator
- SLOW_RESPONSE (>1500ms): Restart service automatically

Always respond in this exact JSON format:
{
    "assessment": "Brief description of the situation",
    "risk_level": "HIGH/MEDIUM/LOW",
    "recommended_action": "ACTION_NAME",
    "action_details": "Specific instructions for the action",
    "reasoning": "Why you chose this action",
    "requires_human_approval": true/false,
    "estimated_resolution_time": "X minutes"
}
"""

def analyze_alert(alert):
    """Send alert to Gemini for reasoning and action decision"""
    
    alert_message = f"""
New venue alert received:
- Type: {alert['type']}
- Severity: {alert['severity']}
- Message: {alert['message']}
- Value: {alert['value']} (threshold: {alert['threshold']})
- Location: {alert.get('gate', alert.get('service', 'Unknown'))}
- Time: {alert['timestamp']}

Current context:
- Match status: In progress (67th minute)
- Weather: 28°C, clear
- Total fans in venue: 87,432

What action should be taken?
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=alert_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=1000
        )
    )
    
    try:
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Fix common JSON issues — truncated responses
        if not response_text.endswith("}"):
            response_text = response_text + '"}'
        
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Extract what we can from the partial response
        risk = "HIGH" if "HIGH" in response.text else "MEDIUM"
        action = "ESCALATE_HUMAN"
        if "OPEN_GATE" in response.text:
            action = "OPEN_GATE"
        elif "PA_ANNOUNCEMENT" in response.text:
            action = "PA_ANNOUNCEMENT"
        elif "ALERT_SECURITY" in response.text:
            action = "ALERT_SECURITY"
        
        return {
            "assessment": response.text[:200].replace("```json", "").replace("```", "").strip(),
            "risk_level": risk,
            "recommended_action": action,
            "action_details": "Extracted from partial response",
            "reasoning": response.text[200:400].strip() if len(response.text) > 200 else "See assessment",
            "requires_human_approval": True,
            "estimated_resolution_time": "5 minutes"
        }

def process_alert(alert):
    """Process an alert through the Gemini agent"""
    print(f"\n{'='*60}")
    print(f"🤖 AGENT PROCESSING ALERT")
    print(f"{'='*60}")
    print(f"Alert: {alert['message']}")
    print(f"Severity: {alert['severity']}")
    print(f"\n⏳ Consulting Gemini...\n")
    
    decision = analyze_alert(alert)
    
    print(f"📊 AGENT ASSESSMENT: {decision.get('assessment', 'N/A')}")
    print(f"⚠️  RISK LEVEL: {decision.get('risk_level', 'N/A')}")
    print(f"🎯 RECOMMENDED ACTION: {decision.get('recommended_action', 'N/A')}")
    print(f"📋 ACTION DETAILS: {decision.get('action_details', 'N/A')}")
    print(f"🧠 REASONING: {decision.get('reasoning', 'N/A')}")
    print(f"👤 REQUIRES HUMAN APPROVAL: {decision.get('requires_human_approval', False)}")
    print(f"⏱️  ESTIMATED RESOLUTION: {decision.get('estimated_resolution_time', 'N/A')}")
    
    return decision

if __name__ == "__main__":
    # Test with a sample alert
    test_alert = {
        "type": "CROWD_SURGE",
        "severity": "HIGH",
        "gate": "Gate_7",
        "value": 97,
        "threshold": 85,
        "message": "Crowd surge at Gate_7 — 97% density",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    process_alert(test_alert)
