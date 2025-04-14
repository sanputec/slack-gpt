from flask import Flask, request
import os
import requests
from openai import OpenAI

app = Flask(__name__)

# 初始化 OpenAI client
client = OpenAI()

# Slack Bot Token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# 使用者對話記憶（記住每個使用者的上下文）
memory_dict = {}
max_context_length = 10  # 最多記住幾句對話

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

def send_image_to_slack(channel, image_url):
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "channel": channel,
        "blocks": [
            {
                "type": "image",
                "image_url": image_url,
                "alt_text": "GPT生成圖片"
            }
        ]
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=data)

@app.route("/", methods=["POST"])
def slack_events():
    data = request.get_json()

    # Slack webhook 驗證
    if data.get("type") == "url_verification":
        return data.get("challenge"), 200, {"Content-Type": "text/plain"}

    if "event" in data:
        event = data["event"]

        # 只處理私訊，並排除 bot 自己的訊息
        if event.get("type") == "message" and event.get("channel_type") == "im" and not event.get("bot_id"):
            user_input = event.get("text")
            channel = event.get("channel")
            user_id = event.get("user")

            # draw 指令：畫圖
            if user_input.strip().lower().startswith("/draw"):
                prompt = user_input.replace("/draw", "").strip()
                try:
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        n=1
                    )
                    image_url = response.data[0].url
                    send_image_to_slack(channel, image_url)
                except Exception as e:
                    reply_to_slack(channel, f"圖片生成失敗：{str(e)}")
                return "OK", 200

            # reset 指令：清除記憶
            if user_input.strip().lower() == "/reset":
                memory_dict[user_id] = []
                reply_to_slack(channel, "記憶已清除 ✅")
                return "OK", 200

            # 正常對話：使用 GPT-4o 並附加上下文
            history = memory_dict.get(user_id, [])
            history.append({"role": "user", "content": user_input})

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=history
                )
                reply = response.choices[0].message.content
                history.append({"role": "assistant", "content": reply})
                reply_to_slack(channel, reply)
            except Exception as e:
                reply_to_slack(channel, f"出錯了：{str(e)}")

            # 限制記憶長度
            if len(history) > max_context_length:
                history = history[-max_context_length:]
            memory_dict[user_id] = history

    return "OK", 200

# 讓 Flask 在 Render 上執行
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
