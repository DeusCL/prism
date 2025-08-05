from litestar import Controller, get
from litestar.response import Template



class SimuladorController(Controller):
    path = "/simulador"

    @get("/")
    async def simulador(self) -> Template:
        """Página del simulador de clientes"""
        return Template("simulador.html", context={
            "title": "Simulador - Prism",
            "page": "simulador"
        })
