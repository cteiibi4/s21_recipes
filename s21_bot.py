import os
from aiogram import Bot, Dispatcher, executor, types
from sqlalchemy import create_engine, or_
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from init_db import User, Recipe, Image
from common import BASE, IMAGE_PATH
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
                for msg_id in user.last_message.split(","):
                    await bot.delete_message(user.user_id, int(msg_id))
            except:
                pass
        new_message_id = await func(msg)
        if type(msg) == types.Message:
            await bot.delete_message(user.user_id, message_id)
        user.last_message = new_message_id
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
    return msg["message_id"]


@dp.callback_query_handler(lambda c: True if 'main' in c.data else False)
@delete_last_message
async def send_main(callback_query: types.CallbackQuery):

    """
    This handler will be called when user sends `/start`
    """
    user_id = callback_query.from_user['id']
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    poll_keyboard.add(types.InlineKeyboardButton(text="Каталог", callback_data='catalog'))
    poll_keyboard.add(types.InlineKeyboardButton(text="Топ 10", callback_data='top_10'))
    msg = await bot.send_message(chat_id=user_id, text=HELLO_MESSAGE,
                                 reply_markup=poll_keyboard)
    return msg["message_id"]


@dp.callback_query_handler(lambda c: True if 'catalog' in c.data else False)
@delete_last_message
async def catalog(callback_query: types.CallbackQuery):
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
    if offset < (count_recipes - LIMIT):
        poll_keyboard.add(types.InlineKeyboardButton(text="Вперед ▶", callback_data=f'right'))
    if offset >= LIMIT:
        poll_keyboard.add(types.InlineKeyboardButton(text="Назад ◀", callback_data=f'left'))
    poll_keyboard.add(types.InlineKeyboardButton(text="На главную ⬆", callback_data=f'main'))
    msg = await bot.send_message(chat_id=user.user_id, text=text,
                                 reply_markup=poll_keyboard)
    msg_id = msg["message_id"]
    return msg_id


@dp.callback_query_handler(lambda c: True if 'top_10' in c.data else False)
@delete_last_message
async def top_10(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user['id']
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    recipes = session.query(Recipe).order_by(Recipe.views.desc()).limit(10).all()
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    poll_keyboard.add(types.InlineKeyboardButton(text="На главную ⬆", callback_data=f'main'))
    msg = await bot.send_message(chat_id=user_id, text="Top 10",
                                 reply_markup=poll_keyboard)
    return msg["message_id"]


@dp.callback_query_handler(lambda c: True if 'right' in c.data or 'left' in c.data else False)
@delete_last_message
async def catalog_move(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user['id'])
    count_recipes = session.query(Recipe).count()
    offset = int(user.last_state)
    if 'right' in callback_query.data:
        user.last_state = offset + LIMIT
    elif 'left' in callback_query.data:
        user.last_state = offset - LIMIT
    session.commit()
    offset = int(user.last_state)
    text = f"Каталог\nстраница {int(offset / LIMIT)}"
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    recipes = session.query(Recipe).order_by(Recipe.id).offset(offset).limit(LIMIT)
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    if offset < (count_recipes - LIMIT):
        poll_keyboard.add(types.InlineKeyboardButton(text="Вперед ▶", callback_data=f'right'))
    if offset >= LIMIT:
        poll_keyboard.add(types.InlineKeyboardButton(text="Назад ◀", callback_data=f'left'))
    poll_keyboard.add(types.InlineKeyboardButton(text="На главную ⬆", callback_data=f'main'))
    msg = await bot.send_message(chat_id=user.user_id, text=text,
                                 reply_markup=poll_keyboard)
    return msg["message_id"]


@dp.callback_query_handler(lambda c: True if "r_" in c.data else False)
@delete_last_message
async def recipe(callback_query: types.CallbackQuery):
    msg_id = str()
    recipe_id = callback_query.data[2:]
    user = get_user(callback_query.from_user['id'])
    recipe = session.query(Recipe).get(recipe_id)
    caption = f"<b>{recipe.name}</b>"
    if recipe.description:
        caption += f'\n{recipe.description}'
    images = recipe.images
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    poll_keyboard.add(types.InlineKeyboardButton(text="Назад ◀", callback_data=f'/catalog'))
    for image in images:
        img = os.path.join(IMAGE_PATH, image.image)
        if images.index(image) == (len(images) - 1):
            msg = await send_image(user.user_id, img, image.photo_id, caption, poll_keyboard)
        else:
            msg = await send_image(user.user_id, img, image.photo_id)
        msg_id += str(msg['message_id']) + ","
        image.photo_id = msg["photo"][-1]["file_id"]
    # views = int(recipe.views)
    recipe.views += 1
    session.commit()
    return msg_id


@dp.message_handler(lambda message: search(message.text))
@delete_last_message
async def search_result(message: types.Message):
    user_id = message['from']['id']
    reg_exp = "%{}%".format(message.text)
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    recipes = session.query(Recipe) \
        .filter(or_(Recipe.name.like(reg_exp))).all()
    for recipe in recipes:
        poll_keyboard.add(types.InlineKeyboardButton(text=recipe.name, callback_data=f'r_{recipe.id}'))
    poll_keyboard.add(types.InlineKeyboardButton(text="На главную ⬆", callback_data=f'main'))
    msg = await bot.send_message(chat_id=user_id, text=f"Результат поиска по: <b>{message.text}</b>",
                                 reply_markup=poll_keyboard, parse_mode="HTML")
    return msg["message_id"]


@dp.message_handler()
@delete_last_message
async def search_result(message: types.Message):
    user_id = message['from']['id']
    poll_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    poll_keyboard.add(types.InlineKeyboardButton(text="На главную ⬆", callback_data=f'main'))
    answer = f'По запросу <b>"{message.text}"</b> ничего не найдено'
    msg = await bot.send_message(chat_id=user_id, text=answer,
                                 reply_markup=poll_keyboard, parse_mode="HTML")
    return msg["message_id"]


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


async def send_image(user_id, img=None, image_id=None, caption=None, keyboard=None):
    if image_id:
        if caption:
            msg = await bot.send_photo(chat_id=user_id, photo=image_id, caption=caption,
                             reply_markup=keyboard, protect_content=True, parse_mode="HTML")
        else:
            msg = await bot.send_photo(chat_id=user_id, photo=image_id, protect_content=True)
    else:
        if caption:
            msg = await bot.send_photo(chat_id=user_id, photo=open(img, 'rb'), caption=caption,
                                       reply_markup=keyboard, protect_content=True, parse_mode="HTML")
        else:
            msg = await bot.send_photo(chat_id=user_id, photo=open(img, 'rb'), protect_content=True)
    return msg


def search(message):
    reg_exp = "%{}%".format(message)
    search_result = session.query(Recipe) \
        .filter(or_(Recipe.name.like(reg_exp))).all()
    if len(search_result) > 0:
        return True
    return False


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

