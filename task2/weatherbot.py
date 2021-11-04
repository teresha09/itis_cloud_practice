import json
import requests
import time

"""
@EgorFineevWeatherBot
"""


def read_config(config_path_):
    with open(config_path_, 'r') as f:
        conf_data_ = json.load(f)
    return conf_data_


def send_weather(msg):
    if msg['message'].get('location') is not None:
        lat = msg['message']['location']['latitude']
        lon = msg['message']['location']['longitude']
    else:
        address = msg['message']['text']
        geocode_resp = requests.post(url=geocode_request['url'], headers=geocode_request['headers'], json=[ address ])
        geocode_resp = json.loads(geocode_resp.text[1:-1])
        lat = geocode_resp['geo_lat']
        lon = geocode_resp['geo_lon']
    weather_resp = json.loads(requests.get(
        weather_url,
        params={
            'lat': lat,
            'lon': lon,
            'appid': weather_key,
            'units': 'metric',
            'lang': 'ru'}).text)
    if weather_resp.get('main') is not None:
        text = f"Температура: {weather_resp['main']['temp']}" \
               f"\nОщущается как: {weather_resp['main']['feels_like']}\n"
        for w in weather_resp['weather']:
            text += f"{w['description']}\n"
    else:
        text = 'Write address or send location'
    requests.post(
        url=tg_url.format(token=tg_token, method='sendMessage'),
        json={'chat_id': msg['message']['chat']['id'], 'text': text,
              'reply_to_message_id': msg['message']['message_id']}
    )


def create_geocode_req(secret, token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
        "X-Secret": secret
    }
    return dict(headers=headers, url="https://cleaner.dadata.ru/api/v1/clean/address")


def send_answer(msg):
    if (msg['message'].get('text') is not None) and (msg['message']['text'] == '/start'):
        requests.post(
            url=tg_url.format(token=tg_token, method='sendMessage'),
            json={'chat_id': msg['message']['chat']['id'], 'text': 'Write address or send location'}
        )
    else:
        send_weather(msg)


if __name__ == '__main__':
    offset = None

    config_path = 'config.json'
    conf_data = read_config(config_path)
    tg_token = conf_data['tg_token']
    weather_key = conf_data['weather_key']
    geocode_key = conf_data['geocode_secret']
    geocode_token = conf_data['geocode_api']

    geocode_request = create_geocode_req(geocode_key, geocode_token)
    tg_url = 'https://api.telegram.org/bot{token}/{method}'
    weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    while True:
        if offset is None:
            tg_update_url = tg_url.format(token=tg_token, method='getUpdates')
        else:
            tg_update_url = tg_url.format(token=tg_token, method=f'getUpdates?offset={offset}')
        r = requests.get(tg_update_url)
        updates = json.loads(r.text)['result']
        for upd in updates:
            send_answer(upd)

        if len(updates) > 0:
            offset = updates[-1]['update_id'] + 1
        time.sleep(10)
