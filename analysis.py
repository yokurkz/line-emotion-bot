import openai
import os
openai.api_key = os.environ["OPENAI_API_KEY"]

def analyze_text(text: str):
    prompt = f"以下の文章の感情と要約を出力してください。\n\n{text}\n\n形式: 感情: ○○ / 要約: △△"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    content = response["choices"][0]["message"]["content"]
    try:
        parts = dict(p.strip().split(": ") for p in content.split(" / "))
        return {"emotion": parts.get("感情", ""), "summary": parts.get("要約", "")}
    except:
        return {"emotion": "不明", "summary": "うまく解析できませんでした"}
