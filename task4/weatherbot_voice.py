import json
import requests
import os

"""
@EgorFineevWeatherBot
"""


def handle_voice(voice, tg_token):
    if (voice['duration'] > 30) or (voice['file_size'] > 1048576):
        return None
    else:
        r = requests.get(url=f"https://api.telegram.org/bot{tg_token}/getFile?file_id={voice['file_id']}")
        file_path = json.loads(r.text)['result']['file_path']
        audio_file = requests.get(url=f"https://api.telegram.org/file/bot{tg_token}/{file_path}").content

        yc_sst_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        sst_headers = {'Authorization': f"Api-Key {os.environ['API_KEY']}"}
        yc_sst_resp = requests.post(url=yc_sst_url, headers=sst_headers, data=audio_file, allow_redirects=False)
        text = json.loads(yc_sst_resp.text).get('result')
    return text


def send_weather(msg, geocode_request=None, weather_url=None, weather_key=None,
                 tg_url=None, tg_token=None):
    if (msg.get('location') is None) and (msg.get('text') is None) and (msg.get('voice') is None):
        text = 'Write address or send location or send voice with location'
    else:

        is_weather = True
        address = None
        if msg.get('location') is not None:
            lat = msg['location']['latitude']
            lon = msg['location']['longitude']
        elif msg.get('text') is not None:
            address = msg['text']
        else:
            address = handle_voice(msg['voice'], tg_token)
            if address is None:
                text = 'Too long voice message'
                is_weather = False
        if address is not None:
            geocode_resp = requests.post(url=geocode_request['url'], headers=geocode_request['headers'], json=[address])
            geocode_resp = json.loads(geocode_resp.text[1:-1])
            lat = geocode_resp['geo_lat']
            lon = geocode_resp['geo_lon']
        if is_weather:
            weather_resp = json.loads(requests.get(
                weather_url,
                params={
                    'lat': lat,
                    'lon': lon,
                    'appid': weather_key,
                    'units': 'metric',
                    'lang': 'ru'}).text)

            if weather_resp.get('main') is not None:
                text = f"??????????????????????: {weather_resp['main']['temp']}" \
                       f"\n?????????????????? ??????: {weather_resp['main']['feels_like']}\n"
                for w in weather_resp['weather']:
                    text += f"{w['description']}\n"
            else:
                text = 'Location is incorrect'
    requests.post(
        url=tg_url.format(token=tg_token, method='sendMessage'),
        json=dict(chat_id=msg['chat']['id'], text=text, reply_to_message_id=msg['message_id'])
    )


def create_geocode_req(secret, token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
        "X-Secret": secret
    }
    return dict(headers=headers, url="https://cleaner.dadata.ru/api/v1/clean/address")


def send_answer(msg, tg_url, tg_token, geocode_request,
                weather_url, weather_key):
    if (msg.get('text') is not None) and (msg['text'] == '/start'):
        requests.post(
            url=tg_url.format(token=tg_token, method='sendMessage'),
            json={'chat_id': msg['chat']['id'],
                  'text': 'Write address or send location'}
        )
    else:
        send_weather(msg,
                     tg_url=tg_url,
                     tg_token=tg_token,
                     geocode_request=geocode_request,
                     weather_url=weather_url,
                     weather_key=weather_key)


def handler(event, context):
    tg_token = os.environ['TG_TOKEN']
    weather_key = os.environ['WEATHER_KEY']
    geocode_key = os.environ['GEOCODE_SECRET']
    geocode_token = os.environ['GEOCODE_API']

    geocode_request = create_geocode_req(geocode_key, geocode_token)
    tg_url = 'https://api.telegram.org/bot{token}/{method}'
    weather_url = 'https://api.openweathermap.org/data/2.5/weather'

    update = json.loads(event['body'])
    message = update['message']
    send_answer(message, tg_url, tg_token, geocode_request,
                weather_url, weather_key)
