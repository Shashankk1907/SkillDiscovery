"""
Comprehensive API Test Script - SkillDiscovery Platform
Tests ALL endpoints across all routers
"""

import requests
import random
import json
import base64
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# ── Indian Test Data ──────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Ishaan", "Dhruv", "Kabir", "Rohan",
    "Vedant", "Pranav", "Ananya", "Priya", "Diya", "Navya", "Riya", "Meera",
    "Kavya", "Shreya", "Neha", "Divya", "Tanvi", "Sneha", "Ira", "Saanvi"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Kumar", "Singh", "Gupta", "Nair", "Iyer",
    "Joshi", "Mehta", "Kulkarni", "Agarwal", "Khanna", "Malhotra", "Chopra",
    "Bansal", "Chatterjee", "Das", "Shah", "Kapoor", "Bhatt", "Pandey"
]

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Kochi"
]

INTRO_LINES = [
    "Passionate about tech and innovation",
    "Creative problem solver and lifelong learner",
    "Enthusiastic mentor and knowledge sharer",
    "Building the future one project at a time",
    "Dedicated to continuous growth and excellence",
]

SKILLS_DATA = {
    "programming":        ["python", "javascript", "react", "node.js", "machine learning"],
    "Data":               ["data analysis", "data science", "sql", "tableau"],
    "Writing":            ["content writing", "copywriting", "technical writing"],
    "Digital marketing":  ["seo", "social media marketing", "email marketing"],
    "Design":             ["ui/ux design", "graphic design", "figma"],
}

PORTFOLIO_TYPES = ["project", "certificate", "work_sample", "other"]

PORTFOLIO_TITLES = [
    "E-commerce Platform Development",
    "Mobile App for Food Delivery",
    "ML Model for Price Prediction",
    "Corporate Website Redesign",
    "Data Analytics Dashboard",
]

REPORT_REASONS = ["spam", "harassment", "fake_profile", "inappropriate_content", "other"]


# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    HEADER = '\033[95m'
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    BOLD   = '\033[1m'
    END    = '\033[0m'


# ── Tester ────────────────────────────────────────────────────────────────────

class Tester:
    def __init__(self):
        self.users: List[Dict]           = []
        self.superuser: Dict             = {}
        self.skills: List[Dict]          = []
        self.user_skills: List[Dict]     = []
        self.portfolio_items: List[Dict] = []
        self.connections: List[Dict]     = []
        self.conversations: List[Dict]   = []
        self.sessions_list: List[Dict]   = []
        self.notifications: List[Dict]   = []
        self.pass_count = 0
        self.fail_count = 0

    # ── Logging ───────────────────────────────────────────────────────────────

    def section(self, title: str):
        print(f"\n{C.HEADER}{C.BOLD}{'─'*70}{C.END}")
        print(f"{C.HEADER}{C.BOLD}  {title}{C.END}")
        print(f"{C.HEADER}{C.BOLD}{'─'*70}{C.END}")

    def ok(self, msg: str):
        print(f"  {C.GREEN}✓{C.END} {msg}")
        self.pass_count += 1

    def fail(self, msg: str, detail: str = ""):
        print(f"  {C.RED}✗{C.END} {msg}")
        if detail:
            print(f"    {C.RED}→ {detail[:120]}{C.END}")
        self.fail_count += 1

    def info(self, msg: str):
        print(f"  {C.CYAN}ℹ{C.END} {msg}")

    def warn(self, msg: str):
        print(f"  {C.YELLOW}⚠{C.END} {msg}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def auth(self, user: Dict) -> Dict:
        return {**HEADERS, "Authorization": f"Bearer {user['token']}"}

    def superauth(self) -> Dict:
        return {**HEADERS, "Authorization": f"Bearer {self.superuser['token']}"}

    def random_user_data(self) -> Dict:
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        return {
            "email": f"{fn.lower()}.{ln.lower()}{random.randint(1, 9999)}@test.com",
            "password": "Test@1234",
            "name": f"{fn} {ln}",
            "intro_line": random.choice(INTRO_LINES),
            "location_city": random.choice(CITIES),
            "location_country": "India",
            "whatsapp_number": f"+91{random.randint(7000000000, 9999999999)}",
            "profile_photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={fn}",
        }

    def do_login(self, email: str, password: str) -> Optional[str]:
        r = requests.post(f"{BASE_URL}/auth/login",
                          data={"username": email, "password": password})
        if r.status_code == 200:
            return r.json().get("access_token")
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. AUTH
    # ═══════════════════════════════════════════════════════════════════════════

    def test_auth(self):
        self.section("AUTH  ·  /auth/register  /auth/login  /auth/refresh  /auth/logout")

        # --- Register superuser ---
        su_data = self.random_user_data()
        su_data.update({"email": "superadmin@skilldiscovery.com",
                         "name": "Super Admin", "is_superuser": True})

        r = requests.post(f"{BASE_URL}/auth/register", json=su_data, headers=HEADERS)
        self.info(f"[DEBUG] register status={r.status_code} body={r.text[:500]}")
        if r.status_code == 201:
            self.ok("POST /auth/register - superuser created")
        elif r.status_code == 400:
            self.warn("Superuser already exists - will login")
        else:
            self.fail("POST /auth/register (superuser)", r.text)

        token = self.do_login(su_data["email"], su_data["password"])
        if token:
            self.superuser = {"data": su_data, "token": token}
            self.ok("POST /auth/login → superuser token obtained")
        else:
            self.fail("POST /auth/login (superuser) — cannot continue without superuser")

        # --- Register 8 regular users ---
        for i in range(8):
            ud = self.random_user_data()
            r = requests.post(f"{BASE_URL}/auth/register", json=ud, headers=HEADERS)
            if r.status_code == 201:
                tok = self.do_login(ud["email"], ud["password"])
                if tok:
                    self.users.append({"data": ud, "response": r.json(), "token": tok})
                    self.ok(f"POST /auth/register → {ud['name']}")
            elif r.status_code == 400:
                self.warn(f"User already exists: {ud['email']}")
            else:
                self.fail(f"POST /auth/register user {i+1}", r.text)

        # --- Refresh token ---
        r = requests.post(f"{BASE_URL}/auth/login",
                          data={"username": su_data["email"], "password": su_data["password"]})
        if r.status_code == 200:
            refresh_tok = r.json().get("refresh_token")
            if refresh_tok:
                r2 = requests.post(f"{BASE_URL}/auth/refresh",
                                   json={"refresh_token": refresh_tok}, headers=HEADERS)
                if r2.status_code == 200:
                    self.ok("POST /auth/refresh → new access + refresh tokens issued")
                else:
                    self.fail("POST /auth/refresh", r2.text)
            else:
                self.warn("No refresh_token in login response — skipping refresh test")

        # --- Logout ---
        r = requests.post(f"{BASE_URL}/auth/logout")
        if r.status_code == 200:
            self.ok("POST /auth/logout → success")
        else:
            self.fail("POST /auth/logout", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. USERS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_users(self):
        self.section("USERS  ·  /users/*")

        if not self.users:
            self.fail("No users available — skipping")
            return

        u  = self.users[0]
        u2 = self.users[1]

        # GET /users/me
        r = requests.get(f"{BASE_URL}/users/me", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /users/me → {r.json()['name']}")
        else:
            self.fail("GET /users/me", r.text)

        # GET /users/me/completion
        r = requests.get(f"{BASE_URL}/users/me/completion", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /users/me/completion → {r.json()['percentage']}% complete, "
                    f"missing: {r.json()['missing']}")
        else:
            self.fail("GET /users/me/completion", r.text)

        # GET /users/me/dashboard
        r = requests.get(f"{BASE_URL}/users/me/dashboard", headers=self.auth(u))
        if r.status_code == 200:
            self.ok("GET /users/me/dashboard → stats returned")
        else:
            self.fail("GET /users/me/dashboard", r.text)

        # GET /users/me/profile-views
        r = requests.get(f"{BASE_URL}/users/me/profile-views", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /users/me/profile-views → {len(r.json())} viewers")
        else:
            self.fail("GET /users/me/profile-views", r.text)

        # GET /users/me/suggested-mentors
        r = requests.get(f"{BASE_URL}/users/me/suggested-mentors", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /users/me/suggested-mentors → {len(r.json())} suggestions")
        else:
            self.fail("GET /users/me/suggested-mentors", r.text)

        # GET /users/me/saved
        r = requests.get(f"{BASE_URL}/users/me/saved", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /users/me/saved → {len(r.json())} saved users")
        else:
            self.fail("GET /users/me/saved", r.text)

        # PUT /users/me
        updated = {**u["data"], "intro_line": "Updated intro — testing PUT /users/me"}
        r = requests.put(f"{BASE_URL}/users/me", json=updated, headers=self.auth(u))
        if r.status_code == 200:
            self.ok("PUT /users/me → profile updated")
        else:
            self.fail("PUT /users/me", r.text)

        # PUT /users/me/availability
        r = requests.put(f"{BASE_URL}/users/me/availability",
                         json={"availability": {"Monday": ["09:00-11:00"], "Saturday": ["10:00-12:00"]}},
                         headers=self.auth(u))
        if r.status_code == 200:
            self.ok("PUT /users/me/availability → saved")
        else:
            self.fail("PUT /users/me/availability", r.text)

        # GET /users/
        r = requests.get(f"{BASE_URL}/users/")
        if r.status_code == 200:
            self.ok(f"GET /users/ → {len(r.json())} users")
        else:
            self.fail("GET /users/", r.text)

        # GET /users/search?name=...
        name_q = u["data"]["name"].split()[0]
        r = requests.get(f"{BASE_URL}/users/search", params={"name": name_q})
        if r.status_code == 200:
            self.ok(f"GET /users/search?name={name_q} → {len(r.json())} results")
        else:
            self.fail("GET /users/search?name", r.text)

        # GET /users/search?city=...
        city_q = u["data"]["location_city"]
        r = requests.get(f"{BASE_URL}/users/search", params={"city": city_q})
        if r.status_code == 200:
            self.ok(f"GET /users/search?city={city_q} → {len(r.json())} results")
        else:
            self.fail("GET /users/search?city", r.text)

        # GET /users/{id}
        uid = u["response"]["id"]
        r = requests.get(f"{BASE_URL}/users/{uid}")
        if r.status_code == 200:
            self.ok(f"GET /users/{uid} → {r.json()['name']}")
        else:
            self.fail(f"GET /users/{uid}", r.text)

        # GET /users/{id}/profile  (viewed by u2 → triggers profile view log)
        r = requests.get(f"{BASE_URL}/users/{uid}/profile", headers=self.auth(u2))
        if r.status_code == 200:
            p = r.json()
            self.ok(f"GET /users/{uid}/profile → connection_status='{p['connection_status']}', "
                    f"views={p.get('stats', {}).get('views', '?')}")
        else:
            self.fail(f"GET /users/{uid}/profile", r.text)

        # POST /users/{id}/save  (toggle)
        tid = u2["response"]["id"]
        r = requests.post(f"{BASE_URL}/users/{tid}/save", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"POST /users/{tid}/save → {r.json()['message']}")
        else:
            self.fail(f"POST /users/{tid}/save", r.text)

        r = requests.post(f"{BASE_URL}/users/{tid}/save", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"POST /users/{tid}/save (toggle off) → {r.json()['message']}")
        else:
            self.fail(f"POST /users/{tid}/save (toggle)", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. SKILLS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_skills(self):
        self.section("SKILLS  ·  /skills/*")

        if not self.superuser:
            self.fail("No superuser — skipping skill creation")
            return

        # POST /skills/
        for category, names in SKILLS_DATA.items():
            for name in names:
                r = requests.post(f"{BASE_URL}/skills/",
                                  json={"name": name, "category": category,
                                        "description": f"Expert knowledge in {name}"},
                                  headers=self.superauth())
                if r.status_code == 201:
                    self.skills.append(r.json())
                    self.ok(f"POST /skills/ → '{name}' [{category}]")
                elif r.status_code == 400:
                    self.warn(f"Skill '{name}' already exists")
                else:
                    self.fail(f"POST /skills/ '{name}'", r.text)

        # GET /skills/
        r = requests.get(f"{BASE_URL}/skills/")
        if r.status_code == 200:
            all_skills = r.json()
            if not self.skills:
                self.skills = all_skills
            self.ok(f"GET /skills/ → {len(all_skills)} total skills")
        else:
            self.fail("GET /skills/", r.text)

        # GET /skills/categories
        r = requests.get(f"{BASE_URL}/skills/categories")
        if r.status_code == 200:
            self.ok(f"GET /skills/categories → {r.json()}")
        else:
            self.fail("GET /skills/categories", r.text)

        # GET /skills/suggestions?query=...
        r = requests.get(f"{BASE_URL}/skills/suggestions", params={"query": "py"})
        if r.status_code == 200:
            self.ok(f"GET /skills/suggestions?query=py → {len(r.json())} results")
        else:
            self.fail("GET /skills/suggestions", r.text)

        # GET /skills/?skill=... (filter)
        r = requests.get(f"{BASE_URL}/skills/", params={"skill": "data"})
        if r.status_code == 200:
            self.ok(f"GET /skills/?skill=data → {len(r.json())} results")
        else:
            self.fail("GET /skills/?skill=data", r.text)

        if not self.skills:
            return

        skill = self.skills[0]

        # GET /skills/{id}
        r = requests.get(f"{BASE_URL}/skills/{skill['id']}")
        if r.status_code == 200:
            self.ok(f"GET /skills/{skill['id']} → '{r.json()['name']}'")
        else:
            self.fail(f"GET /skills/{skill['id']}", r.text)

        # POST /skills/{id}/follow  (toggle follow/unfollow)
        if self.users:
            u = self.users[0]
            r = requests.post(f"{BASE_URL}/skills/{skill['id']}/follow", headers=self.auth(u))
            if r.status_code == 200:
                self.ok(f"POST /skills/{skill['id']}/follow → {r.json()['message']}")
            else:
                self.fail(f"POST /skills/{skill['id']}/follow", r.text)

            r = requests.post(f"{BASE_URL}/skills/{skill['id']}/follow", headers=self.auth(u))
            if r.status_code == 200:
                self.ok(f"POST /skills/{skill['id']}/follow (toggle) → {r.json()['message']}")
            else:
                self.fail(f"POST /skills/{skill['id']}/follow (unfollow)", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. USER SKILLS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_user_skills(self):
        self.section("USER SKILLS  ·  /user-skills/*")

        if not self.users or not self.skills:
            self.fail("Need users + skills — skipping")
            return

        # POST /user-skills/
        for u in self.users[:4]:
            uid = u["response"]["id"]
            for skill in random.sample(self.skills, min(3, len(self.skills))):
                role = random.choice(["teach", "learn"])
                r = requests.post(f"{BASE_URL}/user-skills/",
                                  json={"user_id": uid, "skill_id": skill["id"],
                                        "role": role,
                                        "proficiency_level": random.choice(
                                            ["beginner", "intermediate", "advanced"])},
                                  headers=self.auth(u))
                if r.status_code == 201:
                    self.user_skills.append(r.json())
                    self.ok(f"POST /user-skills/ → {u['data']['name']} [{role}] '{skill['name']}'")
                elif r.status_code == 400:
                    self.warn(f"Skill already added")
                else:
                    self.fail("POST /user-skills/", r.text)

        u   = self.users[0]
        uid = u["response"]["id"]

        # GET /user-skills/me
        r = requests.get(f"{BASE_URL}/user-skills/me", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /user-skills/me → {len(r.json())} skills")
        else:
            self.fail("GET /user-skills/me", r.text)

        # GET /user-skills/me?role=teach
        r = requests.get(f"{BASE_URL}/user-skills/me", params={"role": "teach"}, headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /user-skills/me?role=teach → {len(r.json())} skills")
        else:
            self.fail("GET /user-skills/me?role=teach", r.text)

        # GET /user-skills/user/{id}  (public — only teach)
        r = requests.get(f"{BASE_URL}/user-skills/user/{uid}")
        if r.status_code == 200:
            self.ok(f"GET /user-skills/user/{uid} → {len(r.json())} public (teach) skills")
        else:
            self.fail(f"GET /user-skills/user/{uid}", r.text)

        # GET /user-skills/mentors
        r = requests.get(f"{BASE_URL}/user-skills/mentors")
        if r.status_code == 200:
            self.ok(f"GET /user-skills/mentors → {len(r.json())} mentor records")
        else:
            self.fail("GET /user-skills/mentors", r.text)

        # GET /user-skills/mentors?skill_id=...
        if self.skills:
            sid = self.skills[0]["id"]
            r = requests.get(f"{BASE_URL}/user-skills/mentors", params={"skill_id": sid})
            if r.status_code == 200:
                self.ok(f"GET /user-skills/mentors?skill_id={sid} → {len(r.json())} results")
            else:
                self.fail("GET /user-skills/mentors?skill_id", r.text)

        # PUT /user-skills/{id}
        if self.user_skills:
            us    = self.user_skills[0]
            owner = self.users[0]
            r = requests.put(f"{BASE_URL}/user-skills/{us['id']}",
                             json={"user_id": owner["response"]["id"],
                                   "skill_id": us["skill_id"],
                                   "role": us["role"],
                                   "proficiency_level": "expert"},
                             headers=self.auth(owner))
            if r.status_code == 200:
                self.ok(f"PUT /user-skills/{us['id']} → proficiency → expert")
            else:
                self.fail(f"PUT /user-skills/{us['id']}", r.text)

        # DELETE /user-skills/{id}
        if len(self.user_skills) > 2:
            us    = self.user_skills[-1]
            owner = self.users[min(3, len(self.users) - 1)]
            r = requests.delete(f"{BASE_URL}/user-skills/{us['id']}", headers=self.auth(owner))
            if r.status_code == 204:
                self.ok(f"DELETE /user-skills/{us['id']} → deleted")
            else:
                self.fail(f"DELETE /user-skills/{us['id']}", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. PORTFOLIO
    # ═══════════════════════════════════════════════════════════════════════════

    def test_portfolio(self):
        self.section("PORTFOLIO  ·  /portfolio/*")

        if not self.users:
            self.fail("No users — skipping")
            return

        created = []

        # POST /portfolio/me
        for u in self.users[:3]:
            for _ in range(2):
                payload = {
                    "title":       random.choice(PORTFOLIO_TITLES),
                    "description": "Showcasing expertise through this project.",
                    "media_url":   f"https://picsum.photos/400/300?random={random.randint(1,999)}",
                    "item_type":   random.choice(PORTFOLIO_TYPES),
                }
                r = requests.post(f"{BASE_URL}/portfolio/me", json=payload, headers=self.auth(u))
                if r.status_code == 201:
                    item = r.json()
                    created.append({"item": item, "owner": u})
                    self.portfolio_items.append(item)
                    self.ok(f"POST /portfolio/me → '{item['title']}' [{item['item_type']}]")
                else:
                    self.fail("POST /portfolio/me", r.text)

        u   = self.users[0]
        uid = u["response"]["id"]

        # GET /portfolio/me
        r = requests.get(f"{BASE_URL}/portfolio/me", headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /portfolio/me → {len(r.json())} items")
        else:
            self.fail("GET /portfolio/me", r.text)

        # GET /portfolio/me?item_type=project
        r = requests.get(f"{BASE_URL}/portfolio/me", params={"item_type": "project"}, headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /portfolio/me?item_type=project → {len(r.json())} items")
        else:
            self.fail("GET /portfolio/me?item_type=project", r.text)

        # GET /portfolio/user/{id}  (public)
        r = requests.get(f"{BASE_URL}/portfolio/user/{uid}")
        if r.status_code == 200:
            self.ok(f"GET /portfolio/user/{uid} → {len(r.json())} public items")
        else:
            self.fail(f"GET /portfolio/user/{uid}", r.text)

        # PUT /portfolio/{id}
        if created:
            entry   = created[0]
            item_id = entry["item"]["id"]
            r = requests.put(f"{BASE_URL}/portfolio/{item_id}",
                             json={"title": "Updated Portfolio Title",
                                   "description": "Updated description.",
                                   "item_type": "project"},
                             headers=self.auth(entry["owner"]))
            if r.status_code == 200:
                self.ok(f"PUT /portfolio/{item_id} → title updated")
            else:
                self.fail(f"PUT /portfolio/{item_id}", r.text)

        # DELETE /portfolio/{id}
        if len(created) > 1:
            entry   = created[-1]
            item_id = entry["item"]["id"]
            r = requests.delete(f"{BASE_URL}/portfolio/{item_id}", headers=self.auth(entry["owner"]))
            if r.status_code == 204:
                self.ok(f"DELETE /portfolio/{item_id} → deleted")
            else:
                self.fail(f"DELETE /portfolio/{item_id}", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 6. CONNECTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_connections(self):
        self.section("CONNECTIONS  ·  /connections/*")

        if len(self.users) < 5:
            self.fail("Need at least 5 users — skipping")
            return

        u1, u2, u3, u4, u5 = self.users[:5]

        def send(sender, recipient) -> Optional[Dict]:
            r = requests.post(f"{BASE_URL}/connections/",
                              json={"recipient_id": recipient["response"]["id"]},
                              headers=self.auth(sender))
            if r.status_code == 201:
                self.ok(f"POST /connections/ → {sender['data']['name']} ➜ {recipient['data']['name']}")
                return r.json()
            elif r.status_code == 400:
                self.warn(f"Connection already exists: {sender['data']['name']} → {recipient['data']['name']}")
            else:
                self.fail("POST /connections/", r.text)
            return None

        conn_12 = send(u1, u2)
        conn_34 = send(u3, u4)
        conn_15 = send(u1, u5)   # will be cancelled

        # GET /connections/requests
        r = requests.get(f"{BASE_URL}/connections/requests", headers=self.auth(u2))
        if r.status_code == 200:
            self.ok(f"GET /connections/requests → {len(r.json())} pending for {u2['data']['name']}")
        else:
            self.fail("GET /connections/requests", r.text)

        # GET /connections/?type=sent
        r = requests.get(f"{BASE_URL}/connections/", params={"type": "sent"}, headers=self.auth(u1))
        if r.status_code == 200:
            self.ok(f"GET /connections/?type=sent → {len(r.json())} sent requests")
        else:
            self.fail("GET /connections/?type=sent", r.text)

        # GET /connections/?type=pending
        r = requests.get(f"{BASE_URL}/connections/", params={"type": "pending"}, headers=self.auth(u2))
        if r.status_code == 200:
            self.ok(f"GET /connections/?type=pending → {len(r.json())} pending received")
        else:
            self.fail("GET /connections/?type=pending", r.text)

        # PUT /connections/{id} — accept
        if conn_12:
            r = requests.put(f"{BASE_URL}/connections/{conn_12['id']}",
                             json={"status": "accepted"}, headers=self.auth(u2))
            if r.status_code == 200:
                self.ok(f"PUT /connections/{conn_12['id']} → accepted by {u2['data']['name']}")
                self.connections.append(r.json())
            else:
                self.fail(f"PUT /connections/{conn_12['id']} accept", r.text)

        # PUT /connections/{id} — reject
        if conn_34:
            r = requests.put(f"{BASE_URL}/connections/{conn_34['id']}",
                             json={"status": "rejected"}, headers=self.auth(u4))
            if r.status_code == 200:
                self.ok(f"PUT /connections/{conn_34['id']} → rejected by {u4['data']['name']}")
            else:
                self.fail(f"PUT /connections/{conn_34['id']} reject", r.text)

        # GET /connections/?type=accepted
        r = requests.get(f"{BASE_URL}/connections/", params={"type": "accepted"}, headers=self.auth(u1))
        if r.status_code == 200:
            self.ok(f"GET /connections/?type=accepted → {len(r.json())} accepted")
        else:
            self.fail("GET /connections/?type=accepted", r.text)

        # DELETE /connections/{id}/cancel
        if conn_15:
            r = requests.delete(f"{BASE_URL}/connections/{conn_15['id']}/cancel", headers=self.auth(u1))
            if r.status_code == 204:
                self.ok(f"DELETE /connections/{conn_15['id']}/cancel → cancelled")
            else:
                self.fail(f"DELETE /connections/{conn_15['id']}/cancel", r.text)

        # DELETE /connections/{id}  (remove accepted connection)
        if conn_12:
            r = requests.delete(f"{BASE_URL}/connections/{conn_12['id']}", headers=self.auth(u1))
            if r.status_code == 204:
                self.ok(f"DELETE /connections/{conn_12['id']} → connection removed")
            else:
                self.fail(f"DELETE /connections/{conn_12['id']}", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 7. REVIEWS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_reviews(self):
        self.section("REVIEWS  ·  /users/{id}/reviews")

        if len(self.users) < 3:
            self.fail("Need at least 3 users — skipping")
            return

        pairs = [(self.users[0], self.users[1]),
                 (self.users[1], self.users[2]),
                 (self.users[2], self.users[0])]

        for reviewer, subject in pairs:
            sid = subject["response"]["id"]
            r = requests.post(f"{BASE_URL}/users/{sid}/reviews",
                              json={"rating": random.randint(3, 5),
                                    "comment": "Excellent mentor! Very knowledgeable and patient."},
                              headers=self.auth(reviewer))
            if r.status_code == 201:
                self.ok(f"POST /users/{sid}/reviews → {reviewer['data']['name']} reviewed {subject['data']['name']}")
            elif r.status_code == 400:
                self.warn(f"Review already exists: {reviewer['data']['name']} → {subject['data']['name']}")
            else:
                self.fail(f"POST /users/{sid}/reviews", r.text)

        # GET /users/{id}/reviews
        sid = self.users[0]["response"]["id"]
        r = requests.get(f"{BASE_URL}/users/{sid}/reviews")
        if r.status_code == 200:
            self.ok(f"GET /users/{sid}/reviews → {len(r.json())} reviews")
        else:
            self.fail(f"GET /users/{sid}/reviews", r.text)

        # Self-review guard
        u = self.users[0]
        r = requests.post(f"{BASE_URL}/users/{u['response']['id']}/reviews",
                          json={"rating": 5, "comment": "I am amazing!"},
                          headers=self.auth(u))
        if r.status_code == 400:
            self.ok("POST self-review → correctly rejected (400)")
        else:
            self.fail("Self-review should return 400", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 8. SESSIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_sessions(self):
        self.section("SESSIONS  ·  /sessions/*")

        if len(self.users) < 2 or not self.skills:
            self.fail("Need users + skills — skipping")
            return

        requester = self.users[0]
        provider  = self.users[1]

        payload = {
            "provider_id": provider["response"]["id"],
            "skill_id":    self.skills[0]["id"],
            "start_time":  "2026-06-01T10:00:00",
            "end_time":    "2026-06-01T11:00:00",
        }

        # POST /sessions/
        r = requests.post(f"{BASE_URL}/sessions/", json=payload, headers=self.auth(requester))
        if r.status_code == 201:
            sess = r.json()
            self.sessions_list.append(sess)
            self.ok(f"POST /sessions/ → booked id={sess['id']}")
        elif r.status_code == 400:
            self.warn("Time slot already booked")
        else:
            self.fail("POST /sessions/", r.text)

        # POST /sessions/ duplicate → should return 400
        r = requests.post(f"{BASE_URL}/sessions/", json=payload, headers=self.auth(requester))
        if r.status_code == 400:
            self.ok("POST /sessions/ (duplicate) → correctly rejected (400)")
        elif r.status_code == 201:
            self.warn("Duplicate session allowed — overlap check may be inactive")
        else:
            self.fail("POST /sessions/ overlap check", r.text)

        # GET /sessions/
        r = requests.get(f"{BASE_URL}/sessions/", headers=self.auth(requester))
        if r.status_code == 200:
            self.ok(f"GET /sessions/ → {len(r.json())} sessions for {requester['data']['name']}")
        else:
            self.fail("GET /sessions/", r.text)

        r = requests.get(f"{BASE_URL}/sessions/", headers=self.auth(provider))
        if r.status_code == 200:
            self.ok(f"GET /sessions/ → {len(r.json())} sessions for {provider['data']['name']}")
        else:
            self.fail("GET /sessions/ (provider)", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 9. MESSAGING
    # ═══════════════════════════════════════════════════════════════════════════

    def test_messaging(self):
        self.section("MESSAGING  ·  /messaging/conversations  /messaging/messages")

        if len(self.users) < 2:
            self.fail("Need at least 2 users — skipping")
            return

        u1 = self.users[0]
        u2 = self.users[1]

        # POST /messaging/conversations
        r = requests.post(f"{BASE_URL}/messaging/conversations",
                          json={"recipient_id": u2["response"]["id"]},
                          headers=self.auth(u1))
        conv = None
        if r.status_code in (200, 201):
            conv = r.json()
            self.conversations.append(conv)
            self.ok(f"POST /messaging/conversations → conv id={conv['id']}")
        else:
            self.fail("POST /messaging/conversations", r.text)

        # GET /messaging/conversations
        r = requests.get(f"{BASE_URL}/messaging/conversations", headers=self.auth(u1))
        if r.status_code == 200:
            self.ok(f"GET /messaging/conversations → {len(r.json())} conversations")
        else:
            self.fail("GET /messaging/conversations", r.text)

        if not conv:
            self.warn("No conversation — skipping message tests")
            return

        # POST /messaging/messages  (back-and-forth)
        msgs = [
            (u1, "Hey! I saw your React profile. Would love to learn from you."),
            (u2, "Sure! I'd be happy to mentor. What's your current level?"),
            (u1, "I'm a beginner. Looking to build my first project."),
        ]
        for sender, text in msgs:
            r = requests.post(f"{BASE_URL}/messaging/messages",
                              json={"conversation_id": conv["id"], "content": text},
                              headers=self.auth(sender))
            if r.status_code == 201:
                self.ok(f"POST /messaging/messages → [{sender['data']['name']}]: '{text[:45]}...'")
            else:
                self.fail("POST /messaging/messages", r.text)

        # GET /messaging/conversations/{id}/messages
        r = requests.get(f"{BASE_URL}/messaging/conversations/{conv['id']}/messages",
                         headers=self.auth(u1))
        if r.status_code == 200:
            self.ok(f"GET /messaging/conversations/{conv['id']}/messages → {len(r.json())} messages")
        else:
            self.fail(f"GET /messaging/conversations/{conv['id']}/messages", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 10. NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_notifications(self):
        self.section("NOTIFICATIONS  ·  /notifications/*")

        if not self.users:
            self.fail("No users — skipping")
            return

        u = self.users[1]   # u2 should have connection + other notifications

        # GET /notifications/
        r = requests.get(f"{BASE_URL}/notifications/", headers=self.auth(u))
        if r.status_code == 200:
            notifs = r.json()
            self.notifications = notifs
            self.ok(f"GET /notifications/ → {len(notifs)} notifications")
        else:
            self.fail("GET /notifications/", r.text)

        # GET /notifications/?limit=5
        r = requests.get(f"{BASE_URL}/notifications/", params={"limit": 5}, headers=self.auth(u))
        if r.status_code == 200:
            self.ok(f"GET /notifications/?limit=5 → {len(r.json())} notifications")
        else:
            self.fail("GET /notifications/?limit=5", r.text)

        # PUT /notifications/{id}/read
        if self.notifications:
            nid = self.notifications[0]["id"]
            r = requests.put(f"{BASE_URL}/notifications/{nid}/read", headers=self.auth(u))
            if r.status_code == 204:
                self.ok(f"PUT /notifications/{nid}/read → marked as read")
            else:
                self.fail(f"PUT /notifications/{nid}/read", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 11. REPORTS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_reports(self):
        self.section("REPORTS  ·  /reports/users")

        if len(self.users) < 3:
            self.fail("Need at least 3 users — skipping")
            return

        reporter    = self.users[0]
        reported_id = self.users[2]["response"]["id"]

        # POST /reports/users
        r = requests.post(f"{BASE_URL}/reports/users",
                          json={"reported_id": reported_id,
                                "reason": random.choice(REPORT_REASONS),
                                "details": "User is sending spam connection requests repeatedly."},
                          headers=self.auth(reporter))
        if r.status_code == 201:
            self.ok(f"POST /reports/users → report filed against user {reported_id}")
        else:
            self.fail("POST /reports/users", r.text)

        # Self-report guard
        r = requests.post(f"{BASE_URL}/reports/users",
                          json={"reported_id": reporter["response"]["id"],
                                "reason": "spam", "details": "testing"},
                          headers=self.auth(reporter))
        if r.status_code == 400:
            self.ok("POST /reports/users self-report → correctly rejected (400)")
        else:
            self.fail("Self-report should return 400", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # 12. UPLOADS
    # ═══════════════════════════════════════════════════════════════════════════

    def test_uploads(self):
        self.section("UPLOADS  ·  /upload/")

        if not self.users:
            self.fail("No users — skipping")
            return

        u = self.users[0]
        headers = {"Authorization": f"Bearer {u['token']}"}

        # Tiny 1×1 transparent PNG
        tiny_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        r = requests.post(f"{BASE_URL}/upload/",
                          files={"file": ("test.png", tiny_png, "image/png")},
                          headers=headers)
        if r.status_code == 201:
            self.ok(f"POST /upload/ → {r.json().get('url')}")
        else:
            self.fail("POST /upload/", r.text)

    # ═══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════

    def summary(self):
        total = self.pass_count + self.fail_count
        pct   = int((self.pass_count / total) * 100) if total else 0
        bar   = ("█" * (pct // 5)).ljust(20)
        color = C.GREEN if pct >= 80 else C.YELLOW if pct >= 50 else C.RED

        print(f"\n{C.BOLD}{'═'*70}{C.END}")
        print(f"{C.BOLD}  RESULTS{C.END}")
        print(f"{'═'*70}")
        print(f"  {C.GREEN}Passed : {self.pass_count}{C.END}")
        print(f"  {C.RED}Failed : {self.fail_count}{C.END}")
        print(f"  {color}[{bar}] {pct}%  ({total} checks){C.END}")
        print(f"{'═'*70}\n")

    # ═══════════════════════════════════════════════════════════════════════════
    # RUN ALL
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self):
        print(f"\n{C.BOLD}{C.BLUE}{'═'*70}{C.END}")
        print(f"{C.BOLD}{C.BLUE}  SkillDiscovery — Full API Test Suite{C.END}")
        print(f"{C.BOLD}{C.BLUE}  {BASE_URL}{C.END}")
        print(f"{C.BOLD}{C.BLUE}{'═'*70}{C.END}")

        self.test_auth()
        self.test_users()
        self.test_skills()
        self.test_user_skills()
        self.test_portfolio()
        self.test_connections()
        self.test_reviews()
        self.test_sessions()
        self.test_messaging()
        self.test_notifications()
        self.test_reports()
        self.test_uploads()
        self.summary()


if __name__ == "__main__":
    Tester().run()