import os
import random
from linebot import LineBotApi, WebhookParser
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ButtonsTemplate, PostbackAction
)
from dotenv import load_dotenv
from topics import TOPIC_CATEGORIES
from analysis import analyze_and_summarize, generate_followup_question

load_dotenv()
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
parser = WebhookParser(os.environ["LINE_CHANNEL_SECRET"])

user_sessions = {}
MAX_TURNS = 3

def pick_topic_by_category(category, used):
    options = list(set(TOPIC_CATEGORIES[category]) - set(used))
    return random.choice(options) if options else None

def generate_topic_choices(used):
    choices = {}
    for cat in ["positive", "negative", "neutral"]:
        picked = pick_topic_by_category(cat, used)
        if picked:
            choices[cat] = picked
    return choices

def build_category_menu(topics_by_category):
    actions = []
    for cat, topic in topics_by_category.items():
        actions.append(PostbackAction(label=cat.capitalize(), data=topic))
    actions.append(PostbackAction(label="他の話題", data="reshuffle"))
    return TemplateSendMessage(
        alt_text="トピックカテゴリ選択",
        template=ButtonsTemplate(
            text="次から選んでね！「終わり」と送ると日記が終了します。",
            actions=actions
        )
    )

async def handle_line_event(body: str, signature: str):
    events = parser.parse(body, signature)
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_id = event.source.user_id
            msg = event.message.text.strip().lower()

            if msg == "書く":
                user_sessions[user_id] = {
                    "used_topics": [],
                    "current_topic": None,
                    "topic_logs": [],
                    "topic_history": {},
                    "turn": 0
                }
                greeting = "📝 今日を一緒に振り返ろう！\n・ポジティブ／ネガティブ／中立から話題を選んで3回ほど会話します。\n・「終わり」と送ればいつでも終了できます。"
                session = user_sessions[user_id]
                session["topics_by_category"] = generate_topic_choices(session["used_topics"])
                menu = build_category_menu(session["topics_by_category"])
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=greeting), menu])

            elif msg == "終わり":
                session = user_sessions.get(user_id)
                if session:
                    result = analyze_and_summarize(session["topic_history"])
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
                    del user_sessions[user_id]
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="まだ日記を始めていないみたい。まずは「書く」と送ってね。"))

            elif user_id in user_sessions:
                session = user_sessions[user_id]
                if session["current_topic"] is None:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="まず話題を選んでね。"))
                else:
                    session["topic_logs"].append({"role": "user", "content": msg})
                    session["topic_history"][session["current_topic"]].append({"role": "user", "content": msg})
                    session["turn"] += 1

                    if session["turn"] < MAX_TURNS:
                        followup_q = generate_followup_question(session["current_topic"], session["topic_history"][session["current_topic"]])
                        session["topic_logs"].append({"role": "assistant", "content": followup_q})
                        session["topic_history"][session["current_topic"]].append({"role": "assistant", "content": followup_q})
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=followup_q))
                    else:
                        thanks = f"ありがとう！「{session['current_topic']}」の話はここまでにしよう。次の話題を選んでみようか！"
                        session["used_topics"].append(session["current_topic"])
                        session["current_topic"] = None
                        session["turn"] = 0
                        session["topics_by_category"] = generate_topic_choices(session["used_topics"])
                        menu = build_category_menu(session["topics_by_category"])
                        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=thanks), menu])
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text="📒 このBotは日記を手伝います。「書く」と送るとスタートします。"
                ))

        elif hasattr(event, 'postback'):
            user_id = event.source.user_id
            data = event.postback.data
            session = user_sessions.get(user_id)
            if not session:
                return
            if data == "reshuffle":
                session["topics_by_category"] = generate_topic_choices(session["used_topics"])
                menu = build_category_menu(session["topics_by_category"])
                line_bot_api.reply_message(event.reply_token, menu)
            else:
                session["current_topic"] = data
                opening = f"今日の「{data}」について、どんなことがあった？"
                session["topic_logs"].append({"role": "assistant", "content": opening})
                session["topic_history"][data] = [{"role": "assistant", "content": opening}]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=opening))
