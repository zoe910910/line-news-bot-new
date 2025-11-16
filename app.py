# app.py

import os
from flask import Flask, request, abort
import urllib.parse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. 凭证设定 (请确认这两个 LINE 凭证是正确的) ---
# 警告：由于您已将 LINE Bot 迁移到 Render，请确保此处的凭证是正确的。
YOUR_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_BOT_ACCESS_TOKEN', "K34uCEOUEhVUYr6THN9oV+04VH0Ytyg2l7e5XrsQHa8QPcHtkeoBzOWAzXbC8oRGQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNhdyxuKRA4QPz1BR27uglGvb4gDDR3NQxEs7VpHTBBBagdB04t89/1O/w1cDnyilFU=")
YOUR_CHANNEL_SECRET = os.environ.get('LINE_BOT_SECRET', "72c1dd7da164b7d96ae69d2cc0965f66")
# ---------------------------------------------

# Flask 应用程序初始化
app = Flask(__name__)

# LINE Bot API 初始化
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# 端口设定（Render 需要）
port = int(os.environ.get('PORT', 5000))

# --- 2. 路由：接收 LINE Webhook 的唯一入口 ---
@app.route("/callback", methods=['POST'])
def callback():
    """处理来自 LINE 的 Webhook 请求"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)
    
    return 'OK'

# --- 3. 事件处理器：处理用户发送的文本消息 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """处理用户发送的文字消息"""
    user_brand = event.message.text.strip()
    
    # 调用生成摘要的函数
    reply_text = generate_news_summary(user_brand)
    
    # 发送回复
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. 核心逻辑：生成 Google 搜索链接 (无需 API) ---
def generate_news_summary(brand_name):
    """
    生成一个限定当周新闻的 Google 搜索链接，并返回给用户。
    """
    
    # 使用 urllib.parse.quote 对品牌名称进行 URL 编码
    encoded_brand_name = urllib.parse.quote(brand_name)
    
    # qdr:w 参数表示搜索结果限定在“过去一周” (Past week)
    news_search_url = f"https://www.google.com/search?q={encoded_brand_name}+新聞&tbs=qdr:w&hl=zh-TW"
    
    # 撰写回复内容 (Markdown/Text 格式)
    # LINE Bot API 默认文本消息支持自动识别 URL 为可点击链接
    summary = f"🤖 **{brand_name} 当周新闻摘要** 整理如下：\n\n"
    # 由于没有 AI 摘要，我们用提示文字代替，指导用户点击链接查看：
    summary += f"**1. 新闻摘要：** 由于没有 AI 摘要功能，请点击下方链接，直接查看 Google 针对 '{brand_name}' 的当周新闻。\n\n"
    summary += f"**2. 当周新闻网址：**\n"
    summary += f"🔗 [点击查看 {brand_name} 最新当周新闻]({news_search_url})\n\n"
    summary += f"(资讯来源：Google 搜索，时间范围：过去一周)"

    return summary


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
```

### 📦 文件依赖更新：`requirements.txt`

由于我们不再使用 `requests` 库 (用于调用 Gemini API)，理论上可以删除它，但为了稳定性，我们保持 `requirements.txt` 不变，或者改为：

```
# requirements.txt
Flask
gunicorn
line-bot-sdk