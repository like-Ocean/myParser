from .product import product
from .task import task
from .websocket import websocket


routes = [
    product.router,
    task.router,
    websocket.socket_router
]
