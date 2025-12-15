from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from service.websocket_manager import manager

socket_router = APIRouter(tags=["WebSocket"])


@socket_router.websocket("/ws/items")
async def websocket_endpoint(
        websocket: WebSocket,
        client_id: str = Query(..., description="Unique client identifier")
):
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "message": "Connected",
                    "client_id": client_id,
                    "total_clients": manager.get_client_count()
                })
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)
