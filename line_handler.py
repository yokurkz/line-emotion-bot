import os
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from analysis import analyze_text
from dotenv import load_dotenv

load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
parser = WebhookParser(os.environ["LINE_CHANNEL_SECRET"])

async def handle_line_event(body: str, signature: str):
    events = parser.parse(body, signature)
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            result = analyze_text(event.message.text)
            reply_text = f"感情: {result['emotion']}\n要約: {result['summary']}"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    return "OK"
