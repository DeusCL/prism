from litestar import Controller, get
from litestar.response import Template



class AdminController(Controller):
    path = "/admin"

    @get("/areas")
    async def areas_admin(self) -> Template:
        """Página de administración de áreas"""
        return Template("admin/areas.html", context={
            "title": "Administración de Áreas - Prism",
            "page": "areas"
        })
