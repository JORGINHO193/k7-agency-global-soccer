# K7 Football Agency — Sitio Web Premium (Python puro, sin Flask)

Sitio web completo para una agencia de representación y scouting de futbolistas,
construido con **Python puro**: sin Flask, sin Django. El servidor usa `wsgiref`
(incluido en la librería estándar de Python) y `sqlite3` como base de datos.
Jinja2 se usa únicamente como motor de plantillas HTML (no es un framework web).

## Tecnologías

- **Backend:** Python 3 + `wsgiref` (servidor WSGI stdlib) + `sqlite3`
- **Plantillas:** Jinja2 (solo renderizado, sin routing ni lógica de framework)
- **Frontend:** HTML5, CSS3 (glassmorphism, animaciones, scroll reveal), JavaScript vanilla
- **Iconos:** Font Awesome (CDN)
- **Sesiones:** cookies HttpOnly + almacenamiento en memoria
- **Seguridad:** protección CSRF en todos los formularios, contraseñas con hash SHA-256

## Instalación

```bash
pip install jinja2
```

## Ejecutar

```bash
python3 app.py
```

Abre tu navegador en: **http://localhost:8000**

## Panel Administrativo

URL: **http://localhost:8000/admin/login**

- Usuario: `admin`
- Contraseña: `K7admin2026`

⚠️ Cambia estas credenciales antes de usar en producción (ver `database.py`,
función `_seed_players`/`init_db`, o crea un usuario nuevo con `hash_password()`).

## Estructura del proyecto

```
k7_agency/
├── app.py              # Servidor WSGI, rutas, sesiones, CSRF
├── database.py          # Esquema SQLite + datos de ejemplo
├── k7.db                 # Base de datos (se genera al primer arranque)
├── templates/            # Plantillas Jinja2 (sitio público + admin)
└── static/
    ├── css/style.css     # Tema premium negro/gris/verde
    └── js/main.js        # Animaciones, contadores, carrusel, modales
```

## Funcionalidades incluidas

**Sitio público**
- Home con hero a pantalla completa, partículas animadas, contadores estadísticos
- Catálogo de jugadores con filtros (nombre, posición) y perfil individual detallado
- Sistema de noticias con carrusel de destacadas, categorías y artículo individual
- Formulario de Scouting (envío de perfiles para evaluación)
- Formulario de Contacto con tipos de consulta
- Páginas de Servicios y Nosotros

**Panel administrativo**
- Login seguro con sesión y CSRF
- Dashboard con estadísticas generales
- CRUD completo de Jugadores (crear, editar, eliminar) vía modales
- CRUD completo de Noticias (crear, editar, eliminar, marcar como destacada)
- Bandeja de mensajes de contacto y postulaciones de scouting

## Extensiones sugeridas (no incluidas en esta versión)

- Subida de archivos/imágenes (actualmente las fotos se referencian por URL)
- Roles múltiples (Editor, Scout, Agente) con permisos diferenciados
- Selector de idioma ES/EN funcional (actualmente es visual)
- Mapa de calor de jugador y estadísticas avanzadas
- Sistema de comentarios en noticias
- Backups automáticos desde el panel

Estas piezas se pueden agregar sobre la misma base sin cambiar la arquitectura.
