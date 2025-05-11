import openai
import os

openai.api_key = os.environ["OPENAI_API_KEY"]

def analyze_and_summarize(topics, logs):
    text = ""
    for topic in topics:
        relevant = [l["content"] for l in logs if topic in l["content"] or l["role"] == "user"]
        text += f"【{topic}】\n" + "\n".join(relevant) + "\n"

    prompt = f"""
以下はユーザーとの日記的な会話ログです。各トピックごとに以下を出力してください：
1. 要約（1行）
2. 感情（ポジティブ／ネガティブ／ニュートラル）
3. コメント（やさしい一言）

{text}
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def generate_followup_question(prev_user_message):
    prompt = f"ユーザーの発言「{prev_user_message}」をもとに、今日の出来事にフォーカスして深掘りする質問を1つ考えてください。やさしい日本語で。"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"].strip()
