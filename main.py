from fastapi import FastAPI, Request, Header
from line_handler import handle_line_event

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(...)):
    body = await request.body()
    return await handle_line_event(body.decode(), x_line_signature)
