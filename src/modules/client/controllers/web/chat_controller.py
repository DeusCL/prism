from litestar import Controller, get
from litestar.response import Template



class ChatController(Controller):
    path = "/chats"

    @get("/")
    async def chats(self) -> Template:
        """Página de los chats con los clientes"""
        return Template("chats.html", context={
            "title": "Chats - Prism",
            "page": "chats"
        })
