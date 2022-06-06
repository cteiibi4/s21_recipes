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


def delete_last_message(func):
    async def wrapper(msg):
        if type(msg) == types.Message:
            message_id = msg["message_id"]
            user = get_user(msg['from']['id'])
        else:
            message_id = msg.id
            user = get_user(msg.from_user['id'])
        if user.last_message:
            try:
                await bot.delete_message(user.user_id, user.last_message)
            except:
                pass
        new_message = await func(msg)
        if type(msg) == types.Message:
            await bot.delete_message(user.user_id, message_id)
        user.last_message = new_message["message_id"]
        session.commit()
    return wrapper


@dp.message_handler(commands=['start'])
@delete_last_message
async def send_welcome(message: types.Message):

    """
    This handler will be called when user sends `/start`
    """
    user_id = message['from']['id']
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    poll_keyboard.add(types.InlineKeyboardButton(text="Каталог", callback_data='catalog'))
    poll_keyboard.add(types.InlineKeyboardButton(text="Топ 10", callback_data='top_10'))
    msg = await bot.send_message(chat_id=user_id, text=HELLO_MESSAGE,
                                 reply_markup=poll_keyboard)
    return msg


@dp.callback_query_handler(lambda c: True if 'catalog' in c.data else False)
@delete_last_message
async def catalog(callback_query: types.CallbackQuery):
    print("+++++")
    print(callback_query.data)
    user = get_user(user_id=callback_query.from_user['id'])
    count_recipes = session.query(Recipe).count()
    offset = user.last_state
    text = f"Каталог\nстраница {int(offset/LIMIT)}"
    if not offset:
        user.last_state = 0
        offset = 0
    session.commit()
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    recipes = session.query(Recipe).order_by(Recipe.id).offset(offset).limit(LIMIT)
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    if offset < count_recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text="Вперед ▶", callback_data=f'rigth'))
    if offset > LIMIT:
        poll_keyboard.add(types.InlineKeyboardButton(text="Назад ◀", callback_data=f'left'))
    msg = await bot.send_message(chat_id=user.user_id, text=text,
                                 reply_markup=poll_keyboard)
    return msg

@dp.callback_query_handler(lambda c: True if 'top_10' in c.data else False)
@delete_last_message
async def top_10(callback_query: types.CallbackQuery):
    print(111111)
    user_id = callback_query.from_user['id']
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    recipes = session.query(Recipe).order_by(Recipe.views).limit(10)
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    poll_keyboard.add(types.InlineKeyboardButton(text="Каталог", callback_data='catalog'))
    msg = await bot.send_message(chat_id=user_id, text="Top 10",
                                 reply_markup=poll_keyboard)
    return msg

@dp.callback_query_handler(lambda c: True if ('right' or 'left') in c.data else False)
@delete_last_message
async def catalog_move(callback_query: types.CallbackQuery):
    print("555555")
    print(callback_query.data)
    user = get_user(callback_query.from_user['id'])
    offset = int(user.last_state)
    if 'right' in callback_query.data:
        user.last_state = offset + LIMIT
    elif 'left' in callback_query.data:
        user.last_state = offset - LIMIT
    session.commit()
    offset = int(user.last_state)
    text = f"Каталог\nстраница {int(offset / LIMIT)}"
    recipes = session.query(Recipe).order_by(Recipe.id).offset(offset).limit(LIMIT)
    count_recipes = session.query(Recipe).count()
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    if offset < count_recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text="Вперед ▶", callback_data=f'rigth'))
    if offset > LIMIT:
        poll_keyboard.add(types.InlineKeyboardButton(text="Назад ◀", callback_data=f'left'))
    msg = await bot.send_message(chat_id=user.user_id, text=text,
                                 reply_markup=poll_keyboard)
    return msg


@dp.callback_query_handler(lambda c: True if "r_" in c.data else False)
@delete_last_message
async def recipe(callback_query: types.CallbackQuery):
    print("****")
    print(callback_query.data)
    recipe_id = callback_query.data[2:]
    user = get_user(callback_query.from_user['id'])
    recipe = session.query(Recipe).get(recipe_id)
    caption = f"{recipe.name}\n{recipe.description}"
    images = recipe.images
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    poll_keyboard.add(types.InlineKeyboardButton(text="Назад ◀", callback_data=f'/catalog'))
    msg = await bot.send_photo(user.user_id, images,
                                   caption=caption,
                                   reply_markup=poll_keyboard)
    return msg

def get_user(user_id):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except:
        user = None
    if not user:
        user = User(user_id)
        session.add(user)
        session.commit()
    return user

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
