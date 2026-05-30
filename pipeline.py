import os
import json
import time
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from google import genai
from google.genai import types
from dotenv import load_dotenv
from agent.classifier import classify_incident, get_match_context

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SUBSCRIPTION_ID = "worldcup-sensors-sub"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

THRESHOLDS = {
    "crowd_density": 85,
    "cpu_percent": 85,
    "response_time_ms": 1500
}

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

def check_alerts(data):
    alerts = []

    if data["type"] == "crowd":
        if data["density_percent"] > THRESHOLDS["crowd_density"]:
            alerts.append({
                "type": "CROWD_SURGE",
                "severity": "HIGH" if data["density_percent"] > 95 else "MEDIUM",
                "gate": data["gate"],
                "value": data["density_percent"],
                "threshold": THRESHOLDS["crowd_density"],
                "message": f"Crowd surge at {data['gate']} — {data['density_percent']}% density",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    elif data["type"] == "infrastructure":
        if data["cpu_percent"] > THRESHOLDS["cpu_percent"]:
            alerts.append({
                "type": "INFRA_SPIKE",
                "severity": "HIGH" if data["cpu_percent"] > 95 else "MEDIUM",
                "service": data["service"],
                "value": data["cpu_percent"],
                "threshold": THRESHOLDS["cpu_percent"],
                "message": f"CPU spike on {data['service']} — {data['cpu_percent']}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        if data["response_time_ms"] > THRESHOLDS["response_time_ms"]:
            alerts.append({
                "type": "SLOW_RESPONSE",
                "severity": "MEDIUM",
                "service": data["service"],
                "value": data["response_time_ms"],
                "threshold": THRESHOLDS["response_time_ms"],
                "message": f"Slow response on {data['service']} — {data['response_time_ms']}ms",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    return alerts

def analyze_alert(alert):
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
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        if not response_text.endswith("}"):
            response_text = response_text + '"}'
        return json.loads(response_text)
    except json.JSONDecodeError:
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

def execute_action(alert, decision):
    action = decision.get("recommended_action")
    requires_approval = decision.get("requires_human_approval", False)

    # Skip if no valid decision
    if not action or action == "None":
        print(f"⚠️  No valid action determined, escalating to human")
        action = "ESCALATE_HUMAN"
        requires_approval = True

    print(f"\n{'='*60}")
    print(f"🤖 AGENT DECISION")
    print(f"{'='*60}")
    print(f"📊 Assessment: {decision.get('assessment', 'N/A')}")
    print(f"⚠️  Risk Level: {decision.get('risk_level', 'N/A')}")
    print(f"🎯 Action: {action}")
    print(f"📋 Details: {decision.get('action_details', 'N/A')}")
    print(f"🧠 Reasoning: {decision.get('reasoning', 'N/A')}")
    print(f"⏱️  Resolution: {decision.get('estimated_resolution_time', 'N/A')}")

    if requires_approval and not alert.get('auto_handle', False):
        print(f"\n👤 WAITING FOR HUMAN APPROVAL...")
        print(f"   Press ENTER to approve or type 'reject' to reject: ", end="")
        user_input = input().strip().lower()
        if user_input == "reject":
            print(f"❌ Action REJECTED by operator")
            return False
        else:
            print(f"✅ Action APPROVED by operator")

    # Simulate action execution
    print(f"\n🚀 EXECUTING: {action}")
    if action == "OPEN_GATE":
        print(f"   → Gates adjacent to {alert.get('gate', 'unknown')} opened")
    elif action == "PA_ANNOUNCEMENT":
        print(f"   → PA system broadcasting fan redirection message")
    elif action == "ALERT_SECURITY":
        print(f"   → Security team alerted at {alert.get('gate', alert.get('service'))}")
    elif action == "RESTART_SERVICE":
        print(f"   → Restarting {alert.get('service', 'unknown')} service")
    elif action == "ESCALATE_HUMAN":
        print(f"   → Escalated to senior operations manager")

    print(f"   ✅ Action completed at {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")
    return True

def callback(message):
    data = json.loads(message.data)
    alerts = check_alerts(data)

    if alerts:
        context = get_match_context()
        for alert in alerts:
            # Run through classifier first
            classified = classify_incident(alert, context)
            
            print(f"\n🚨 ALERT: {classified['message']}")
            print(f"📊 Severity Score: {classified['severity_score']} → {classified['severity_class']}")
            print(f"🔍 Factors: {', '.join(classified['severity_factors'])}")
            
            if classified['auto_handle']:
                print(f"⚡ AUTO-HANDLING (no human approval needed)")
            
            decision = analyze_alert(classified)
            execute_action(classified, decision)
    else:
        if data["type"] == "crowd":
            print(f"✅ Normal: {data['gate']} density {data['density_percent']}%")
        else:
            print(f"✅ Normal: {data['service']} CPU {data['cpu_percent']}%")

    message.ack()

def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    print(f"🏟️  World Cup Ops Agent ONLINE")
    print(f"🔍 Monitoring: {subscription_path}")
    print(f"🤖 Gemini: gemini-2.5-flash")
    print(f"Press Ctrl+C to stop\n")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        print("\n🏟️  Agent offline.")

if __name__ == "__main__":
    main()
