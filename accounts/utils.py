import logging
import requests
from django.conf import settings
from community.models import TrustedContact
from local_residents.models import LocalResident as Guardian

logger = logging.getLogger(__name__)

def send_whatsapp_to_number(phone, message):
    if not (getattr(settings, 'WA_PHONE_NUMBER_ID', None) and getattr(settings, 'WA_ACCESS_TOKEN', None)):
        logger.info(f"[Simulation] WhatsApp to {phone}: {message}")
        return {"status": "simulated"}

    url = f"https://graph.facebook.com/v19.0/{settings.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return {"error": str(e)}


def send_sos_to_all_contacts(user, location):
    results = []

    # 1. Trusted Contacts
    contacts = TrustedContact.objects.filter(user=user)
    for c in contacts:
        if c.contact.phone:
            message = f"🚨 SOS ALERT 🚨\n\nVictim: {user.username}\nLocation: {location}\n\nRespond immediately!"
            results.append(send_whatsapp_to_number(c.contact.phone, message))

    # 2. Local Residents / Responders
    residents = Guardian.objects.filter(is_available=True, is_verified=True)
    for g in residents:
        if g.user.phone:
            message = f"🚨 EMERGENCY ALERT 🚨\n\nVictim: {user.username}\nLocation: {location}\n\nRespond ASAP!"
            results.append(send_whatsapp_to_number(g.user.phone, message))

    return results
