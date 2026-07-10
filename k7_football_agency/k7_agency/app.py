"""
K7 Football Agency - Servidor web en Python puro (SIN Flask).
Motor: wsgiref (stdlib) + sqlite3 + Jinja2 (solo para plantillas).

Ejecutar:
    python3 app.py
Luego abrir:
    http://localhost:8000
Admin:
    http://localhost:8000/admin/login   (usuario: admin / clave: K7admin2026)
"""
import os
import re
import json
import secrets
import datetime
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from jinja2 import Environment, FileSystemLoader, select_autoescape

import database as db

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)

# ---------------------------------------------------------------------------
# Sesiones en memoria (token de cookie -> datos de sesión). Suficiente para
# una demo / single-process app. Para producción real usar un store externo.
# ---------------------------------------------------------------------------
SESSIONS = {}
SESSION_COOKIE = "k7_session"


def new_session():
    token = secrets.token_hex(24)
    SESSIONS[token] = {"csrf": secrets.token_hex(16)}
    return token


def get_session(environ):
    cookie = SimpleCookie(environ.get("HTTP_COOKIE", ""))
    if SESSION_COOKIE in cookie:
        token = cookie[SESSION_COOKIE].value
        if token in SESSIONS:
            return token, SESSIONS[token]
    token = new_session()
    return token, SESSIONS[token]


def render(template_name, **context):
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def redirect(location, session_token=None):
    headers = [("Location", location)]
    if session_token:
        headers.append(("Set-Cookie", f"{SESSION_COOKIE}={session_token}; Path=/; HttpOnly"))
    return "302 Found", headers, b""


def html_response(body, session_token=None, status="200 OK"):
    headers = [("Content-Type", "text/html; charset=utf-8")]
    if session_token:
        headers.append(("Set-Cookie", f"{SESSION_COOKIE}={session_token}; Path=/; HttpOnly"))
    return status, headers, body.encode("utf-8")


def json_response(data, status="200 OK"):
    headers = [("Content-Type", "application/json; charset=utf-8")]
    return status, headers, json.dumps(data).encode("utf-8")


def parse_post(environ):
    try:
        size = int(environ.get("CONTENT_LENGTH", 0) or 0)
    except ValueError:
        size = 0
    raw = environ["wsgi.input"].read(size) if size else b""
    fields = parse_qs(raw.decode("utf-8"))
    return {k: v[0] for k, v in fields.items()}


def require_admin(session):
    return session.get("admin_id") is not None


# ---------------------------------------------------------------------------
# Handlers - Sitio público
# ---------------------------------------------------------------------------
def h_home(environ, session, token, params):
    conn = db.get_conn()
    players = conn.execute(
        "SELECT * FROM players ORDER BY created_at DESC LIMIT 4"
    ).fetchall()
    news = conn.execute(
        "SELECT * FROM news ORDER BY featured DESC, date DESC LIMIT 3"
    ).fetchall()
    conn.close()
    body = render("index.html", players=players, news=news, active="home")
    return html_response(body, token)


def h_players(environ, session, token, params):
    q = params.get("q", [""])[0]
    position = params.get("position", [""])[0]
    conn = db.get_conn()
    sql = "SELECT * FROM players WHERE 1=1"
    args = []
    if q:
        sql += " AND name LIKE ?"
        args.append(f"%{q}%")
    if position:
        sql += " AND position = ?"
        args.append(position)
    sql += " ORDER BY created_at DESC"
    players = conn.execute(sql, args).fetchall()
    positions = [r["position"] for r in conn.execute(
        "SELECT DISTINCT position FROM players"
    ).fetchall()]
    conn.close()
    body = render("players.html", players=players, positions=positions,
                   q=q, position=position, active="players")
    return html_response(body, token)


def h_player_detail(environ, session, token, params, player_id):
    conn = db.get_conn()
    player = conn.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
    conn.close()
    if not player:
        return html_response(render("404.html", active=""), token, status="404 Not Found")
    body = render("player_detail.html", player=player, active="players")
    return html_response(body, token)


def h_news(environ, session, token, params):
    category = params.get("category", [""])[0]
    conn = db.get_conn()
    if category:
        news = conn.execute(
            "SELECT * FROM news WHERE category=? ORDER BY date DESC", (category,)
        ).fetchall()
    else:
        news = conn.execute("SELECT * FROM news ORDER BY date DESC").fetchall()
    categories = [r["category"] for r in conn.execute(
        "SELECT DISTINCT category FROM news"
    ).fetchall()]
    featured = conn.execute(
        "SELECT * FROM news WHERE featured=1 ORDER BY date DESC"
    ).fetchall()
    conn.close()
    body = render("news.html", news=news, categories=categories, featured=featured,
                   category=category, active="news")
    return html_response(body, token)


def h_news_detail(environ, session, token, params, news_id):
    conn = db.get_conn()
    article = conn.execute("SELECT * FROM news WHERE id=?", (news_id,)).fetchone()
    related = []
    if article:
        related = conn.execute(
            "SELECT * FROM news WHERE category=? AND id!=? ORDER BY date DESC LIMIT 3",
            (article["category"], news_id),
        ).fetchall()
    conn.close()
    if not article:
        return html_response(render("404.html", active=""), token, status="404 Not Found")
    body = render("news_detail.html", article=article, related=related, active="news")
    return html_response(body, token)


def h_scouting_get(environ, session, token, params):
    body = render("scouting.html", active="scouting", csrf=session["csrf"], sent=False)
    return html_response(body, token)


def h_scouting_post(environ, session, token, params):
    form = parse_post(environ)
    if form.get("csrf") != session.get("csrf"):
        return html_response("Token CSRF inválido.", token, status="400 Bad Request")
    conn = db.get_conn()
    conn.execute(
        """INSERT INTO scouting_submissions
        (name, age, position, height, weight, nationality, city, club, video,
         transfermarkt, wyscout, instat, description, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (form.get("name", ""), form.get("age") or 0, form.get("position", ""),
         form.get("height", ""), form.get("weight", ""), form.get("nationality", ""),
         form.get("city", ""), form.get("club", ""), form.get("video", ""),
         form.get("transfermarkt", ""), form.get("wyscout", ""), form.get("instat", ""),
         form.get("description", ""), datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    body = render("scouting.html", active="scouting", csrf=session["csrf"], sent=True)
    return html_response(body, token)


def h_contact_get(environ, session, token, params):
    body = render("contact.html", active="contact", csrf=session["csrf"], sent=False)
    return html_response(body, token)


def h_contact_post(environ, session, token, params):
    form = parse_post(environ)
    if form.get("csrf") != session.get("csrf"):
        return html_response("Token CSRF inválido.", token, status="400 Bad Request")
    conn = db.get_conn()
    conn.execute(
        """INSERT INTO messages
        (first_name, last_name, email, whatsapp, country, subject, message,
         inquiry_type, created_at) VALUES (?,?,?,?,?,?,?,?,?)""",
        (form.get("first_name", ""), form.get("last_name", ""), form.get("email", ""),
         form.get("whatsapp", ""), form.get("country", ""), form.get("subject", ""),
         form.get("message", ""), form.get("inquiry_type", "General"),
         datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    body = render("contact.html", active="contact", csrf=session["csrf"], sent=True)
    return html_response(body, token)


def h_about(environ, session, token, params):
    body = render("about.html", active="about")
    return html_response(body, token)


def h_services(environ, session, token, params):
    body = render("services.html", active="services")
    return html_response(body, token)


# ---------------------------------------------------------------------------
# Handlers - Panel administrativo
# ---------------------------------------------------------------------------
def h_admin_login_get(environ, session, token, params):
    body = render("admin_login.html", csrf=session["csrf"], error=None)
    return html_response(body, token)


def h_admin_login_post(environ, session, token, params):
    form = parse_post(environ)
    if form.get("csrf") != session.get("csrf"):
        body = render("admin_login.html", csrf=session["csrf"], error="Token inválido.")
        return html_response(body, token)
    conn = db.get_conn()
    user = conn.execute(
        "SELECT * FROM admin_users WHERE username=?", (form.get("username", ""),)
    ).fetchone()
    conn.close()
    if user and user["password_hash"] == db.hash_password(form.get("password", "")):
        session["admin_id"] = user["id"]
        session["admin_user"] = user["username"]
        session["admin_role"] = user["role"]
        return redirect("/admin", token)
    body = render("admin_login.html", csrf=session["csrf"],
                   error="Usuario o contraseña incorrectos.")
    return html_response(body, token)


def h_admin_logout(environ, session, token, params):
    session.pop("admin_id", None)
    session.pop("admin_user", None)
    session.pop("admin_role", None)
    return redirect("/admin/login", token)


def _admin_guard(session, token):
    if not require_admin(session):
        return redirect("/admin/login", token)
    return None


def h_admin_dashboard(environ, session, token, params):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    conn = db.get_conn()
    stats = {
        "players": conn.execute("SELECT COUNT(*) c FROM players").fetchone()["c"],
        "news": conn.execute("SELECT COUNT(*) c FROM news").fetchone()["c"],
        "messages": conn.execute("SELECT COUNT(*) c FROM messages").fetchone()["c"],
        "unread": conn.execute("SELECT COUNT(*) c FROM messages WHERE read=0").fetchone()["c"],
        "scouting": conn.execute("SELECT COUNT(*) c FROM scouting_submissions").fetchone()["c"],
    }
    conn.close()
    body = render("admin_dashboard.html", stats=stats, session=session, active="dashboard")
    return html_response(body, token)


def h_admin_players(environ, session, token, params):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    conn = db.get_conn()
    players = conn.execute("SELECT * FROM players ORDER BY created_at DESC").fetchall()
    conn.close()
    body = render("admin_players.html", players=players, session=session,
                   active="players", csrf=session["csrf"])
    return html_response(body, token)


def h_admin_player_save(environ, session, token, params):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    form = parse_post(environ)
    if form.get("csrf") != session.get("csrf"):
        return redirect("/admin/players", token)
    conn = db.get_conn()
    pid = form.get("id")
    fields = ("name", "age", "position", "nationality", "club", "league", "height",
              "weight", "foot", "market_value", "status", "photo", "bio", "career",
              "trophies", "video_url", "agent", "matches", "goals", "assists",
              "minutes", "cards", "instagram")
    values = [form.get(f, "") for f in fields]
    if pid:
        conn.execute(
            f"UPDATE players SET {', '.join(f + '=?' for f in fields)} WHERE id=?",
            values + [pid],
        )
    else:
        conn.execute(
            f"""INSERT INTO players ({', '.join(fields)}, created_at)
            VALUES ({', '.join('?' for _ in fields)}, ?)""",
            values + [datetime.datetime.now().isoformat()],
        )
    conn.commit()
    conn.close()
    return redirect("/admin/players", token)


def h_admin_player_delete(environ, session, token, params, player_id):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    conn = db.get_conn()
    conn.execute("DELETE FROM players WHERE id=?", (player_id,))
    conn.commit()
    conn.close()
    return redirect("/admin/players", token)


def h_admin_news(environ, session, token, params):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    conn = db.get_conn()
    news = conn.execute("SELECT * FROM news ORDER BY date DESC").fetchall()
    conn.close()
    body = render("admin_news.html", news=news, session=session,
                   active="news", csrf=session["csrf"])
    return html_response(body, token)


def h_admin_news_save(environ, session, token, params):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    form = parse_post(environ)
    if form.get("csrf") != session.get("csrf"):
        return redirect("/admin/news", token)
    conn = db.get_conn()
    nid = form.get("id")
    fields = ("title", "subtitle", "author", "date", "category", "summary",
              "content", "image", "tags")
    values = [form.get(f, "") for f in fields]
    featured = 1 if form.get("featured") == "on" else 0
    if nid:
        conn.execute(
            f"UPDATE news SET {', '.join(f + '=?' for f in fields)}, featured=? WHERE id=?",
            values + [featured, nid],
        )
    else:
        conn.execute(
            f"""INSERT INTO news ({', '.join(fields)}, featured, created_at)
            VALUES ({', '.join('?' for _ in fields)}, ?, ?)""",
            values + [featured, datetime.datetime.now().isoformat()],
        )
    conn.commit()
    conn.close()
    return redirect("/admin/news", token)


def h_admin_news_delete(environ, session, token, params, news_id):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    conn = db.get_conn()
    conn.execute("DELETE FROM news WHERE id=?", (news_id,))
    conn.commit()
    conn.close()
    return redirect("/admin/news", token)


def h_admin_messages(environ, session, token, params):
    guard = _admin_guard(session, token)
    if guard:
        return guard
    conn = db.get_conn()
    messages = conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    scouting = conn.execute(
        "SELECT * FROM scouting_submissions ORDER BY created_at DESC"
    ).fetchall()
    conn.execute("UPDATE messages SET read=1")
    conn.commit()
    conn.close()
    body = render("admin_messages.html", messages=messages, scouting=scouting,
                   session=session, active="messages")
    return html_response(body, token)


# ---------------------------------------------------------------------------
# Enrutador
# ---------------------------------------------------------------------------
ROUTES = [
    ("GET", r"^/$", h_home),
    ("GET", r"^/jugadores/?$", h_players),
    ("GET", r"^/jugadores/(\d+)/?$", h_player_detail),
    ("GET", r"^/noticias/?$", h_news),
    ("GET", r"^/noticias/(\d+)/?$", h_news_detail),
    ("GET", r"^/scouting/?$", h_scouting_get),
    ("POST", r"^/scouting/?$", h_scouting_post),
    ("GET", r"^/contacto/?$", h_contact_get),
    ("POST", r"^/contacto/?$", h_contact_post),
    ("GET", r"^/nosotros/?$", h_about),
    ("GET", r"^/servicios/?$", h_services),
    ("GET", r"^/admin/login/?$", h_admin_login_get),
    ("POST", r"^/admin/login/?$", h_admin_login_post),
    ("GET", r"^/admin/logout/?$", h_admin_logout),
    ("GET", r"^/admin/?$", h_admin_dashboard),
    ("GET", r"^/admin/players/?$", h_admin_players),
    ("POST", r"^/admin/players/save/?$", h_admin_player_save),
    ("POST", r"^/admin/players/(\d+)/delete/?$", h_admin_player_delete),
    ("GET", r"^/admin/news/?$", h_admin_news),
    ("POST", r"^/admin/news/save/?$", h_admin_news_save),
    ("POST", r"^/admin/news/(\d+)/delete/?$", h_admin_news_delete),
    ("GET", r"^/admin/messages/?$", h_admin_messages),
]
COMPILED_ROUTES = [(m, re.compile(p), h) for m, p, h in ROUTES]


def serve_static(path):
    file_path = os.path.normpath(os.path.join(STATIC_DIR, path[len("/static/"):]))
    if not file_path.startswith(STATIC_DIR) or not os.path.isfile(file_path):
        return "404 Not Found", [("Content-Type", "text/plain")], b"Not found"
    ext = os.path.splitext(file_path)[1]
    ctype = {
        ".css": "text/css", ".js": "application/javascript",
        ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
    }.get(ext, "application/octet-stream")
    with open(file_path, "rb") as f:
        data = f.read()
    return "200 OK", [("Content-Type", ctype)], data


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    if path.startswith("/static/"):
        status, headers, body = serve_static(path)
        start_response(status, headers)
        return [body]

    token, session = get_session(environ)
    params = parse_qs(environ.get("QUERY_STRING", ""))

    for m, pattern, handler in COMPILED_ROUTES:
        if m != method:
            continue
        match = pattern.match(path)
        if match:
            try:
                status, headers, body = handler(environ, session, token, params, *match.groups())
            except TypeError:
                status, headers, body = handler(environ, session, token, params)
            start_response(status, headers)
            return [body]

    body = render("404.html", active="")
    status, headers, body_bytes = html_response(body, token, status="404 Not Found")
    start_response(status, headers)
    return [body_bytes]


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 8000))
    with make_server("0.0.0.0", port, application) as httpd:
        print(f"K7 Football Agency corriendo en http://localhost:{port}")
        print("Panel admin: /admin/login  (usuario: admin / clave: K7admin2026)")
        httpd.serve_forever()
