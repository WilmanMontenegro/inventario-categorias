# Inventario categorías

Demo Django: mercancía en un container, catálogo para empresas y compra en web.

Stack: Python + Django 5.2 + templates + HTMX.

## Arranque (desde cero)

Python 3.11+ (o 3.12). En la carpeta del repo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver
```

Abrí http://127.0.0.1:8000/entrar/

| Rol | Usuario | Clave |
| --- | --- | --- |
| Admin | `admin` | `demo1234` |
| Comprador (empresa) | `unilago` | `demo1234` |

No hace falta `.env` para la demo local.

## Recorrido demo

1. `seed_demo` carga container `CONT-DEMO-001` + 10 productos DEMO.
2. Entrar como empresa → catálogo.
3. Al carrito → confirmar compra → factura.
4. El inventario del container baja al confirmar.

## Qué hay

- App `inventario`: categoría, producto, container, inventario, empresa, entrega, carrito, factura.
- Login: `/entrar/`. Admin Django: `/admin/` (como `admin`).
