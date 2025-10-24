import requests
from urllib.parse import urljoin
from typing import Iterator, Any, Dict, List, Optional


class APIError(Exception):
    """Custom exception for API errors."""
    pass


class PyJMQKrill:
    def __init__(self, host: str, username: str, password: str) -> None:
        if not host or not isinstance(host, str):
            raise ValueError("El parámetro 'host' debe ser una URL no vacía de tipo str.")
        if not username or not isinstance(username, str):
            raise ValueError("El parámetro 'username' debe ser un str no vacío.")
        if not password or not isinstance(password, str):
            raise ValueError("El parámetro 'password' debe ser un str no vacío.")

        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.session = requests.Session()
        # Configuración por defecto para todas las peticiones
        self.session.headers.update({
            "Accept": "application/json"
        })

    def login(self) -> str:
        """
        Authenticate with the API and store the access token.
        :return: Access token string.
        :raises APIError: If authentication fails.
        """
        payload = {"username": self.username, "password": self.password}
        data = self._request("POST", "/api/v2/auth/login", data=payload, auth=True)
        token = data.get("access")
        if not token:
            raise APIError("Token de acceso no encontrado en la respuesta.")
        self.token = token
        # Reutilizar sesión con encabezado de autorización
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return token

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        auth: bool = False
    ) -> Any:
        """
        Internal helper to perform HTTP requests.
        :param method: HTTP method ("GET", "POST", etc.).
        :param path: API endpoint path or full URL.
        :param params: Query parameters.
        :param data: Form data or JSON payload.
        :param auth: Whether this request is for authentication (ignores Authorization header).
        :return: Parsed JSON response.
        :raises APIError: On network errors, non-2xx responses, or invalid JSON.
        """
        # Construir URL completo o usar path absoluto
        if path.lower().startswith('http'):
            url = path
        else:
            url = urljoin(self.host + '/', path.lstrip('/'))
        headers = {}
        # Para login, no usar Authorization
        if auth:
            pass  # solo Accept ya está en session.headers
        else:
            if not self.token:
                raise APIError("No se encontró un token. Realiza login primero.")
            # Authorization ya configurado en session.headers

        try:
            response = self.session.request(method, url, params=params, data=data)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Error de conexión: {e}")

        if not 200 <= response.status_code < 300:
            msg = f"HTTP {response.status_code}: {response.text}"
            raise APIError(msg)

        try:
            return response.json()
        except ValueError:
            raise APIError("Respuesta no es un JSON válido.")

    def get_cpes_by_gen_equipos(self, uuid_gen_equipo: str) -> Any:
        """
        Obtener CPEs de una topología específica.
        :param uuid_gen_equipo: Identificador de la topología.
        :raises ValueError: Si el parámetro no es válido.
        """
        if not uuid_gen_equipo or not isinstance(uuid_gen_equipo, str):
            raise ValueError("El parámetro 'uuid_gen_equipo' debe ser un str no vacío.")
        return self._request("GET", "/api/v2/isp/cpes/", params={"topology": uuid_gen_equipo})

    def get_cpe_info(self, cpe: int) -> Any:
        """
        Obtener información en tiempo real de un CPE.
        :param cpe: Nombre o ID del CPE.
        :raises ValueError: Si el parámetro no es válido.
        """
        if not cpe or not isinstance(cpe, int):
            raise ValueError("El parámetro 'cpe' debe ser un int no vacío.")
        return self._request("GET", f"/api/v2/monitoring/cpes/{cpe}/info")

    def get_cpes_by_olt(self, nombre_olt: str, frame: str, slot: str, port: str) -> Any:
        """
        Obtener estado de ONUs para una OLT, frame, slot y puerto específicos.
        :raises ValueError: Si algún parámetro no es válido.
        """
        if not nombre_olt or not isinstance(nombre_olt, str):
            raise ValueError("El parámetro 'nombre_olt' debe ser un str no vacío.")
        for name, val in [('frame', frame), ('slot', slot), ('port', port)]:
            if not isinstance(val, str):
                raise ValueError(f"El parámetro '{name}' debe ser un string formato XX.")

        path = f"/api/v2/gpon/olts/{nombre_olt}/frames/{frame}/slots/{slot}/ports/{port}/onus/status/"
        return self._request("GET", path)

    def get_cpes_monitoring(self, topology: Optional[str] = None, limit: int = 100, hostgroup: str = "cpegpon") -> List[Any]:
        """
        Obtener todos los CPEs de monitoring, con opción de filtrar por topología.
        Optimiza la paginación usando 'next' directamente.
        :param topology: Nombre de la topología para filtrar (opcional).
        :raises ValueError: Si el parámetro 'topology' no es un str.
        """
        if topology is not None and not isinstance(topology, str):
            raise ValueError("El parámetro 'topology' debe ser un str si se proporciona.")

        # URL inicial de búsqueda
        url = urljoin(self.host + '/', '/api/v2/monitoring/search/')
        params: Dict[str, Any] = {
            "joins": "services",
            "type": "Host",
            "limit": int(limit),
            "offset": 1,
            "hostgroups": hostgroup
        }
        if topology:
            params["topology"] = topology
            params["vars.administrative_info__topology"] = topology

        all_results: List[Any] = []
        # Paginación: usar 'next' completo
        while url:
            data = self._request("GET", url, params=params)
            all_results.extend(data.get("results", []))
            # Preparar siguiente página
            url = data.get("next")
            params = None  # next_url ya incluye parámetros

        return all_results

    def iter_cpes_monitoring_pages(
            self,
            topology: Optional[str] = None,
            limit: int = 100,
            include_services: bool = True,
            hostgroup: str = "cpegpon",
    ) -> Iterator[List[Any]]:
        """
        Generador que devuelve páginas (listas) de CPEs desde el endpoint de monitoring,
        sin esperar a terminar toda la paginación. Ideal para procesar en streaming.

        :param topology: Filtro por topología si se desea.
        :param limit: Tamaño de página (número de resultados por request).
        :param include_services: Si True, añade joins=services para obtener info de servicios.
        :param hostgroup: Hostgroup a filtrar; en redes GPON suele ser "cpegpon".
        :return: Iterador que va rindiendo listas de resultados (no una lista completa).
        """
        if topology is not None and not isinstance(topology, str):
            raise ValueError("El parámetro 'topology' debe ser un str si se proporciona.")

        # URL inicial del endpoint
        url = urljoin(self.host + '/', '/api/v2/monitoring/search/')

        # Parámetros iniciales (solo se envían en la primera petición)
        params = {
            "type": "Host",
            "limit": int(limit),
            "offset": 1,
            "hostgroups": hostgroup,
        }
        if include_services:
            params["joins"] = "services"
        if topology:
            params["topology"] = topology
            params["vars.administrative_info__topology"] = topology

        # Paginación usando "next"
        while url:
            data = self._request("GET", url, params=params)
            # Para siguiente iteración: no enviamos params porque `next` ya los incluye
            params = None

            results = data.get("results", [])
            yield results  # <-- devolución parcial en streaming

            # Obtener URL para la siguiente página
            url = data.get("next")



""" Ejemplo de USO de PAGINACION POR PAGE
krill = PyJMQKrill(host, user, pwd)
krill.login()

for page in krill.iter_cpes_monitoring_pages(topology="MiTopologia", limit=500):
    print(f"Recibida página con {len(page)} CPEs")
    for cpe in page:
        # Procesa la página en caliente, guarda en BD, sincroniza, etc.
        print(cpe.get("name"))
"""