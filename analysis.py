import openai
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

def analyze_and_summarize(topic_histories):
    full_text = ""
    for topic, log in topic_histories.items():
        full_text += f"【{topic}】\n"
        for entry in log:
            role = "ユーザー" if entry["role"] == "user" else "Bot"
            full_text += f"{role}: {entry['content']}\n"
        full_text += "\n"

    prompt = f"""
以下はユーザーとの3つの話題に関する会話です。
全体を通して、以下を日本語で出力してください：

1. 今日一日の要約（3〜5文程度）
2. ユーザーの総合的な感情傾向（ポジティブ／ネガティブ／混在／ニュートラル）
3. 有益なフィードバック（振り返りを深めるコメントや励まし）

[会話ログ]
{full_text}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

def generate_followup_question(topic, history):
    dialogue = "\n".join([
        f"{'Bot' if entry['role'] == 'assistant' else 'ユーザー'}: {entry['content']}"
        for entry in history
    ])
    prompt = f"""
以下は「{topic}」に関するユーザーとBotの会話です。これを踏まえて、
ユーザーに今日のことをさらに自然に深掘りさせるような質問を、やさしい日本語で1つ考えてください。

{dialogue}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response["choices"][0]["message"]["content"].strip()
