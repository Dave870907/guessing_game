import os
import random
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 儲存用戶遊戲狀態
user_games = {}

def generate_possible_numbers():
    """ 產生所有可能的 4 位不重複數字組合 """
    numbers = []
    for num in range(1023, 9877):  # 1023 是第一個 4 位不重複數字，9876 是最後一個
        str_num = str(num)
        if len(set(str_num)) == 4:  # 確保數字不重複
            numbers.append(str_num)
    return numbers

def get_next_guess(possible_numbers):
    """ 從剩餘可能數字中選擇一個來猜 """
    return random.choice(possible_numbers)

def filter_possible_numbers(possible_numbers, guess, a, b):
    """ 根據 A B 的結果過濾可能的數字 """
    def count_ab(secret, guess):
        A = sum(1 for i in range(4) if secret[i] == guess[i])
        B = sum(1 for i in range(4) if guess[i] in secret) - A
        return A, B

    return [num for num in possible_numbers if count_ab(num, guess) == (a, b)]

@app.route("/", methods=["GET"])
def home():
    return "Hello, LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    """ 處理 LINE Webhook 請求 """
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200
    
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip().upper()  # 統一轉大寫

    if user_message in ["開始", "NEW GAME", "RESTART"]:
        possible_numbers = generate_possible_numbers()
        first_guess = random.choice(possible_numbers)
        user_games[user_id] = {
            "possible_numbers": possible_numbers,
            "last_guess": first_guess
        }
        reply_text = f"請在心中選一個 4 位不重複的數字！\n\n我的第一個猜測是：{first_guess}\n請回覆「XA YB」，例如「1A2B」"
    elif user_id in user_games:
        # 嘗試解析 A B 數值
        try:
            import re
            match = re.match(r"(\d)A(\d)B", user_message)  # 確保格式為 2A1B
            if match:
                a, b = map(int, match.groups())

                game_data = user_games[user_id]
                last_guess = game_data["last_guess"]
                possible_numbers = game_data["possible_numbers"]

                if a == 4:
                    reply_text = f"🎉 太棒了！我猜對了！答案是 {last_guess}。\n輸入「開始」來玩新的一局！"
                    del user_games[user_id]  # 遊戲結束
                else:
                    # 過濾可能的數字並進行下一次猜測
                    possible_numbers = filter_possible_numbers(possible_numbers, last_guess, a, b)
                    if not possible_numbers:
                        reply_text = "😵 這個 A B 可能有錯誤，請確認你的回應！"
                    else:
                        new_guess = random.choice(possible_numbers)
                        user_games[user_id] = {
                            "possible_numbers": possible_numbers,
                            "last_guess": new_guess
                        }
                        reply_text = f"我的下一個猜測是：{new_guess}\n請回覆「XA YB」，例如「1A2B」"
            else:
                reply_text = "❌ 請輸入正確的格式，例如「1A2B」，不要有空格或錯誤的符號。"
        except Exception as e:
            reply_text = "❌ 發生錯誤，請確保輸入格式為「XA YB」，例如「1A2B」。"
    else:
        reply_text = "輸入「開始」，讓我來猜你的 4 位數字！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
