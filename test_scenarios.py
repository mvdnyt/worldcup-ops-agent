import json
import time
from datetime import datetime, timezone
from agent.classifier import classify_incident, get_match_context
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import analyze_alert, execute_action

SCENARIOS = [
    {
        "name": "Scenario 1 — Critical Crowd Crush Risk",
        "description": "Gate_7 at 99% density during final minutes of match",
        "alert": {
            "type": "CROWD_SURGE",
            "severity": "HIGH",
            "gate": "Gate_7",
            "value": 99,
            "threshold": 85,
            "message": "Crowd surge at Gate_7 — 99% density",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "context_override": {"match_minute": 88}
    },
    {
        "name": "Scenario 2 — Ticketing System Failure",
        "description": "Ticketing service CPU at 96% during peak entry time",
        "alert": {
            "type": "INFRA_SPIKE",
            "severity": "HIGH",
            "service": "ticketing",
            "value": 96,
            "threshold": 85,
            "message": "CPU spike on ticketing — 96%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "context_override": {"match_minute": 0}
    },
    {
        "name": "Scenario 3 — WiFi Outage During Match",
        "description": "WiFi service degraded at 91% CPU mid-match",
        "alert": {
            "type": "INFRA_SPIKE",
            "severity": "MEDIUM",
            "service": "wifi",
            "value": 91,
            "threshold": 85,
            "message": "CPU spike on wifi — 91%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "context_override": {"match_minute": 45}
    },
    {
        "name": "Scenario 4 — Gate Jam During Half Time",
        "description": "Gate_2 at 93% density during half time crowd movement",
        "alert": {
            "type": "CROWD_SURGE",
            "severity": "MEDIUM",
            "gate": "Gate_2",
            "value": 93,
            "threshold": 85,
            "message": "Crowd surge at Gate_2 — 93% density",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "context_override": {"match_minute": 47}
    },
    {
        "name": "Scenario 5 — PA System Failure",
        "description": "PA system slow response — cannot broadcast emergency announcements",
        "alert": {
            "type": "SLOW_RESPONSE",
            "severity": "MEDIUM",
            "service": "pa_system",
            "value": 1876,
            "threshold": 1500,
            "message": "Slow response on pa_system — 1876ms",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "context_override": {"match_minute": 67}
    }
]

def run_scenario(scenario):
    print(f"\n{'#'*60}")
    print(f"# {scenario['name']}")
    print(f"# {scenario['description']}")
    print(f"{'#'*60}")

    # Get context and override match minute
    context = get_match_context()
    if scenario.get("context_override"):
        context.update(scenario["context_override"])
    
    print(f"⏱️  Match minute: {context['match_minute']}")

    # Classify
    classified = classify_incident(scenario["alert"], context)
    print(f"📊 Severity Score: {classified['severity_score']} → {classified['severity_class']}")
    print(f"🔍 Factors: {', '.join(classified['severity_factors'])}")
    print(f"⚡ Auto-handle: {classified['auto_handle']}")

    # Analyze with Gemini
    print(f"\n⏳ Consulting Gemini...")
    decision = analyze_alert(classified)

    # Execute
    execute_action(classified, decision)
    
    print(f"\n✅ Scenario complete")
    print(f"⏸️  Waiting 3 seconds before next scenario...\n")
    time.sleep(3)

def main():
    print(f"\n🏟️  WORLD CUP OPS AGENT — SCENARIO TESTING")
    print(f"{'='*60}")
    print(f"Running {len(SCENARIOS)} test scenarios\n")
    print(f"NOTE: Some scenarios require human approval.")
    print(f"Press ENTER to approve or type 'reject' to reject.\n")

    results = []
    for i, scenario in enumerate(SCENARIOS):
        print(f"\nStarting scenario {i+1} of {len(SCENARIOS)}...")
        run_scenario(scenario)
        results.append(scenario["name"])

    print(f"\n{'='*60}")
    print(f"🎯 ALL SCENARIOS COMPLETE")
    print(f"{'='*60}")
    for r in results:
        print(f"  ✅ {r}")

if __name__ == "__main__":
    main()
