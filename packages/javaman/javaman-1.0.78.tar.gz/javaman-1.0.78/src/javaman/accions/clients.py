from javaman.connexio import JManCon


class Clients:
    __slots__ = '_con'

    _url_crear_client = '/clients'
    _url_get_client = '/clients'
    _url_get_client_llista = '/clients/llista'
    _url_importar_tercers = '/importar_tercers'
    _url_client_central = '/clients_seccions?tercer_seccio_id={tercer_seccio_id}'
    _url_clients_seccions = '/clients_seccions?client_central_id={client_central_id}'
    _url_clients_classificacions_by_client_id = '/clients/{client_id}/classificacions'
    _url_clients_classificacions = '/clients/clients_classificacions'
    _url_classificacions_clients = '/clients/classificacions'

    def __init__(self, con: JManCon):
        self._con = con

    def crear(self, p_client: dict):
        req = self._con.post(url=self._url_crear_client, data=p_client)
        return req.json()

    def get_client(self, p_client: int):
        req = self._con.get(url=self._url_crear_client+'/'+str(p_client))
        return req.json()

    def get_client_by_nif(self, p_nif: str):
        req = self._con.get(url=self._url_get_client+'?actiu=S&nif='+p_nif)
        return req.json()

    def importar_tercers(self, p_dades: dict):
        req = self._con.post(url=self._url_importar_tercers, data=p_dades)
        return req.json()

    def get_client_central_id(self, p_tercer_seccio_id: int) -> int:
        client_id = None
        req = self._con.get(url=self._url_client_central.format(tercer_seccio_id=p_tercer_seccio_id))
        result = req.json()
        if result is not None and len(result) > 0:
            client_id = result[0]["client_id"]
        return client_id

    def get_seccions_client(self, p_client_central_id: int) -> list:
        req = self._con.get(url=self._url_clients_seccions.format(client_central_id=p_client_central_id))
        result = req.json()
        return result

    def get_clients_classificacions_by_client_id(self, p_client_id: int) -> list:
        req = self._con.get(url=self._url_clients_classificacions_by_client_id.format(client_id=p_client_id))
        result = req.json()
        return result

    def get_clients_classificacions(self) -> list:
        req = self._con.get(url=self._url_clients_classificacions)
        result = req.json()
        return result

    def get_classificacions(self) -> list:
        req = self._con.get(url=self._url_classificacions_clients)
        result = req.json()
        return result
