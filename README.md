# UNDERGRAWN | JOSE_DM — tienda de ropa

Tienda minimalista de ropa construida como aplicación híbrida: FastAPI administra prendas, inventario por talla/color y pedidos en MongoDB; Django proporciona la interfaz MVT y la autenticación de clientes y administradores. El código está separado entre `techgear_api/` (FastAPI) y `techgear_web/` (Django).

## Roles

- **Cliente:** se registra en Django, consulta el catálogo, realiza pedidos y consulta su historial.
- **Administrador:** cuenta Django con `is_staff=True`. Puede crear, editar y desactivar prendas desde la interfaz web, especificando stock para cada combinación de talla y color.
- Las rutas de escritura de FastAPI requieren el secreto compartido; Django conserva ese valor en el servidor y nunca lo expone en el navegador. Las cuentas se almacenan en la base SQL de Django; productos y pedidos, en MongoDB.

## Desarrollo local

Requiere Python 3.11 o posterior y MongoDB local o una URI de MongoDB Atlas.

1. Crea y activa un entorno virtual, luego instala las dependencias:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r techgear_api\requirements.txt
   pip install -r techgear_web\requirements.txt
   ```

2. Configura `techgear_api/.env` desde `techgear_api/.env.example`, indicando `MONGODB_URL`, `MONGODB_DATABASE` y `ADMIN_API_TOKEN`.
3. Configura `techgear_web/.env` desde `techgear_web/.env.example`. `CORE_API_TOKEN` debe ser el mismo valor que `ADMIN_API_TOKEN`.
4. Inicia la API en una terminal:

   ```powershell
   cd techgear_api
   uvicorn app.main:app --reload
   ```

   Swagger UI estará en `http://127.0.0.1:8000/docs`.

5. En otra terminal, aplica migraciones y crea un usuario administrador:

   ```powershell
   cd techgear_web
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

   La tienda estará en `http://127.0.0.1:8001` (la API usa el puerto 8000).

## API principal

| Método | Ruta | Uso | Acceso |
|---|---|---|---|
| `GET` | `/products` | Listar productos activos; filtro opcional `category` | Público |
| `GET` | `/products/{product_id}` | Consultar producto | Público |
| `POST` | `/products` | Crear producto | Token de administrador |
| `PATCH` | `/products/{product_id}` | Editar producto | Token de administrador |
| `DELETE` | `/products/{product_id}` | Desactivar producto | Token de administrador |
| `POST` | `/orders?customer={username}` | Registrar pedido de una talla y color disponibles | Token de servicio |
| `GET` | `/orders?customer={username}` | Consultar pedidos de un cliente | Token de servicio |
| `GET` | `/health` | Comprobar conexión con MongoDB | Público |

Para operaciones protegidas se envía `X-Admin-Token` o `X-Client-Token`, según la ruta. Al crear prendas, cada variante se registra con talla, color y stock propio. Al comprar, la API reserva las unidades de esa variante de forma atómica; no se confía en precios enviados por el cliente. Los pedidos guardan una copia del precio, nombre, talla y color elegidos al momento de la compra.

## Pruebas y controles

Desde la raíz del proyecto:

```powershell
python -m pip install -r techgear_api\requirements.txt
python -m pip install -r techgear_web\requirements.txt
python -m pytest techgear_api\tests
python techgear_web\manage.py check
```

## Render

`render.yaml` describe dos servicios web y la base PostgreSQL para las cuentas Django. Al crear el Blueprint, completa `MONGODB_URL` (URI de Atlas), `ADMIN_API_TOKEN` y `CORE_API_TOKEN` con el mismo secreto. Asegúrate de permitir en Atlas las conexiones de red del servicio desplegado y de restringir el usuario de base de datos a los permisos mínimos necesarios. Swagger se publica en `/docs` en el servicio de la API.

## Secuencia de commits

La implementación se organiza linealmente en `main`, sin ramas de trabajo:

1. `feat: estructura, conexión MongoDB Atlas y modelos Pydantic` — 23/10/2026
2. `feat: API REST, esquemas de usuario, portal Django y Render` — 26/10/2026

Los commits reflejan las fechas de entrega indicadas en el plan de desarrollo.
