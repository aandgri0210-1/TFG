# MotoMarket MVP

Marketplace de motos construido con Django 5, Bootstrap y SQLite por defecto.

## Funcionalidades

- Registro, login, logout y perfil de usuario
- Publicación y listado de anuncios de motos, recambios y taller por perfiles profesionales
- Filtrado por categoría y ciudad
- Solicitudes de servicio con cancelación e historial
- Valoraciones por servicio
- Integración externa de geolocalización por ciudad con Geoapify
- Base preparada para Docker, Nginx, HTTPS y MySQL

## Ejecución local

1. Crea y activa tu entorno virtual.
2. Instala dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecuta migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Crea un superusuario:

```bash
python manage.py createsuperuser
```

5. Arranca el servidor:

```bash
python manage.py runserver
```

## Variables de entorno recomendadas

```bash
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=tu_clave_secreta
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GEOAPIFY_API_KEY=tu_api_key_geoapify
```

## Docker

```bash
docker compose up --build
```

## MySQL opcional

Configura estas variables:

- `DB_ENGINE=mysql`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`

## Estructura principal

- `users`: autenticación y perfiles
- `services`: catálogo de anuncios y clima externo
- `requests_app`: solicitudes de servicio
- `reviews`: valoraciones
