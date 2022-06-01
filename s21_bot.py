from aiogram import Bot, Dispatcher, executor, types
from sqlalchemy import create_engine, or_
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from init_db import User, Recipe, Image
from common import BASE
from settings import TOKEN, HELLO_MESSAGE

engine = create_engine(f'sqlite:///{BASE}', echo=True)
conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()
LIMIT = 10
# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):

    """
    This handler will be called when user sends `/start` or `/help` command
    """
    user_id = message['from']['id']
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    recipes = session.query(Recipe).order_by(Recipe.id).limit(LIMIT)
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    msg = await bot.send_message(chat_id=user_id, text=HELLO_MESSAGE,
                                     reply_markup=poll_keyboard)
    return msg


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    await message.answer(message.text)


def delete_last_message(func):
    def wrapper(message: types.Message):
        message_id = message["message_id"]
        user = get_user(message['from']['id'])
        if user.last_message:
            await bot.delete_message(user.user_id, user.last_message)
        new_message = func(message)
        await bot.delete_message(user.user_id, message_id)
        user.last_message = new_message["message_id"]
        session.commit()
    return wrapper


def get_user(user_id):
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id)
        session.add(user)
        session.commit()
    return user

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
