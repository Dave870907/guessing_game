from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from itertools import permutations
from collections import defaultdict
import os

app = Flask(__name__)

# 設定你的 LINE Bot Token & Secret
LINE_ACCESS_TOKEN = "Az6lo0YTC4ncLVv9ClanQL5WH0+/4G+FlBtq/SNqO3Ugh0jW1LD/BOnoeU+pl6RimXk2mLoNeqxdh4AFb2B1LLNdyOtBwJof8ZdLx990VnbsaB31BjLKWn4WFs6jJwI/ojqtUnJ7uhs3HlBgUysQAwdB04t89/1O/w1cDnyilFU="
LINE_SECRET = "77ee7f770c42e026f49ca5ba2c5cc47a"
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 儲存使用者的遊戲狀態
user_games = {}

def get_feedback(secret, guess):
    """計算 A (數字與位置皆正確) 和 B (數字正確但位置錯誤)"""
    A = sum(s == g for s, g in zip(secret, guess))
    B = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - A
    return A, B

def best_next_guess(candidates, all_numbers):
    """選擇最能縮小候選範圍的最佳猜測"""
    min_max_group_size = float('inf')
    best_guess = None

    for guess in all_numbers:
        feedback_groups = defaultdict(list)
        for num in candidates:
            feedback = get_feedback(num, guess)
            feedback_groups[feedback].append(num)
        max_group_size = max(len(group) for group in feedback_groups.values())
        if max_group_size < min_max_group_size:
            min_max_group_size = max_group_size
            best_guess = guess
    return best_guess

@app.route("/", methods=["GET"])
def home():
    return "1A2B LINE Bot 正在運行中！"

@app.route("/callback", methods=["POST"])
def callback():
    """處理 LINE Bot 訊息"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()

    # 開始新遊戲
    if user_text.lower() == "開始":
        all_numbers = [''.join(p) for p in permutations("0123456789", 4)]
        user_games[user_id] = {
            "candidates": all_numbers,
            "all_numbers": all_numbers,
            "attempts": 0
        }
        guess = best_next_guess(user_games[user_id]["candidates"], user_games[user_id]["all_numbers"])
        user_games[user_id]["attempts"] += 1
        reply_text = f"遊戲開始！\n請在心裡想好 4 位不重複數字。\n我先猜：{guess}\n請回覆 A 與 B，例如：1A2B"
    
    # 處理 A B 回應
    elif user_id in user_games and "A" in user_text and "B" in user_text:
        try:
            A, B = map(int, user_text.replace("A", "").replace("B", "").split())
        except ValueError:
            reply_text = "格式錯誤！請輸入正確的 A B 數字，例如：1A2B"
        else:
            if A == 4:
                reply_text = f"成功破解！總共嘗試 {user_games[user_id]['attempts']} 次。\n輸入 '開始' 再玩一次！"
                del user_games[user_id]
            else:
                candidates = user_games[user_id]["candidates"]
                candidates = [num for num in candidates if get_feedback(num, user_games[user_id]["candidates"][0]) == (A, B)]
                user_games[user_id]["candidates"] = candidates
                guess = best_next_guess(candidates, user_games[user_id]["all_numbers"])
                user_games[user_id]["attempts"] += 1
                reply_text = f"下一次猜測：{guess}\n請回覆 A 與 B，例如：1A2B"

    else:
        reply_text = "輸入 '開始' 來玩 1A2B！"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

