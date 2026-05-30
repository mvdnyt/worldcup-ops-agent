from datetime import datetime, timezone

def classify_incident(alert, context=None):
    """
    Multi-factor severity classifier.
    Considers alert value, type, time of match, and combinations.
    Returns enriched alert with severity score and recommended handling.
    """
    
    score = 0
    factors = []
    
    # Base score from value
    value = alert["value"]
    threshold = alert["threshold"]
    excess_percent = ((value - threshold) / threshold) * 100
    
    if excess_percent > 15:
        score += 40
        factors.append(f"Value {excess_percent:.0f}% above threshold")
    elif excess_percent > 5:
        score += 20
        factors.append(f"Value {excess_percent:.0f}% above threshold")
    else:
        score += 10
        factors.append(f"Value just above threshold")

    # Alert type scoring
    if alert["type"] == "CROWD_SURGE":
        score += 30
        factors.append("Crowd surge — direct safety risk")
        
        # Gate position matters
        gate = alert.get("gate", "")
        if gate in ["Gate_1", "Gate_2", "Gate_7", "Gate_8"]:
            score += 10
            factors.append(f"{gate} is a high-traffic exit gate")
            
    elif alert["type"] == "INFRA_SPIKE":
        score += 20
        factors.append("Infrastructure spike — service risk")
        
        # Critical services score higher
        service = alert.get("service", "")
        if service in ["ticketing", "pa_system"]:
            score += 15
            factors.append(f"{service} is a critical service")
        elif service in ["security_cam"]:
            score += 10
            factors.append(f"{service} affects safety monitoring")
            
    elif alert["type"] == "SLOW_RESPONSE":
        score += 10
        factors.append("Slow response — performance degradation")

    # Time context scoring
    if context:
        match_minute = context.get("match_minute", 0)
        
        # Critical match moments
        if match_minute >= 85:
            score += 20
            factors.append("Final minutes — fans preparing to leave")
        elif match_minute >= 45 and match_minute <= 50:
            score += 15
            factors.append("Half time — high crowd movement")
        elif match_minute == 0:
            score += 15
            factors.append("Match starting — peak entry time")

    # Determine final severity and handling
    if score >= 70:
        severity_class = "CRITICAL"
        auto_handle = False
        priority = 1
    elif score >= 45:
        severity_class = "HIGH"
        auto_handle = False
        priority = 2
    elif score >= 25:
        severity_class = "MEDIUM"
        auto_handle = True
        priority = 3
    else:
        severity_class = "LOW"
        auto_handle = True
        priority = 4

    return {
        **alert,
        "severity_class": severity_class,
        "severity_score": score,
        "severity_factors": factors,
        "auto_handle": auto_handle,
        "priority": priority
    }


def get_match_context():
    """Simulates match context — in production this would come from a live API"""
    now = datetime.now(timezone.utc)
    hour = now.hour
    
    # Simulate match in progress
    if 14 <= hour < 16:
        minute = (now.minute + now.second // 30) % 90
        return {
            "match_minute": minute,
            "match_status": "In Progress",
            "venue_capacity": 90000,
            "fans_present": 87432,
            "weather": "28°C, Clear",
            "next_match": "Morocco vs Portugal"
        }
    else:
        return {
            "match_minute": 67,
            "match_status": "In Progress",
            "venue_capacity": 90000,
            "fans_present": 87432,
            "weather": "28°C, Clear",
            "next_match": "Morocco vs Portugal"
        }


if __name__ == "__main__":
    # Test the classifier with different scenarios
    test_alerts = [
        {
            "type": "CROWD_SURGE",
            "severity": "HIGH",
            "gate": "Gate_7",
            "value": 97,
            "threshold": 85,
            "message": "Crowd surge at Gate_7 — 97% density",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "type": "CROWD_SURGE",
            "severity": "MEDIUM",
            "gate": "Gate_3",
            "value": 88,
            "threshold": 85,
            "message": "Crowd surge at Gate_3 — 88% density",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "type": "INFRA_SPIKE",
            "severity": "MEDIUM",
            "service": "ticketing",
            "value": 91,
            "threshold": 85,
            "message": "CPU spike on ticketing — 91%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "type": "SLOW_RESPONSE",
            "severity": "MEDIUM",
            "service": "security_cam",
            "value": 1600,
            "threshold": 1500,
            "message": "Slow response on security_cam — 1600ms",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    context = get_match_context()
    print(f"Match context: Minute {context['match_minute']}, {context['match_status']}\n")
    
    for alert in test_alerts:
        result = classify_incident(alert, context)
        print(f"Alert: {alert['message']}")
        print(f"Score: {result['severity_score']} → {result['severity_class']}")
        print(f"Auto-handle: {result['auto_handle']}")
        print(f"Factors: {', '.join(result['severity_factors'])}")
        print()
