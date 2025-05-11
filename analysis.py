import openai
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

def analyze_and_summarize(topic_histories):
    prompt = "以下はユーザーとBotによる日記的な会話ログです。各トピックごとに次の形式でまとめてください：\n" +              "1. トピック名\n2. 要約（1行）\n3. 感情（ポジティブ／ネガティブ／ニュートラル）\n4. コメント（やさしい一言）\n\n"

    for topic, log in topic_histories.items():
        prompt += f"【{topic}】\n"
        for entry in log:
            role = "ユーザー" if entry["role"] == "user" else "Bot"
            prompt += f"{role}: {entry['content']}\n"
        prompt += "\n"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response["choices"][0]["message"]["content"].strip()
