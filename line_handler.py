import os
import random
from linebot import LineBotApi, WebhookParser
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ButtonsTemplate, PostbackAction
)
from dotenv import load_dotenv
from topics import TOPIC_LIST
from analysis import analyze_and_summarize, generate_followup_question

load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
parser = WebhookParser(os.environ["LINE_CHANNEL_SECRET"])

user_sessions = {}

MAX_TOPICS = 3
MAX_TURNS = 3

def generate_topic_template(used_topics):
    available = list(set(TOPIC_LIST) - set(used_topics))
    choices = random.sample(available, min(3, len(available)))
    actions = [PostbackAction(label=topic, data=topic) for topic in choices]
    actions.append(PostbackAction(label="記入を終える", data="finish"))

    template = ButtonsTemplate(
        text="次に話したいトピックを選んでね！",
        actions=actions
    )
    return TemplateSendMessage(alt_text="トピック選択", template=template)

async def handle_line_event(body: str, signature: str):
    events = parser.parse(body, signature)
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_id = event.source.user_id
            msg = event.message.text.strip()

            if msg.lower() == "書く":
                user_sessions[user_id] = {
                    "used_topics": [],
                    "current_topic": None,
                    "topic_logs": [],
                    "turn": 0,
                    "topics_done": 0
                }
                tmpl = generate_topic_template([])
                line_bot_api.reply_message(event.reply_token, tmpl)

            elif user_id in user_sessions:
                session = user_sessions[user_id]
                if session["current_topic"] is None:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="トピックを選んでね！"))
                else:
                    session["topic_logs"].append({"role": "user", "content": msg})
                    session["turn"] += 1
                    if session["turn"] < MAX_TURNS:
                        followup_q = generate_followup_question(msg)
                        session["topic_logs"].append({"role": "assistant", "content": followup_q})
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=followup_q))
                    else:
                        session["used_topics"].append(session["current_topic"])
                        session["topics_done"] += 1
                        session["current_topic"] = None
                        session["turn"] = 0
                        if session["topics_done"] >= MAX_TOPICS:
                            result = analyze_and_summarize(session["used_topics"], session["topic_logs"])
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
                            del user_sessions[user_id]
                        else:
                            tmpl = generate_topic_template(session["used_topics"])
                            line_bot_api.reply_message(event.reply_token, tmpl)
        elif hasattr(event, 'postback'):
            user_id = event.source.user_id
            data = event.postback.data
            session = user_sessions.get(user_id)
            if not session:
                return
            if data == "finish":
                result = analyze_and_summarize(session["used_topics"], session["topic_logs"])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
                del user_sessions[user_id]
            else:
                session["current_topic"] = data
                opening = f"{data}について、どんなことがあった？"
                session["topic_logs"].append({"role": "assistant", "content": opening})
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=opening))
