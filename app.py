from flask import Flask, request
import openai
import os
import requests

app = Flask(__name__)

# 從環境變數取得 API 金鑰
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

    # ✅ Step 1: 處理 Slack 驗證 (url_verification)
    if data.get("type") == "url_verification":
        return data.get("challenge"), 200, {"Content-Type": "text/plain"}

    # ✅ Step 2: 處理來自 Slack 的訊息事件
    if "event" in data:
        event = data["event"]

        # 處理來自私訊 (im) 的訊息
        if event.get("type") == "message" and event.get("channel_type") == "im" and not event.get("bot_id
