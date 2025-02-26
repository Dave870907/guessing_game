import os
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 初始化 Flask 應用
app = Flask(__name__)

# LINE Bot 設定（換成你自己的 Channel Access Token 和 Secret）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "Hello, LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    """ 處理 LINE Webhook 請求 """
    # 取得 X-Line-Signature
    signature = request.headers.get("X-Line-Signature")
    
    # 取得請求的 JSON 內容
    body = request.get_data(as_text=True)
    app.logger.info(f"收到 LINE Webhook: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ 處理收到的文字訊息 """
    user_message = event.message.text
    reply_text = f"你說了: {user_message}"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
