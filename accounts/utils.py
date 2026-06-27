from community.models import TrustedContact
from guardians.models import Guardian

import requests
from django.conf import settings

def send_whatsapp_to_number(phone, message):
    url = f"https://graph.facebook.com/v19.0/{settings.WA_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()



def send_sos_to_all_contacts(user, location):

    results = []

    # 1. Trusted Contacts
    contacts = TrustedContact.objects.filter(user=user)

    for c in contacts:
        message = f"""
🚨 SOS ALERT 🚨

Victim: {user.username}
Location: {location}

Respond immediately!
"""
        results.append(
    send_whatsapp_to_number(
        c.contact.phone,
        message
    )
)

    # 2. Guardians (NEW ADDITION)
    guardians = Guardian.objects.filter(user=user, is_available=True)

    for g in guardians:
        message = f"""
🚨 GUARDIAN ALERT 🚨

Victim: {user.username}
Location: {location}

You are assigned as Guardian. Respond ASAP!
"""
        results.append(
    send_whatsapp_to_number(
        g.contact.phone,
        message
    )
)

    return results