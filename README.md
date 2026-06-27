# 🛡️ Women Safety Shield

**A Production-Level Intelligent Women Safety Ecosystem**

Built with Django, Django REST Framework, Django Channels (WebSockets), and Leaflet.js maps.

---

## 🚀 Features

### 1. Smart SOS Emergency System
- One-tap SOS button with GPS capture
- Voice trigger support (Web Speech API)
- Shake-to-SOS detection (DeviceMotion API)
- Instant trusted contact notification
- 3KM community guardian alert with priority sorting

### 2. Live Location Tracking
- Real-time WebSocket location streaming (Django Channels)
- Guardian and victim movement tracking on Leaflet map
- Complete location history storage

### 3. Community Guardian Network (3KM Radius)
- Verified guardian registration system
- Haversine distance calculation for nearby search
- Priority: Nearest → Higher Trust Score → Faster response
- Guardian availability toggle
- Trust score and response rate tracking

### 4. Trusted Circle System
- Add family/friends as trusted contacts
- Instant SOS alerts to all contacts
- Live location sharing during emergency

### 5. Safety Intelligence Map
- Community-reported safety zones (Green/Yellow/Red)
- Risk score calculation per area
- Anonymous incident reporting
- Interactive Leaflet.js map with clickable zones

### 6. Incident Timeline & Reports
- Full event timeline: SOS Created → Guardian Notified → Accepted → Arrived → Closed
- Auto-generated printable incident reports
- Location history attached to reports

### 7. Organization Dashboard
- Colleges, Companies, NGOs can monitor safety
- View all active emergencies
- Guardian management
- Safety analytics

### 8. Admin Control Panel
- Guardian verification workflow
- User management
- System-wide monitoring

### 9. REST API
- JWT Authentication
- Full CRUD endpoints for all modules
- WebSocket endpoints for live tracking

---

## 🗂️ Project Structure

```
women_safety_shield/
├── accounts/           # Custom user model, auth, JWT
├── emergency/          # SOS system, emergency management
├── tracking/           # Live location WebSocket
├── community/          # Trusted circle
├── guardians/          # Guardian network
├── incident/           # Timeline, reports
├── safety_map/         # Safety zones, reports
├── organization/       # Org dashboard
├── notifications/      # In-app notifications
├── admin_panel/        # Admin control
├── templates/          # HTML templates
├── static/             # CSS, JS, images
│   ├── css/main.css
│   └── js/main.js
├── manage.py
├── requirements.txt
└── women_safety_shield/
    ├── settings.py
    ├── urls.py
    ├── asgi.py         # Channels/WebSocket support
    └── wsgi.py
```

---

## ⚙️ Installation & Setup

### Step 1: Clone and Install

```bash
git clone <repo-url>
cd women_safety_shield

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2: Configure Database

For **development** (SQLite — already configured):
```python
# settings.py — default SQLite config works out of the box
```

For **production** (PostgreSQL + PostGIS):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'women_safety_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

```bash
# Install PostGIS on Ubuntu
sudo apt-get install postgresql postgresql-contrib postgis
sudo -u postgres createdb women_safety_db
sudo -u postgres psql women_safety_db -c "CREATE EXTENSION postgis;"
```

### Step 3: Configure Redis (for WebSockets in production)

```bash
sudo apt-get install redis-server
redis-server

# Update settings.py:
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    }
}
```

### Step 4: Environment Variables

Create a `.env` file:
```env
SECRET_KEY=your-very-secret-key-here
DEBUG=True
GOOGLE_MAPS_API_KEY=your-google-maps-key
FCM_SERVER_KEY=your-firebase-fcm-key
DATABASE_URL=postgresql://postgres:password@localhost/women_safety_db
REDIS_URL=redis://localhost:6379
```

### Step 5: Migrate and Run

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For **ASGI (WebSockets)**:
```bash
daphne -p 8000 women_safety_shield.asgi:application
```

---

## 🔑 Demo Credentials

| Role         | Username       | Password   |
|--------------|---------------|------------|
| Admin        | admin          | admin123   |
| User         | priya_sharma   | demo1234   |
| User 2       | sneha_patel    | demo1234   |
| Guardian     | ravi_kumar     | demo1234   |
| Guardian 2   | arjun_verma    | demo1234   |
| Organization | safecorp       | demo1234   |

---

## 🌐 URL Routes

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/accounts/register/` | User registration |
| `/accounts/login/` | Login |
| `/dashboard/` | Main dashboard |
| `/emergency/sos/` | SOS trigger page |
| `/emergency/list/` | Emergency history |
| `/emergency/<id>/track/` | Live tracking |
| `/safety-map/` | Safety map |
| `/community/trusted-contacts/` | Trusted circle |
| `/guardians/list/` | Guardian network |
| `/guardians/register/` | Become guardian |
| `/incident/list/` | Incident reports |
| `/organization/dashboard/` | Org dashboard |
| `/admin-panel/` | Admin panel |
| `/admin/` | Django admin |

---

## 🔌 REST API Endpoints

### Authentication
```
POST /api/register/           → Register new user
POST /api/login/              → Login, get JWT tokens
POST /api/token/refresh/      → Refresh JWT token
GET  /api/profile/            → Get profile
```

### Emergency
```
POST /api/emergency/create/          → Trigger SOS
GET  /api/emergency/status/          → My emergencies
POST /api/emergency/<id>/accept/     → Guardian accepts
POST /api/emergency/<id>/close/      → Close emergency
```

### Guardians
```
POST /api/guardians/register/    → Register as guardian
GET  /api/guardians/nearby/      → ?lat=&lng=&radius=3
```

### Location
```
POST /api/tracking/update/       → Update location
GET  /api/tracking/history/      → Location history
```

### Community
```
GET  /api/community/trusted-contacts/   → List contacts
POST /api/community/trusted-contact/add/ → Add contact
```

### Incident
```
GET /api/incident/report/<id>/   → Get incident report
```

### Safety Map
```
GET  /api/safety-map/       → All zones + reports
POST /api/safety-map/report/ → Submit safety report
```

---

## 🔌 WebSocket Endpoints

```
ws://host/ws/emergency/<emergency_id>/   → Emergency live updates
ws://host/ws/location/<user_id>/         → Live location tracking
```

### WebSocket Message Format
```json
{
    "type": "location",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "emergency_id": 1,
    "timestamp": "2024-01-01T10:00:00Z"
}
```

---

## 🛡️ Security

- **JWT Authentication** on all API endpoints
- **Role-based permissions**: user / guardian / organization / admin
- **CSRF protection** on all forms
- **Input validation** via DRF serializers
- **Secure file uploads** with type checking
- **Anonymous reporting** option for safety map

---

## 🗺️ Guardian Alert Logic (3KM Radius)

```python
# Haversine distance formula used for accuracy
def get_nearby_guardians(emergency_lat, emergency_lng, radius_km=3):
    all_guardians = Guardian.objects.filter(
        is_verified=True,
        is_available=True
    )
    nearby = []
    for guardian in all_guardians:
        distance = haversine(emergency_lat, emergency_lng,
                             guardian.latitude, guardian.longitude)
        if distance <= radius_km:
            guardian.distance_km = distance
            nearby.append(guardian)
    
    # Priority: nearest first, then higher trust score
    return sorted(nearby, key=lambda g: (g.distance_km, -g.trust_score))
```

**Production upgrade**: Replace with PostGIS `ST_DWithin` for database-level geo queries:
```sql
SELECT * FROM guardians_guardian 
WHERE ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
    3000  -- 3000 meters
)
AND is_verified = TRUE AND is_available = TRUE
ORDER BY ST_Distance(location, ST_MakePoint(lng, lat));
```

---

## 📱 Frontend Features

- Responsive Bootstrap 5 design
- Leaflet.js interactive maps
- Real-time WebSocket location updates
- Shake detection (DeviceMotion API)
- Voice SOS (Web Speech API)
- Pulse animation on SOS button
- Auto-dismissing notifications
- Print-ready incident reports

---

## 🏭 Production Deployment

```bash
# Gunicorn + Daphne
gunicorn women_safety_shield.wsgi:application --bind 0.0.0.0:8000 &
daphne -b 0.0.0.0 -p 8001 women_safety_shield.asgi:application &

# Nginx config
location / { proxy_pass http://127.0.0.1:8000; }
location /ws/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 📞 Emergency Helplines (India)

| Service | Number |
|---------|--------|
| Police | 100 |
| Ambulance | 108 |
| Women Helpline | 1091 |
| National Emergency | 112 |
| Childline | 1098 |

---

## 🤝 Contributing

This is a production-quality safety platform. Contributions welcome for:
- FCM push notification integration
- PostGIS production migration
- Mobile app (React Native / Flutter)
- AI-based threat detection
- Geofencing alerts

---

*Built with ❤️ for women's safety — Women Safety Shield © 2024*
