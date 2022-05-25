import os
import json
import datetime
import tornado.ioloop
import tornado.web
import tornado.httputil
import tornado.escape
from tornado.web import url
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from common import BASE
from init_db import Recipe, Image

BASE_DIR = os.path.dirname(__file__)
IMAGE_PATH = os.path.join(BASE_DIR, 'static', 'recipe_img')
engine = create_engine(f'sqlite:///{BASE}', echo=True)
conn = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        recipes = session.query(Recipe).order_by(Recipe.id).all()
        self.render("main.html", title="Каталог", name="Список рецептов", recipes=recipes)


class AddRecipeHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("add_recipe.html", title="Add recipe")

    def post(self):
        name = self.get_argument("name")
        description = self.get_argument("description") if self.get_argument("description") else None
        date = get_date(self.get_argument("date")) if self.get_argument("date") else None
        images = self.request.files
        recipe = Recipe(name, date, description)
        session.add(recipe)
        session.commit()
        i = 0
        for image in images:
            img = images[image][0]
            i += 1
            save_img(recipe, img, i)
        session.commit()
        self.redirect(f"/success_add/{recipe.name}")


class SuccessAddRecipeHandler(tornado.web.RequestHandler):
    def get(self, name=None):
        self.render("success_add.html", title="Успешное добавление", name=name)


class RecipeHandler(tornado.web.RequestHandler):
    def get(self, recipe_id):
        recipe = session.query(Recipe).get(recipe_id)
        self.render("recipe.html", title=recipe.name, recipe=recipe, success=False, error=False)

    def post(self, recipe_id):
        try:
            recipe = session.query(Recipe).get(recipe_id)
        except:
            self.redirect(f"/error/")
            return
        try:
            hidden = True if self.get_argument("hidden") == "True" else False
        except:
            hidden = False
        try:
            images = self.request.files
            recipe = session.query(Recipe).get(recipe_id)
            recipe.name = self.get_argument("name")
            recipe.date = get_date(self.get_argument("date")) if self.get_argument("date") else None
            recipe.description = self.get_argument("description") if self.get_argument("description") else None
            recipe.hidden = hidden
            i = recipe.images[-1].image.split(".")[0].split("-")[-1]
            for image in images:
                img = images[image][0]
                i += 1
                save_img(recipe, img, i)
            session.commit()
            self.render("recipe.html", title=recipe.name, recipe=recipe, success=True, error=False)
        except Exception as e:
            self.render("recipe.html", title=recipe.name, recipe=recipe, success=True, error=e)

class DeleteImageHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            image_id = self.get_argument("image_id")
            recipe_id = self.get_argument("recipe_id")
            recipe = session.query(Recipe).get(recipe_id)
            image = session.query(Image).get(image_id)
            img = os.path.join(IMAGE_PATH, image.image)
            os.remove(img)
            recipe.images.remove(image)
            session.commit()
            self.on_finish()
        except Exception as e:
            self.send_error(500, error=e)


class ErrorHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("error.html", title="Ошибка")



def make_app():

    return tornado.web.Application([
        url(r"/", MainHandler, name="main"),
        url(r"/add_recipe/", AddRecipeHandler, name="add_recipe"),
        url(r"/success_add/(.*)", SuccessAddRecipeHandler, name="Success"),
        url(r"/recipe/(.*)", RecipeHandler, name="recipe"),
        url(r"/delete_img/", DeleteImageHandler, name="delete_img"),
        url(r"/error/", ErrorHandler, name="error"),
    ],
        template_path=os.path.join(BASE_DIR, 'templates'),
        static_path=os.path.join(BASE_DIR, 'static'),
    )


def get_date(request_date):
    rough_date = request_date.split("-")
    date = datetime.datetime(int(rough_date[0]), int(rough_date[1]), int(rough_date[2]))
    return date


def save_img(recipe, image, number):
    extension = image["filename"].split(".")[-1]
    name = str(recipe.id) + "-" + str(number) + "." + extension
    filename = os.path.join(IMAGE_PATH, name)
    with open(filename, "wb") as f:
        f.write(image['body'])
    img_obj = Image(name)
    recipe.images.append(img_obj)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()