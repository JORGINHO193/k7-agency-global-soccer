"""
K7 Football Agency - Capa de base de datos (SQLite puro, sin ORM/Flask).
"""
import sqlite3
import hashlib
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "k7.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    position TEXT,
    nationality TEXT,
    club TEXT,
    league TEXT,
    height TEXT,
    weight TEXT,
    foot TEXT,
    market_value TEXT,
    status TEXT DEFAULT 'Disponible',
    photo TEXT,
    bio TEXT,
    career TEXT,
    trophies TEXT,
    video_url TEXT,
    agent TEXT,
    matches INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    minutes INTEGER DEFAULT 0,
    cards INTEGER DEFAULT 0,
    instagram TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subtitle TEXT,
    author TEXT,
    date TEXT,
    category TEXT,
    summary TEXT,
    content TEXT,
    image TEXT,
    tags TEXT,
    featured INTEGER DEFAULT 0,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    whatsapp TEXT,
    country TEXT,
    subject TEXT,
    message TEXT,
    inquiry_type TEXT,
    created_at TEXT,
    read INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS scouting_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    position TEXT,
    height TEXT,
    weight TEXT,
    nationality TEXT,
    city TEXT,
    club TEXT,
    video TEXT,
    transfermarkt TEXT,
    wyscout TEXT,
    instat TEXT,
    description TEXT,
    created_at TEXT,
    reviewed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'Administrador'
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt: str = "k7-agency-salt") -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_db(seed=True):
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()

    cur = conn.execute("SELECT COUNT(*) AS c FROM admin_users")
    if cur.fetchone()["c"] == 0:
        conn.execute(
            "INSERT INTO admin_users (username, password_hash, role) VALUES (?,?,?)",
            ("admin", hash_password("K7admin2026"), "Administrador"),
        )
        conn.commit()

    if seed:
        cur = conn.execute("SELECT COUNT(*) AS c FROM players")
        if cur.fetchone()["c"] == 0:
            _seed_players(conn)
        cur = conn.execute("SELECT COUNT(*) AS c FROM news")
        if cur.fetchone()["c"] == 0:
            _seed_news(conn)

    conn.close()


def _seed_players(conn):
    now = datetime.datetime.utcnow().isoformat()
    players = [
        ("Kevin Ramírez", 22, "Delantero", "República Dominicana", "CD Águilas FC",
         "Liga Dominicana", "1.82 m", "76 kg", "Derecho", "€850,000", "Disponible",
         "https://images.unsplash.com/photo-1517927033932-b3d18e61fb3a?q=80&w=800&auto=format&fit=crop",
         "Delantero explosivo con gran definición y lectura de espacios en el área rival.",
         "CD Águilas FC (2022-Presente), Juventud Independiente (2019-2022)",
         "Campeón Liga Dominicana 2023, Bota de Oro Sub-20 2021",
         "", "Carlos Peña", 58, 34, 12, 4120, 6, "@kevin.ramirez"),
        ("Andrés Fabián", 19, "Mediocentro", "Colombia", "Deportivo Norte",
         "Categoría Primera B", "1.75 m", "68 kg", "Izquierdo", "€1,200,000", "En negociación",
         "https://images.unsplash.com/photo-1526232761682-d26e03ac148e?q=80&w=800&auto=format&fit=crop",
         "Mediocampista creativo, visión de juego y llegada al área.",
         "Deportivo Norte (2021-Presente)",
         "Mejor Jugador Sub-20 Torneo Apertura 2023",
         "", "María Torres", 41, 6, 15, 3200, 5, "@andres.fabian10"),
        ("Luis Domínguez", 25, "Defensa Central", "República Dominicana", "Real Cibao FC",
         "Liga Dominicana", "1.88 m", "84 kg", "Derecho", "€600,000", "Disponible",
         "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=800&auto=format&fit=crop",
         "Defensor central sólido en el juego aéreo y salida limpia de balón.",
         "Real Cibao FC (2020-Presente), Atlético Norte (2017-2020)",
         "Subcampeón Copa Nacional 2022",
         "", "Carlos Peña", 70, 3, 2, 5890, 9, "@luisdominguez_5"),
        ("Josué Fernández", 20, "Extremo", "Venezuela", "Deportivo Táchira",
         "Liga FUTVE", "1.73 m", "65 kg", "Zurdo", "€950,000", "Disponible",
         "https://images.unsplash.com/photo-1550881111-7cfde14b8073?q=80&w=800&auto=format&fit=crop",
         "Extremo veloz con gran capacidad de desborde y último pase.",
         "Deportivo Táchira (2022-Presente)",
         "Revelación del Torneo Clausura 2023",
         "", "María Torres", 45, 10, 14, 3450, 3, "@josuefdz"),
    ]
    conn.executemany(
        """INSERT INTO players
        (name, age, position, nationality, club, league, height, weight, foot,
         market_value, status, photo, bio, career, trophies, video_url, agent,
         matches, goals, assists, minutes, cards, instagram, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [p + (now,) for p in players],
    )
    conn.commit()


def _seed_news(conn):
    now = datetime.datetime.utcnow().isoformat()
    items = [
        ("Kevin Ramírez renueva contrato con CD Águilas FC hasta 2027",
         "El delantero extiende su vínculo tras una temporada destacada",
         "Redacción K7", "2026-06-14", "Renovaciones",
         "El atacante seguirá vistiendo la camiseta de Águilas FC por tres temporadas más.",
         "CD Águilas FC confirmó la renovación de Kevin Ramírez, uno de los delanteros más "
         "prometedores del fútbol dominicano. El nuevo contrato lo vincula al club hasta "
         "mediados de 2027, tras una campaña en la que fue determinante de cara al gol.",
         "https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=800&auto=format&fit=crop",
         "renovacion,delanteros,liga dominicana", 1),
        ("Andrés Fabián en la mira de clubes europeos",
         "Varios equipos de la Primera División de Portugal siguen de cerca al mediocampista",
         "Redacción K7", "2026-06-02", "Transferencias",
         "El talentoso volante colombiano despierta interés en el extranjero.",
         "Ojeadores europeos han estado presentes en los últimos partidos de Andrés Fabián, "
         "quien ha destacado por su capacidad de generación de juego y su madurez táctica "
         "pese a su corta edad.",
         "https://images.unsplash.com/photo-1543326727-cf6c39e8f84c?q=80&w=800&auto=format&fit=crop",
         "transferencias,scouting,europa", 1),
        ("K7 Football Agency amplía su red de scouting a Centroamérica",
         "La agencia suma nuevos ojeadores en Costa Rica, Honduras y Panamá",
         "Redacción K7", "2026-05-20", "Scouting",
         "K7 refuerza su presencia internacional con nuevo talento humano.",
         "Como parte de su plan de expansión, K7 Football Agency incorpora un equipo de "
         "ojeadores especializados en la región centroamericana, ampliando su capacidad de "
         "detección de talento joven.",
         "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?q=80&w=800&auto=format&fit=crop",
         "scouting,expansion,centroamerica", 0),
    ]
    conn.executemany(
        """INSERT INTO news (title, subtitle, author, date, category, summary, content,
        image, tags, featured, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        [n + (now,) for n in items],
    )
    conn.commit()


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada en", DB_PATH)
