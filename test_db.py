import asyncio
import uuid
from datetime import datetime
from worker.db.engine import async_session
from worker.db.repositories import InferenceRepository
from worker.pipeline.validator import EventValidator

async def test():
    payload = '{"event_type":"inference_failed","request_id":"bed4d660-6be2-41e3-b15d-ddc928029391","conversation_id":"170ea683-9efe-408f-bb84-2ea8a1bd469e","provider":"gemini","model":"gemini-2.5-flash","timestamp":"2026-05-22T12:33:10.129607+00:00","ttft_ms":null,"total_latency_ms":4124,"error":"Gemini API Error: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.","status":"failed"}'
    event = EventValidator.validate(payload)
    print("Valid:", bool(event))
    async with async_session() as session:
        repo = InferenceRepository(session)
        inserted = await repo.insert(event)
        print("Inserted:", inserted)

asyncio.run(test())
