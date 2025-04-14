from flask import Flask, request
import openai
import os
import requests

app = Flask(__name__)

# 環境變數：OpenAI Key & Slack Bot Token
openai.api_key = os.environ.get("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# 回覆訊息給 Slack
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

# 接收 Slack webhook
@app.route("/", methods=["POST"])
def slack_events():
    data = request.json

    # 驗證用（首次設 webhook）
    if "challenge" in data:
        return data["challenge"]

    # 處理事件
    if "event" in data:
        event = data["event"]

        # 處理私訊
        if event.get("type") == "message" and event.get("channel_type") == "im":
            user_input = event.get("text")
            channel = event.get("channel")

            # 呼叫 GPT
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_input}]
                )
                reply = response.choices[0].message.content
                reply_to_slack(channel, reply)
            except Exception as e:
                reply_to_slack(channel, f"⚠️ 發生錯誤：{str(e)}")

    return "OK"
