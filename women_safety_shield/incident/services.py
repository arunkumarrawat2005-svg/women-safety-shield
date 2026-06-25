from .models import IncidentEvent, IncidentReport
import uuid


def generate_incident_report(emergency):
    events = IncidentEvent.objects.filter(emergency=emergency).order_by('timestamp')
    
    summary_lines = [f"Emergency #{emergency.id} by {emergency.victim.full_name}"]
    summary_lines.append(f"Location: ({emergency.latitude}, {emergency.longitude})")
    summary_lines.append(f"Trigger: {emergency.trigger_type}")
    summary_lines.append(f"Status: {emergency.status}")
    
    if emergency.assigned_guardian:
        summary_lines.append(f"Guardian: {emergency.assigned_guardian.full_name}")
    
    summary_lines.append(f"\nTimeline ({events.count()} events):")
    for event in events:
        summary_lines.append(f"  [{event.timestamp.strftime('%H:%M:%S')}] {event.get_event_name_display()}")

    report_number = f"WSS-{emergency.id}-{uuid.uuid4().hex[:6].upper()}"
    
    report, _ = IncidentReport.objects.get_or_create(
        emergency=emergency,
        defaults={
            'report_number': report_number,
            'summary': '\n'.join(summary_lines),
            'response_time_minutes': emergency.duration_minutes(),
        }
    )
    return report
