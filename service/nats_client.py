import json
from typing import Optional
from nats.aio.client import Client as NATS
from core.config import settings


class NATSClient:
    def __init__(self):
        self.nc: Optional[NATS] = None

    async def connect(self):
        try:
            self.nc = NATS()
            await self.nc.connect(servers=[settings.NATS_URL])
            print(f"Connected to NATS at {settings.NATS_URL}")
        except Exception as e:
            print(f"Failed to connect to NATS: {e}")
            self.nc = None

    async def disconnect(self):
        if self.nc:
            await self.nc.close()
            print("Disconnected from NATS")

    async def publish(self, subject: str, data: dict):
        if self.nc:
            try:
                message = json.dumps(data, ensure_ascii=False).encode('utf-8')
                await self.nc.publish(subject, message)
                await self.nc.flush()
            except Exception as e:
                print(f"Error publishing to NATS: {e}")

    async def subscribe(self, subject: str, callback):
        if self.nc:
            try:
                await self.nc.subscribe(subject, cb=callback)
                print(f"Subscribed to NATS subject: {subject}")
            except Exception as e:
                print(f"Error subscribing to NATS: {e}")


nats_client = NATSClient()
