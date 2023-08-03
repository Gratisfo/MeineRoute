from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, \
    KeyboardButton, ParseMode, InputFile, MediaGroup, ChatActions
from math import radians, cos, sin, asin, sqrt
from config import api_token, admin_user_id
from io import BytesIO
import requests
import pandas as pd
from texts import welcome_message, random_message, near_bars, feedback_text
import random
import math
import asyncio

TOKEN_API = api_token
bot = Bot(TOKEN_API)
dp = Dispatcher(bot)


def get_sheet_data():
    spreadsheet_id = '104XHBWU2Q3dUUYB-OQCt8JcUXiM5vUY0id5KIL49C_4'
    file_name = 'https://docs.google.com/spreadsheets/d/{}/export?format=csv'.format(spreadsheet_id)
    r = requests.get(file_name)
    global data
    data = pd.read_csv(BytesIO(r.content))
    global bars
    bars = data['bar'].unique().tolist()
    return data, bars


get_sheet_data()
users_to_notify = set()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    users_to_notify.add(message.from_user.id)
    keyboard = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton(text="Бары рядом", callback_data='nearby_bars')
    button2 = InlineKeyboardButton(text="Рандомный бар", callback_data='random_bar')
    button3 = InlineKeyboardButton(text="Список всех баров", callback_data='list_all_bars')
    keyboard.add(button1, button2, button3)
    await message.answer(welcome_message, reply_markup=keyboard)


@dp.callback_query_handler(text='back_to_start_delete')
async def process_callback_back_to_start_delete(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    await bot.delete_message(chat_id=callback_query.message.chat.id,
                             message_id=callback_query.message.message_id)
    await send_welcome(callback_query.message)


@dp.callback_query_handler(text='back_to_start')
async def process_callback_back_to_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await send_welcome(callback_query.message)


@dp.message_handler(commands=['admin_mode'])
async def admin_mode_start(message: types.Message):
    if message.from_user.id == admin_user_id:
        button1 = InlineKeyboardButton(text="Обновить базу", callback_data='update')
        button2 = InlineKeyboardButton(text="Рассылка о фидбеке", callback_data='feedback_notification')
        keyboard = InlineKeyboardMarkup(row_width=1).add(button1, button2)
        await message.answer('Выберите дейсвтие, которое хотите осуществить', reply_markup=keyboard)


@dp.callback_query_handler(text='update')
async def process_update(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == admin_user_id:
        get_sheet_data()
        await bot.answer_callback_query(callback_query.id, text="База обновилась")
    else:
        await bot.answer_callback_query(callback_query.id, text="Вы не имеете права использовать эту команду.")


@dp.callback_query_handler(text='feedback_notification')
async def process_update(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == admin_user_id:
        url_button = types.InlineKeyboardButton(text='Оставить обратную связь', url='https://forms.gle/7bZtpwJurRfyd5Zd7')
        back_button = InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_start')
        keyboard = types.InlineKeyboardMarkup(row_width=1).add(url_button, back_button)

        for user_id in users_to_notify:
            await bot.send_message(user_id, feedback_text, reply_markup=keyboard)
            await bot.send_chat_action(user_id, ChatActions.TYPING)

    else:
        await bot.answer_callback_query(callback_query.id, text="Вы не имеете права использовать эту команду.")


@dp.callback_query_handler(text='nearby_bars')
async def process_callback_list_all_bars(callback_query: CallbackQuery):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    location_button = KeyboardButton(text="📍Поделиться геолокацией", request_location=True)
    keyboard.add(location_button)
    await bot.send_message(chat_id=callback_query.from_user.id, text=near_bars, reply_markup=keyboard)


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def process_location(message: types.Message):
    await message.answer(text='Ищем ближайшие к вам бары...', reply_markup=types.ReplyKeyboardRemove())
    latitude = message.location.latitude
    longitude = message.location.longitude
    data['distance'] = data.apply(lambda row: haversine(latitude, longitude, row['latitude'], row['longitude']), axis=1)
    df_sorted = data.sort_values(by=['distance'])
    nearest_bars_result = ''
    for i in range(3):
        bar_name = df_sorted.iloc[i]['bar']
        bar_distance = df_sorted.iloc[i]['distance']
        nearest_bars_result += f"{i + 1}. Бар: {bar_name}\nРасстояние: {bar_distance} км\n"
    buttons = [
        InlineKeyboardButton(text=str(idx + 1), callback_data=row[1]['callback'])
        for idx, row in enumerate(df_sorted.head(3).iterrows())
    ]
    start_button = InlineKeyboardButton(text="Вернуться в начало", callback_data='back_to_start')
    keyboard = InlineKeyboardMarkup(row_width=3).add(*buttons)
    keyboard.add(start_button)
    await message.answer(text=nearest_bars_result, reply_markup=keyboard)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return round(R * c, 2)


@dp.callback_query_handler(text='random_bar')
async def process_callback_random_bar(callback_query: CallbackQuery):
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    random_bar = random.choice(bars)
    button = InlineKeyboardButton(text=random_bar, callback_data=data[data['bar'] == random_bar]['callback'].values[0])
    one_more = InlineKeyboardButton(text="Еще раз", callback_data='random_bar')
    back_button = InlineKeyboardButton(text="Назад", callback_data='back_to_start')
    keyboard = InlineKeyboardMarkup(row_width=1).add(button, one_more, back_button)
    await bot.send_message(chat_id=callback_query.from_user.id, text=random_message, reply_markup=keyboard)


@dp.callback_query_handler(text='list_all_bars')
async def process_callback_list_all_bars(callback_query: CallbackQuery):
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    unique_bars = set()
    for idx, row in data.iterrows():
        unique_bars.add((row['bar'], row['callback']))

    buttons = [InlineKeyboardButton(text=bar, callback_data=callback) for bar, callback in unique_bars]

    keyboard = InlineKeyboardMarkup(row_width=3)
    back_button = InlineKeyboardButton(text="Назад", callback_data='back_to_start_delete')
    keyboard.add(*buttons)
    keyboard.add(back_button)

    await bot.send_message(chat_id=callback_query.from_user.id, text="Все доступные бары с историями.",
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda callback_query: callback_query.data in data['callback'].tolist())
async def process_callback_bar(callback_query: CallbackQuery):
    await bot.delete_message(chat_id=callback_query.message.chat.id,
                             message_id=callback_query.message.message_id)
    row = data.loc[data['callback'] == callback_query.data].iloc[0]
    bar_name = row['bar']
    address = row['address']
    unique = row['unique']
    if unique:
        story_info = 'Для этого бара есть одна история.'
    else:
        story_info = 'Этот бар хранит в себе несколько историй.'
    message_text = f"<b>Бар</b>: {bar_name}\n<b>Адрес</b>: {address}\n\n" + story_info
    here_button = InlineKeyboardButton(text="Я тут", callback_data=callback_query.data + '_here')
    back_button = InlineKeyboardButton(text="Назад", callback_data='back_to_start')
    keyboard = InlineKeyboardMarkup(row_width=2).add(here_button, back_button)
    await bot.send_message(callback_query.from_user.id, text=message_text,
                           reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query_handler(lambda callback_query: callback_query.data.replace('_here', '') in data['callback'].tolist())
async def process_callback_bar_here(callback_query: CallbackQuery):
    callback = callback_query.data.replace('_here', '')
    rows = data.loc[data['callback'] == callback]

    if rows.shape[0] > 1:
        buttons = []
        message_text = f"Вы можете выбрать одну историю героев представленных ниже. \n\n"
        for idx, row in enumerate(rows.iterrows()):
            name = row[1]['name']
            about = row[1]['about_author']
            try:
                if math.isnan(about):
                    about = 'Герой о себе ничего не рассказал(а) :с'
            except:
                pass

            message_text += f'История {idx + 1}:\n' \
                            f'<b>Имя героя</b>: {name} \n' \
                            f'<b>О герое</b>: {about} \n'
            buttons.append(InlineKeyboardButton(text=' История ' + str(idx + 1), callback_data=row[1]['user_id']))

        keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    else:
        name = rows['name'].values[0]
        about = rows['about_author'].values[0]
        try:
            if math.isnan(about):
                about = 'Герой о себе ничего не рассказал(а) :с'
        except:
            pass
        user_id = rows['user_id'].values[0]
        message_text = f'<b>Имя героя</b>: {name} \n' \
                       f'<b>О герое</b>: {about}'
        story_button = InlineKeyboardButton(text='История от героя', callback_data=str(user_id))
        keyboard = InlineKeyboardMarkup(row_width=2).add(story_button)

    back_button = InlineKeyboardButton(text="Назад", callback_data='back_to_start')
    keyboard.add(back_button)
    await bot.send_message(callback_query.from_user.id, text=message_text,
                           reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query_handler(lambda callback_query: int(callback_query.data) in data['user_id'].tolist())
async def process_callback_story(callback_query: CallbackQuery):
    row = data.loc[data['user_id'] == int(callback_query.data)].iloc[0]
    bar_name = row['bar']
    audio_ids = row['audio_id']
    drink = row['drink']
    contact = row['contact']
    photo_ids = row['photo_ids']

    if type(audio_ids) != float:
        await bot.send_audio(callback_query.from_user.id, audio=audio_ids)
        await asyncio.sleep(1)

    else:
        MAX_MESSAGE_LENGTH = 4096
        story = row['story']
        if len(story) <= MAX_MESSAGE_LENGTH:
            await bot.send_message(callback_query.from_user.id, text=story)
        else:
            chunks = [story[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(story), MAX_MESSAGE_LENGTH)]
            for chunk in chunks:
                await bot.send_message(callback_query.from_user.id, text=chunk)

    if type(drink) != float:
        message = f'<b>Рекомендация от героя:</b>\n{drink}'
        await bot.send_message(callback_query.from_user.id, text=message, parse_mode=ParseMode.HTML)

    if type(photo_ids) != float:
        await asyncio.sleep(1)
        photo_ids = photo_ids.split()
        media = [types.InputMediaPhoto(media=photo_id) for photo_id in photo_ids]
        try:
            await bot.send_media_group(callback_query.from_user.id, media=media)
        except:
            pass

    await asyncio.sleep(1)
    message_text = 'Надеюсь вам понравилась история, и вы хорошо проведете время в баре.'
    if type(contact) != float:
        message_text = f'Если хотите, вы можете связаться с автором и дать свою обратную связь о его истории, ' \
                       f'а также узнать дополнительные детали о месте.\n\n<b>Контакты героя:</b>\n{contact}'
    back_button = InlineKeyboardButton(text="Вернуться в главное меню", callback_data='back_to_start')
    keyboard = InlineKeyboardMarkup(row_width=1).add(back_button)
    await bot.send_message(callback_query.from_user.id, text=message_text, reply_markup=keyboard,
                           parse_mode=ParseMode.HTML)


@dp.message_handler(content_types=types.ContentTypes.PHOTO)
async def handle_photo(message: types.Message):
    if message.from_user.id == admin_user_id:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_path = await bot.get_file(photo.file_id)
        file_path = file_path.file_path

        await message.reply(f"ID фотографии: {file_id}\nПуть к файлу: {file_path}")
        await bot.send_photo(message.chat.id, photo=file_id)


@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_audio(message: types.Message):
    audio = message.audio
    file_info = await bot.get_file(audio.file_id)
    file_id = file_info.file_id
    await message.reply(f"ID вашего аудиофайла: {file_id}")

if __name__ == '__main__':
    executor.start_polling(dp)
