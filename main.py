from flask import Flask, request, abort
import os
import urllib.request
import json
import unicodedata


"""
このプログラムはlast-fm-twitterと同様にランキングを作成します。LINE返答用です。
"""

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)


YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

LASTFM_API_KEY = os.environ['LASTFM_API_KEY']


class Period:
    SEVEN_DAYS = '7day'
    ONE_MONTH = '1month'
    TWELVE_MONTH = '12month'


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text1 = main(Period.SEVEN_DAYS)
    text2 = main(Period.ONE_MONTH)
    text3 = main(Period.TWELVE_MONTH)
    text = text1 + text2 + text3
    print(event)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
    
    
def main(period):
    data = get_last_fm_tracks(period)

    # 返信する文字列
    tweet_str = generate_ranking(data, period)

    print(tweet_str)
    return tweet_str + '\n'


def get_last_fm_tracks(period):
    url = 'http://ws.audioscrobbler.com/2.0/'
    params = {
        'format': 'json',
        'api_key': LASTFM_API_KEY,
        'method': 'user.getTopTracks',
        'user': 'SoraraP',
        'period': period,
    }
    req = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)))
    with urllib.request.urlopen(req) as res:
        body = res.read()
        body = json.loads(body)
        return body


def generate_ranking(data, period):
    track_titles = []
    track_artists = []
    track_playcount = []
    track_num = 0
    for track in data['toptracks']['track']:
        if track_num < 10:
            if int(track['playcount']) >= 1:
                track_titles.append(track['name'])
                track_artists.append(track['artist']['name'])
                track_playcount.append(track['playcount'])
                track_num += 1
    
    tweet = '私が'
    if period == Period.SEVEN_DAYS:
        tweet += '今週'
    elif period == Period.ONE_MONTH:
        tweet += '先月'
    elif period == Period.TWELVE_MONTH:
        tweet += '今年'
    tweet += '聞いた曲ランキング\n'
    for i in range(track_num):
        tweet += str(i + 1) + '位. ' + track_titles[i]
        tweet += ' [' + track_artists[i] + ']'
        tweet += '(' + str(track_playcount[i]) + '回)\n'
    
    return tweet


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
