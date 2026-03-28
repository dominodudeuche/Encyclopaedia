from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, jwt, bcrypt, os, json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)
SECRET = "NAF_ENC_SECRET_2026_RESTRICTED"
DB = "naf_encyclopedia.db"

# ── DATABASE SETUP ────────────────────────────────────────────────
def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    c = db.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        rank TEXT NOT NULL,
        role TEXT NOT NULL,
        unit TEXT,
        base TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        classification TEXT NOT NULL,
        summary TEXT,
        content TEXT NOT NULL,
        author TEXT,
        status TEXT DEFAULT 'published',
        views INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_number TEXT NOT NULL,
        user_name TEXT,
        action TEXT NOT NULL,
        detail TEXT,
        ip_address TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    # Seed users if empty
    if not c.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        users = [
            ("EAU/ADMIN/001",  "Air Cdre J. Nwachukwu", "Air Commodore",    "super_admin", "Encyclopedia Admin Unit", "HQ Abuja"),
            ("NAF/00/00/1247", "Sqn Ldr A. Okafor",      "Squadron Leader",  "officer",     "115 Air Maritime Group",  "Abuja"),
            ("NAF/01/27/4421", "Wg Cdr E. Bello",        "Wing Commander",   "officer",     "303 Flying Training School","Kaduna"),
            ("NAF/05/14/7703", "Flt Lt C. Adeyemi",      "Flight Lieutenant","officer",     "Naval Air Wing",          "Lagos"),
            ("NAF/09/03/2219", "Cpl I. Musa",            "Corporal",         "nco",         "Ground Support Squadron",  "Kano"),
            ("NAF/02/19/8841", "Fg Off T. Ibrahim",      "Flying Officer",   "officer",     "Attack Helicopter Sqn",   "Makurdi"),
            ("NAF/11/05/3310", "Sgt B. Adewale",         "Sergeant",         "nco",         "Air Defence Regiment",    "Jos"),
            ("GUEST/00/0001",  "Training Observer",      "Civilian",         "guest",       "NAF College of Aviation",  "Kaduna"),
        ]
        c.executemany("INSERT INTO users (service_number,name,rank,role,unit,base) VALUES (?,?,?,?,?,?)", users)

    # Seed articles if empty
    if not c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]:
        articles = [
            ("SEPECAT Jaguar GN-Mk1 — Tactical Strike Profile",
             "Aircraft & Equipment", "restricted",
             "The SEPECAT Jaguar GN-Mk1 served as the cornerstone of NAF offensive strike capability from 1984, bringing supersonic tactical strike and close air support to the Nigerian Air Force.",
             """## Background & Procurement

The decision to procure the SEPECAT Jaguar was taken in the early 1980s as part of a broader NAF modernisation programme. Nigeria evaluated several contemporary tactical strike platforms before selecting the Jaguar, with the GN-Mk1 variant configured specifically to Nigerian Air Force operational requirements.

The aircraft were delivered between 1984 and 1986, with initial operational capability declared at 115 Air Maritime Group, Benin Air Base. A two-seat trainer variant, the Jaguar BN, was also procured to support pilot conversion training.

## Technical Specifications

- **Manufacturer:** SEPECAT (BAC / Breguet joint venture)
- **Role:** Tactical Strike, Close Air Support, Interdiction
- **Powerplant:** 2× Rolls-Royce/Turbomeca Adour Mk 811 turbofans
- **Maximum Speed:** Mach 1.6 (1,699 km/h) at altitude
- **Combat Radius:** 852 km (lo-lo-lo profile)
- **Service Ceiling:** 14,000 m (45,930 ft)
- **Armament:** 2× 30mm DEFA 553 cannon; 4,763 kg external stores
- **NAF Quantity:** 13 GN-Mk1 + 5 BN trainer variants

## Operational Service

In NAF service, the Jaguar was primarily tasked with tactical strike and battlefield interdiction. NAF Jaguar pilots were trained at the Operational Conversion Unit at Benin Air Base, with initial assistance from RAF and Armée de l'Air instructors under bilateral defence cooperation agreements.

The aircraft maintained high operational tempo through the late 1980s and 1990s, serving as the NAF's primary offensive capability during this period.""",
             "EAU Editorial Team"),

            ("Alpha Jet A — Light Attack and Training",
             "Aircraft & Equipment", "unclassified",
             "The Alpha Jet A is the Nigerian Air Force primary advanced jet trainer and light attack platform, procured from Dassault-Breguet/Dornier and operated across multiple NAF bases.",
             """## Overview

The Alpha Jet is a Franco-German light attack and advanced jet trainer jointly developed by Dassault Aviation of France and Dornier of West Germany. The Nigerian Air Force acquired its Alpha Jets to fulfil both the advanced training and light attack roles.

## Specifications

- **Type:** Advanced Trainer / Light Attack
- **Crew:** 2 (tandem seating)
- **Powerplant:** 2× SNECMA/Turbomeca Larzac 04-C6 turbofans, 13.24 kN each
- **Maximum Speed:** 1,000 km/h (Mach 0.86) at sea level
- **Range:** 1,390 km
- **Service Ceiling:** 14,630 m
- **Armament:** 1× 27mm Mauser cannon pod; up to 2,500 kg external stores

## Role in NAF

The Alpha Jet serves the NAF in two primary roles: advanced jet pilot training at the 303 Flying Training School, Kaduna, and light attack duties with combat-ready squadrons. Its versatility makes it the most widely operated fixed-wing aircraft type in the NAF inventory.""",
             "EAU Editorial Team"),

            ("Nigerian Air Force — Founding and Early Years (1964–1970)",
             "History & Heritage", "unclassified",
             "The Nigerian Air Force was established in 1964, growing from a small transport and liaison force into a multi-role air arm within its first decade of existence.",
             """## Establishment

The Nigerian Air Force was formally established on 18 April 1964 as a component of the Nigerian Armed Forces. Its formation was driven by the need for an independent air capability following Nigeria's independence from Britain in 1960.

## Initial Fleet

The earliest NAF fleet consisted primarily of:
- **Dornier Do 27** — utility and liaison aircraft
- **Piaggio P.149** — basic trainer
- **Noratlas N.2501** — transport aircraft

Initial training was conducted with assistance from West German and British instructors, with the first generation of Nigerian pilots trained abroad before returning to form the nucleus of the new service.

## Growth Period

By the late 1960s, the NAF had expanded significantly, acquiring jet aircraft for the first time and establishing the training infrastructure that would support generations of Nigerian Air Force personnel. The service played a significant role during the Nigerian Civil War (1967–1970), gaining operational experience that shaped its doctrine for decades.""",
             "EAU Editorial Team"),

            ("NAF Headquarters — Abuja Air Base Profile",
             "Bases & Installations", "unclassified",
             "NAF Headquarters is located at Abuja, Federal Capital Territory, and serves as the administrative and operational nerve centre of the Nigerian Air Force.",
             """## Location & Status

NAF Headquarters is situated in Abuja, the Federal Capital Territory of Nigeria. The installation serves as the primary administrative centre of the entire Nigerian Air Force and houses the Office of the Chief of Air Staff.

## Key Facilities

- Office of the Chief of Air Staff (CAS)
- Directorate of Operations
- Directorate of Training
- Directorate of Logistics
- NAF Band
- NAF Museum
- Encyclopedia Admin Unit (EAU)
- Medical Centre

## Historical Notes

The NAF Headquarters was relocated to Abuja following Nigeria's capital relocation from Lagos. The move consolidated the central command function within the Federal Capital Territory, improving coordination with other armed forces commands and the Ministry of Defence.""",
             "EAU Editorial Team"),

            ("Ranks of the Nigerian Air Force — Complete Guide",
             "Ranks & Structure", "unclassified",
             "A comprehensive guide to all officer and airman ranks in the Nigerian Air Force, including insignia descriptions, equivalencies, and promotion pathways.",
             """## Officer Ranks

| Rank | Abbreviation | NATO Equivalent |
|------|-------------|-----------------|
| Air Marshal | AM | OF-8 |
| Air Vice Marshal | AVM | OF-7 |
| Air Commodore | Air Cdre | OF-6 |
| Group Captain | Gp Capt | OF-5 |
| Wing Commander | Wg Cdr | OF-4 |
| Squadron Leader | Sqn Ldr | OF-3 |
| Flight Lieutenant | Flt Lt | OF-2 |
| Flying Officer | Fg Off | OF-1 |
| Pilot Officer | Plt Off | OF-D |

## Airmen Ranks

| Rank | Abbreviation |
|------|-------------|
| Warrant Officer | WO |
| Flight Sergeant | FS |
| Sergeant | Sgt |
| Corporal | Cpl |
| Lance Corporal | LCpl |
| Aircraftman | AC |

## Promotions

Promotion in the NAF follows a combination of time-in-rank, performance evaluations, and availability of vacancies. Officers are selected for promotion by a board convened by the Chief of Air Staff.""",
             "EAU Editorial Team"),

            ("NAF Operations in the Northeast — Overview",
             "Operations & Missions", "restricted",
             "A summary of Nigerian Air Force contributions to counter-insurgency operations in the Northeast of Nigeria, covering air support, ISR, and humanitarian airlift roles.",
             """## Operational Context

The Nigerian Air Force has been a critical component of joint military operations in the Northeast of Nigeria, providing close air support, intelligence, surveillance and reconnaissance (ISR), and logistical airlift to ground forces.

## Air Assets Employed

The NAF deployed a combination of platforms including:
- **Alpha Jet A** — close air support and interdiction
- **L-39ZA Albatros** — light attack
- **AgustaWestland AW109** — attack helicopter
- **Mi-35M Hind** — attack helicopter
- **C-130 Hercules** — strategic airlift
- **Dornier 228** — maritime patrol and ISR

## Key Contributions

NAF contributions have included direct air support to ground troops, disruption of supply lines, and medical evacuation operations for wounded personnel. The air component has been instrumental in enabling ground force manoeuvre across the challenging terrain of the Lake Chad Basin.

*[Further operational details available to officers with appropriate clearance]*""",
             "EAU Editorial Team"),

            ("Air Force Medical Centre Abuja — Services Guide",
             "Medical & Welfare", "unclassified",
             "The Air Force Medical Centre at NAF HQ Abuja provides comprehensive healthcare services to serving personnel, retirees, and their dependants.",
             """## Facilities

The Air Force Medical Centre (AFMC) Abuja is the flagship medical facility of the Nigerian Air Force, offering a full range of primary, secondary, and specialist healthcare.

### Available Services
- General Medicine and Family Practice
- Surgery (General, Orthopaedic)
- Obstetrics and Gynaecology
- Paediatrics
- Dentistry
- Ophthalmology
- Radiology and Imaging
- Pharmacy
- Physiotherapy
- Mental Health and Counselling

## Eligibility

All serving NAF personnel and their immediate dependants are entitled to medical services at AFMC facilities. Retired personnel retain access subject to the terms of the NAF welfare scheme.""",
             "EAU Editorial Team"),

            ("NAF Glossary — Common Acronyms A–F",
             "Glossary & Acronyms", "unclassified",
             "A reference glossary of commonly used acronyms and abbreviations in the Nigerian Air Force, covering sections A through F.",
             """## A

- **AC** — Aircraftman
- **AFB** — Air Force Base
- **AFMC** — Air Force Medical Centre
- **AGL** — Above Ground Level
- **AM** — Air Marshal
- **AOC** — Air Officer Commanding
- **ATC** — Air Traffic Control
- **AVM** — Air Vice Marshal
- **AWACS** — Airborne Warning and Control System

## B

- **BDA** — Battle Damage Assessment
- **BN** — (Jaguar) Two-Seat Trainer Variant

## C

- **CAS** — Chief of Air Staff
- **CAS** — Close Air Support (context-dependent)
- **CAP** — Combat Air Patrol
- **COS** — Chief of Staff

## D

- **DCA** — Defensive Counter Air
- **DCAS** — Deputy Chief of Air Staff

## E

- **EAU** — Encyclopedia Admin Unit
- **EW** — Electronic Warfare

## F

- **FAC** — Forward Air Controller
- **FLIR** — Forward Looking Infrared
- **FOB** — Forward Operating Base
- **FTS** — Flying Training School""",
             "EAU Editorial Team"),

            ("303 Flying Training School — Kaduna",
             "Training & Education", "unclassified",
             "303 Flying Training School at Kaduna Air Base is the primary pilot training institution of the Nigerian Air Force, producing generations of NAF aviators.",
             """## Overview

303 Flying Training School (303 FTS) is the primary fixed-wing pilot training school of the Nigerian Air Force, located at Kaduna Air Base in Kaduna State. The school has trained the majority of NAF fixed-wing pilots since its establishment.

## Training Pipeline

The NAF pilot training pipeline at 303 FTS includes:

1. **Basic Flying Training** — Initial ab initio training on the Grob G 120TP
2. **Intermediate Flying Training** — Transition to more demanding aircraft types
3. **Advanced Flying Training** — High-performance jet training on the Alpha Jet A
4. **Operational Conversion** — Type-specific training for operational squadrons

## Notable Facts

- One of the longest-established military aviation training schools in West Africa
- Has trained pilots from several other African air forces under bilateral cooperation agreements
- The school maintains a library of training publications available through this encyclopedia""",
             "EAU Editorial Team"),

            ("NAF Rules of Engagement — General Principles",
             "Doctrine & Regulations", "confidential",
             "An overview of the general principles governing the Nigerian Air Force Rules of Engagement, applicable to all NAF operations under Nigerian and international law.",
             """## Legal Framework

The Nigerian Air Force Rules of Engagement (ROE) are derived from:
- The Constitution of the Federal Republic of Nigeria
- The Armed Forces Act (Cap A20, Laws of the Federation)
- The Geneva Conventions and Additional Protocols
- UN Security Council Resolutions applicable to Nigeria

## Core Principles

### Proportionality
Force used must be proportional to the threat posed and the military objective being pursued. Collateral damage must not be excessive relative to the military advantage anticipated.

### Distinction
NAF personnel must at all times distinguish between combatants and non-combatants. Attacks may only be directed against military objectives.

### Necessity
Force may only be used when necessary to accomplish a legitimate military objective. The minimum force necessary must be employed.

### Command Authority
All lethal force authorisation follows the established chain of command. Rules of Engagement cards are issued to all aircrew before operations.

*[Full ROE document available to authorised officers through secure channel]*""",
             "EAU Editorial Team"),
        ]
        c.executemany("""
            INSERT INTO articles (title,category,classification,summary,content,author)
            VALUES (?,?,?,?,?,?)
        """, articles)

    db.commit()
    db.close()

# ── AUTH HELPERS ──────────────────────────────────────────────────
def make_token(user):
    payload = {
        "id": user["id"],
        "service_number": user["service_number"],
        "name": user["name"],
        "rank": user["rank"],
        "role": user["role"],
        "base": user["base"],
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            request.user = payload
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            if payload.get("role") != "super_admin":
                return jsonify({"error": "Forbidden — admin only"}), 403
            request.user = payload
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

def log_action(service_number, name, action, detail="", ip=""):
    db = get_db()
    db.execute(
        "INSERT INTO audit_logs (service_number,user_name,action,detail,ip_address) VALUES (?,?,?,?,?)",
        (service_number, name, action, detail, ip)
    )
    db.commit()
    db.close()

ROLE_LEVELS = {"super_admin": 4, "officer": 3, "nco": 2, "guest": 1}
CLASSIFICATION_LEVELS = {"unclassified": 1, "restricted": 2, "confidential": 3}

def can_access(role, classification):
    role_level = ROLE_LEVELS.get(role, 0)
    cls_level = CLASSIFICATION_LEVELS.get(classification, 1)
    if role == "super_admin": return True
    if classification == "confidential" and role not in ["super_admin"]: return False
    if classification == "restricted" and role not in ["super_admin", "officer"]: return False
    return True

# ── AUTH ROUTES ───────────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    svc = (data.get("service_number") or "").strip().upper()
    if not svc:
        return jsonify({"error": "Service number required"}), 400
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE service_number=? AND active=1", (svc,)).fetchone()
    db.close()
    if not user:
        log_action(svc, "Unknown", "FAILED_LOGIN", f"Unknown service number: {svc}", request.remote_addr)
        return jsonify({"error": "Service number not recognised or account inactive"}), 401
    token = make_token(user)
    log_action(user["service_number"], user["name"], "LOGIN",
               f"Login from {request.remote_addr}", request.remote_addr)
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "service_number": user["service_number"],
            "name": user["name"],
            "rank": user["rank"],
            "role": user["role"],
            "unit": user["unit"],
            "base": user["base"]
        }
    })

@app.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    log_action(request.user["service_number"], request.user["name"], "LOGOUT", "", request.remote_addr)
    return jsonify({"message": "Logged out"})

# ── ARTICLE ROUTES ────────────────────────────────────────────────
@app.route("/api/articles", methods=["GET"])
@require_auth
def list_articles():
    role = request.user["role"]
    category = request.args.get("category", "")
    db = get_db()
    if category:
        rows = db.execute("SELECT * FROM articles WHERE status='published' AND category=? ORDER BY updated_at DESC", (category,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM articles WHERE status='published' ORDER BY updated_at DESC").fetchall()
    db.close()
    articles = []
    for r in rows:
        if can_access(role, r["classification"]):
            articles.append({
                "id": r["id"], "title": r["title"], "category": r["category"],
                "classification": r["classification"], "summary": r["summary"],
                "author": r["author"], "views": r["views"],
                "created_at": r["created_at"], "updated_at": r["updated_at"]
            })
    return jsonify(articles)

@app.route("/api/articles/<int:article_id>", methods=["GET"])
@require_auth
def get_article(article_id):
    role = request.user["role"]
    db = get_db()
    r = db.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    if not r:
        db.close()
        return jsonify({"error": "Not found"}), 404
    if not can_access(role, r["classification"]):
        db.close()
        log_action(request.user["service_number"], request.user["name"],
                   "ACCESS_DENIED", f"Attempted to access: {r['title']}", request.remote_addr)
        return jsonify({"error": "Access denied — insufficient clearance"}), 403
    db.execute("UPDATE articles SET views=views+1 WHERE id=?", (article_id,))
    db.commit()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "ARTICLE_VIEW", f"Viewed: {r['title']}", request.remote_addr)
    return jsonify({
        "id": r["id"], "title": r["title"], "category": r["category"],
        "classification": r["classification"], "summary": r["summary"],
        "content": r["content"], "author": r["author"], "views": r["views"] + 1,
        "created_at": r["created_at"], "updated_at": r["updated_at"]
    })

@app.route("/api/articles", methods=["POST"])
@require_auth
def create_article():
    if request.user["role"] not in ["super_admin", "officer"]:
        return jsonify({"error": "Forbidden"}), 403
    d = request.get_json()
    db = get_db()
    cur = db.execute("""INSERT INTO articles (title,category,classification,summary,content,author,status)
                        VALUES (?,?,?,?,?,?,?)""",
        (d["title"], d["category"], d.get("classification","unclassified"),
         d.get("summary",""), d["content"],
         request.user["name"],
         d.get("status","published")))
    db.commit()
    new_id = cur.lastrowid
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "ARTICLE_CREATE", f"Created: {d['title']}", request.remote_addr)
    return jsonify({"id": new_id, "message": "Article created"}), 201

@app.route("/api/articles/<int:article_id>", methods=["PUT"])
@require_auth
def update_article(article_id):
    if request.user["role"] not in ["super_admin", "officer"]:
        return jsonify({"error": "Forbidden"}), 403
    d = request.get_json()
    db = get_db()
    r = db.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    if not r:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute("""UPDATE articles SET title=?,category=?,classification=?,summary=?,
                  content=?,status=?,updated_at=datetime('now') WHERE id=?""",
        (d.get("title", r["title"]), d.get("category", r["category"]),
         d.get("classification", r["classification"]), d.get("summary", r["summary"]),
         d.get("content", r["content"]), d.get("status", r["status"]), article_id))
    db.commit()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "ARTICLE_UPDATE", f"Updated: {r['title']}", request.remote_addr)
    return jsonify({"message": "Updated"})

@app.route("/api/articles/<int:article_id>", methods=["DELETE"])
@require_admin
def delete_article(article_id):
    db = get_db()
    r = db.execute("SELECT title FROM articles WHERE id=?", (article_id,)).fetchone()
    if not r:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute("DELETE FROM articles WHERE id=?", (article_id,))
    db.commit()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "ARTICLE_DELETE", f"Deleted: {r['title']}", request.remote_addr)
    return jsonify({"message": "Deleted"})

# ── SEARCH ────────────────────────────────────────────────────────
@app.route("/api/search")
@require_auth
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    role = request.user["role"]
    db = get_db()
    rows = db.execute("""SELECT * FROM articles WHERE status='published'
        AND (title LIKE ? OR summary LIKE ? OR content LIKE ?)
        ORDER BY updated_at DESC LIMIT 20""",
        (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "SEARCH", f"Query: {q}", request.remote_addr)
    results = []
    for r in rows:
        if can_access(role, r["classification"]):
            results.append({
                "id": r["id"], "title": r["title"], "category": r["category"],
                "classification": r["classification"], "summary": r["summary"],
                "updated_at": r["updated_at"]
            })
    return jsonify(results)

# ── USER ROUTES (Admin) ───────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
@require_admin
def list_users():
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY role, name").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/users", methods=["POST"])
@require_admin
def create_user():
    d = request.get_json()
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE service_number=?", (d["service_number"].upper(),)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "Service number already exists"}), 409
    db.execute("INSERT INTO users (service_number,name,rank,role,unit,base) VALUES (?,?,?,?,?,?)",
        (d["service_number"].upper(), d["name"], d.get("rank",""), d.get("role","nco"),
         d.get("unit",""), d.get("base","")))
    db.commit()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "USER_CREATE", f"Created user: {d['service_number']}", request.remote_addr)
    return jsonify({"message": "User created"}), 201

@app.route("/api/users/<int:user_id>", methods=["PUT"])
@require_admin
def update_user(user_id):
    d = request.get_json()
    db = get_db()
    r = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not r:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute("UPDATE users SET name=?,rank=?,role=?,unit=?,base=?,active=? WHERE id=?",
        (d.get("name", r["name"]), d.get("rank", r["rank"]),
         d.get("role", r["role"]), d.get("unit", r["unit"]),
         d.get("base", r["base"]), d.get("active", r["active"]), user_id))
    db.commit()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "USER_UPDATE", f"Updated user: {r['service_number']}", request.remote_addr)
    return jsonify({"message": "Updated"})

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@require_admin
def delete_user(user_id):
    db = get_db()
    r = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not r:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute("UPDATE users SET active=0 WHERE id=?", (user_id,))
    db.commit()
    db.close()
    log_action(request.user["service_number"], request.user["name"],
               "USER_DEACTIVATE", f"Deactivated: {r['service_number']}", request.remote_addr)
    return jsonify({"message": "User deactivated"})

# ── AUDIT ROUTES ──────────────────────────────────────────────────
@app.route("/api/audit", methods=["GET"])
@require_admin
def audit_logs():
    limit = int(request.args.get("limit", 100))
    db = get_db()
    rows = db.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ── STATS ─────────────────────────────────────────────────────────
@app.route("/api/stats", methods=["GET"])
@require_auth
def stats():
    db = get_db()
    total_articles = db.execute("SELECT COUNT(*) FROM articles WHERE status='published'").fetchone()[0]
    total_users = db.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
    total_logs = db.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
    categories = db.execute("SELECT category, COUNT(*) as count FROM articles WHERE status='published' GROUP BY category").fetchall()
    recent = db.execute("SELECT * FROM articles WHERE status='published' ORDER BY updated_at DESC LIMIT 5").fetchall()
    db.close()
    return jsonify({
        "total_articles": total_articles,
        "total_users": total_users,
        "total_logs": total_logs,
        "categories": [dict(r) for r in categories],
        "recent_articles": [{"id":r["id"],"title":r["title"],"category":r["category"],
                              "classification":r["classification"],"updated_at":r["updated_at"]} for r in recent]
    })

# ── SERVE FRONTEND ────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"🛡️  NAF Encyclopedia System starting on port {port}")
    print(f"📡  Access at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
