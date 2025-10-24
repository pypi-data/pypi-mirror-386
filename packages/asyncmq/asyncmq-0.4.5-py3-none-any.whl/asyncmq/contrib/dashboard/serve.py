from lilya.apps import Lilya
from lilya.middleware.base import DefineMiddleware
from lilya.middleware.cors import CORSMiddleware
from lilya.routing import Include

from asyncmq import monkay
from asyncmq.contrib.dashboard.application import dashboard

dash_app = Lilya(
    routes=[Include(path="/", app=dashboard)],
    middleware=[
        DefineMiddleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        ),
        monkay.settings.dashboard_config.session_middleware,
    ],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("serve:dash_app", host="0.0.0.0", port=8000, reload=True)
