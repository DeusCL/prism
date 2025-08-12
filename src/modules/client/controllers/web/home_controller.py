from litestar import Controller, get
from litestar.response import Template



class HomeController(Controller):
    path = "/"

    @get("/")
    async def home(self) -> Template:
        """Página principal del sistema"""
        return Template("home.html", context={
            "title": "Dashboard - Prism",
            "page": "home",
            "stats": {
                "total_conversations": 45,
                "active_conversations": 12,
                "areas_configured": 5,
                "ai_responses_today": 78
            }
        })

    @get("/dashboard")
    async def dashboard(self) -> Template:
        """Dashboard con métricas del sistema"""
        return Template("dashboard.html", context={
            "title": "Dashboard - Prism",
            "page": "dashboard",
            "metrics": {
                "conversations_today": 23,
                "response_time_avg": 2.3,
                "satisfaction_rate": 94.5,
                "ai_accuracy": 89.2
            }
        })
