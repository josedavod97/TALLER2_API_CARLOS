import requests
from django.conf import settings


class CoreAPIError(Exception):
    pass


def request_core(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if settings.CORE_API_TOKEN:
        headers["X-Admin-Token"] = settings.CORE_API_TOKEN
        headers["X-Client-Token"] = settings.CORE_API_TOKEN
    try:
        response = requests.request(
            method,
            f"{settings.FASTAPI_BASE_URL}{path}",
            headers=headers,
            timeout=8,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise CoreAPIError("No fue posible conectar con el servicio de catálogo.") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "El servicio rechazó la solicitud.")
        except ValueError:
            detail = "El servicio de catálogo devolvió una respuesta no válida."
        raise CoreAPIError(str(detail))
    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise CoreAPIError("El servicio de catálogo devolvió una respuesta no válida.") from exc


def require_core_token() -> None:
    if not settings.CORE_API_TOKEN:
        raise CoreAPIError("CORE_API_TOKEN no está configurado en Django.")
