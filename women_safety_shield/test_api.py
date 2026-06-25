#!/usr/bin/env python3
"""
Women Safety Shield - API Test Script
Run: python test_api.py
Make sure the server is running on port 8000
"""
import json
import urllib.request
import urllib.error

BASE = 'http://localhost:8000'

def post(url, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + url, json.dumps(data).encode(), headers)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def get(url, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + url, headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def test(name, ok, code):
    status = '✅' if ok else '❌'
    print(f'  {status} {name} [{code}]')

print('\n🛡️  Women Safety Shield - API Tests\n')

# 1. Register
print('1. Authentication')
data, code = post('/api/register/', {
    'username': 'testuser99', 'email': 'test99@wss.com',
    'first_name': 'Test', 'last_name': 'User',
    'phone': '9999999999', 'role': 'user',
    'password': 'TestPass@123', 'password2': 'TestPass@123'
})
test('Register new user', code == 201, code)
token = data.get('tokens', {}).get('access')

# 2. Login
data2, code2 = post('/api/login/', {'username': 'priya_sharma', 'password': 'demo1234'})
test('Login existing user', code2 == 200, code2)
user_token = data2.get('tokens', {}).get('access', token)

# 3. Profile
print('\n2. Profile')
data, code = get('/api/profile/', user_token)
test('Get profile', code == 200, code)
if code == 200:
    print(f'     → User: {data.get("first_name")} {data.get("last_name")} ({data.get("role")})')

# 4. Emergency
print('\n3. Emergency System')
data, code = post('/api/emergency/create/', {
    'latitude': 19.076, 'longitude': 72.877,
    'trigger_type': 'button', 'description': 'API test emergency'
}, user_token)
test('Create SOS emergency', code == 201, code)
emergency_id = None
if code == 201:
    emergency_id = data.get('emergency', {}).get('id')
    print(f'     → Emergency #{emergency_id} created')

data, code = get('/api/emergency/status/', user_token)
test('Get emergency status', code == 200, code)

# 5. Close emergency
if emergency_id:
    data, code = post(f'/api/emergency/{emergency_id}/close/', {}, user_token)
    test('Close emergency', code == 200, code)

# 6. Guardians
print('\n4. Guardians')
data, code = get('/api/guardians/nearby/?lat=19.076&lng=72.877&radius=3', user_token)
test('Get nearby guardians (3km)', code == 200, code)
if code == 200:
    count = data.get('count', 0)
    print(f'     → {count} guardian(s) found within 3KM')

# 7. Trusted contacts
print('\n5. Community')
data, code = get('/api/community/trusted-contacts/', user_token)
test('Get trusted contacts', code == 200, code)

data, code = post('/api/community/trusted-contact/add/', {'contact_id': 3, 'relation': 'friend'}, user_token)
test('Add trusted contact', code in [200, 201, 400], code)

# 8. Location update
print('\n6. Location Tracking')
data, code = post('/api/tracking/update/', {
    'latitude': 19.076, 'longitude': 72.877, 'accuracy': 10.0
}, user_token)
test('Update location', code == 200, code)

data, code = get('/api/tracking/history/', user_token)
test('Get location history', code == 200, code)

# 9. Safety Map
print('\n7. Safety Map')
data, code = get('/api/safety-map/', user_token)
test('Get safety map data', code == 200, code)
if code == 200:
    zones = len(data.get('zones', []))
    reports = len(data.get('reports', []))
    print(f'     → {zones} zone(s), {reports} report(s)')

data, code = post('/api/safety-map/report/', {
    'latitude': 19.076, 'longitude': 72.877,
    'category': 'safe', 'location_name': 'Test Park',
    'description': 'API test report'
}, user_token)
test('Submit safety report', code == 201, code)

# 10. Incident
print('\n8. Incident Reports')
data, code = get('/api/incident/report/1/', user_token)
test('Get incident report', code in [200, 404], code)

print('\n' + '='*40)
print('✅ API tests complete!')
print('='*40 + '\n')
