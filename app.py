import os
import random
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE Bot 設定（換成你的 Channel Access Token 和 Secret）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 儲存每位用戶的遊戲狀態
user_games = {}

def generate_secret_number():
    """ 產生一組不重複的 4 位數字 """
    digits = list("0123456789")
    random.shuffle(digits)
    return "".join(digits[:4])

def calculate_AB(secret, guess):
    """ 計算幾 A 幾 B """
    A = sum(1 for i in range(4) if secret[i] == guess[i])
    B = sum(1 for i in range(4) if guess[i] in secret) - A
    return A, B

@app.route("/", methods=["GET"])
def home():
    return "Hello, LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    """ 處理 LINE Webhook 請求 """
    signature = request.headers.get("X-Line-Signature")
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
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 重新開始遊戲
    if user_message.lower() in ["開始", "重新開始", "new game"]:
        secret_number = generate_secret_number()
        user_games[user_id] = secret_number
        reply_text = "遊戲開始！請輸入 4 位不重複數字來猜答案。"
    elif user_id in user_games:
        # 使用者已經開始遊戲，判斷輸入是否合法
        if len(user_message) == 4 and user_message.isdigit() and len(set(user_message)) == 4:
            secret_number = user_games[user_id]
            A, B = calculate_AB(secret_number, user_message)
            if A == 4:
                reply_text = f"🎉 恭喜你猜對了！答案是 {secret_number}，遊戲結束！請輸入「開始」來玩新的一局。"
                del user_games[user_id]  # 移除遊戲紀錄
            else:
                reply_text = f"{A}A{B}B，請再試試看！"
        else:
            reply_text = "請輸入 **4 位不重複的數字**，例如 1234。"
    else:
        reply_text = "請輸入「開始」來玩 1A2B 猜數字遊戲！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
