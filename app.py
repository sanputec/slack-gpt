from flask import Flask, request
import openai
import os
import requests

app = Flask(__name__)

# 從環境變數取得金鑰
openai.api_key = os.environ.get("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

def reply_to_slack(channel, text):
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "channel": channel,
        "text": text
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=data)

@app.route("/", methods=["POST"])
def slack_events():
    data = request.get_json()

    # ✅ Slack 驗證（第一次連 webhook 時）
    if data.get("type") == "url_verification":
        return data.get("challenge"), 200, {"Content-Type": "text/plain"}

    # ✅ 處理 Slack 訊息事件
    if "event" in data:
        event = data["event"]

        # ✅ 處理 DM 訊息 + 避免自己觸發自己
        if event.get("type") == "message" and event.get("channel_type") == "im" and not event.get("bot_id"):
            user_input = event.get("text")
            channel = event.get("channel")

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_input}]
                )
                reply = response["choices"][0]["message"]["content"]
            except Exception as e:
                reply = f"出錯了：{str(e)}"

            reply_to_slack(channel, reply)

    return "OK", 200
