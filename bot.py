import telebot
import requests
from datetime import datetime, timedelta, timezone

# Токен Telegram API и ключ OpenWeatherMap API
TELEGRAM_API_TOKEN = 'ваш токен'
OPENWEATHER_API_KEY = 'ваш токен'

# создаем объект бота
bot = telebot.TeleBot(TELEGRAM_API_TOKEN)

# кэширование данных о погоде
weather_cache = {}

start_txt = (
    'Привет! Это бот прогноза погоды. ☀️\n\n'
    'Отправьте боту название города, и он скажет, какая там температура и как она ощущается. 🌡️\n\n'
    'Вы также можете воспользоваться командой /help для получения помощи. ℹ️'
)

# обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, start_txt, parse_mode='Markdown')

# обработка команды /help
@bot.message_handler(commands=['help'])
def help(message):
    help_txt = (
        'Для получения прогноза погоды отправьте название города. 🌍\n'
        'Пример: Москва 🏙️\n\n'
        'Бот отправит текущую температуру, ощущаемую температуру, скорость ветра и рекомендации. 💨'
    )
    bot.send_message(message.from_user.id, help_txt, parse_mode='Markdown')

# обработка текстовых запросов
@bot.message_handler(content_types=['text'])
def get_weather_by_message(message):
    city = message.text.strip()
    get_weather(city, message.from_user.id)

def get_weather(city, user_id):
    # проверка в кэше
    if city in weather_cache and (datetime.now() - weather_cache[city]['time']).seconds < 600:
        weather_data = weather_cache[city]['data']
    else:
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={OPENWEATHER_API_KEY}'
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # добавление проверки статуса ответа
            weather_data = response.json()

            # сохранение в кэш
            weather_cache[city] = {'data': weather_data, 'time': datetime.now()}

        except requests.exceptions.RequestException as e:
            bot.send_message(user_id, '❌ Не удалось получить данные о погоде. Проверьте правильность написания города или попробуйте позже.')
            print(f'❌❌❌❌❌ Исключение: {e} ❌❌❌❌❌')
            return
        except KeyError:
            bot.send_message(user_id, '❌ Город не найден. Пожалуйста, проверьте написание и попробуйте снова.')
            return

    try:
        temperature = round(weather_data['main']['temp'])
        temperature_feels = round(weather_data['main']['feels_like'])
        wind_speed = round(weather_data['wind']['speed'])
        pressure_hpa = weather_data['main']['pressure']
        pressure_mmhg = round(pressure_hpa * 0.75006)
        description = weather_data['weather'][0]['description']

        # получение локального времени
        timezone_offset = weather_data['timezone']
        local_time = datetime.now(timezone.utc) + timedelta(seconds=timezone_offset)
        local_time_str = local_time.strftime('%H:%M:%S')

        weather_report = (
            f'🌆 Сейчас в городе {city} {temperature} °C\n'
            f'🌡️ Ощущается как {temperature_feels} °C\n'
            f'☁️ Описание: {description}\n'
            f'💨 Скорость ветра: {wind_speed} м/с\n'
            f'🔽 Давление: {pressure_mmhg} мм рт. ст.\n'
            f'⏰ Местное время: {local_time_str}\n'
        )

        if wind_speed < 5:
            weather_report += '✅ Погода хорошая, ветра почти нет'
        elif wind_speed < 10:
            weather_report += '🤔 На улице ветрено, оденьтесь чуть теплее'
        elif wind_speed < 20:
            weather_report += '❗️ Ветер очень сильный, будьте осторожны, выходя из дома'
        else:
            weather_report += '❌ На улице шторм, на улицу лучше не выходить'

        bot.send_message(user_id, weather_report)

    except KeyError as e:
        bot.send_message(user_id, '❌ Произошла ошибка при обработке данных о погоде. Пожалуйста, попробуйте позже.')
        print(f'❌❌❌❌❌ Исключение: {e} ❌❌❌❌❌')

# запуск бота
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f'❌❌❌❌❌ Сработало исключение: {e} ❌❌❌❌❌')
