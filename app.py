from flask import Flask, request
import os
import requests
from openai import OpenAI

app = Flask(__name__)

# 建立 OpenAI client（會自動讀取 OPENAI_API_KEY 環境變數）
client = OpenAI()

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

    # ✅ Step 1: Slack 驗證 Webhook 時會發送 challenge
    if data.get("type") == "url_verification":
        return data.get("challenge"), 200, {"Content-Type": "text/plain"}

    # ✅ Step 2: 處理訊息事件
    if "event" in data:
        event = data["event"]

        # ✅ 私訊（DM）觸發且不是 bot 自己的訊息
        if event.get("type") == "message" and event.get("channel_type") == "im" and not event.get("bot_id"):
            user_input = event.get("text")
            channel = event.get("channel")

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": user_input}
                    ]
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"出錯了：{str(e)}"

            reply_to_slack(channel, reply)

    return "OK", 200

# ✅ 讓 Render 知道我們在哪個 port 上運行
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
