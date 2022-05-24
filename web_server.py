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
        request_date = self.get_argument("date") if self.get_argument("date") else None
        date = None
        if request_date:
            rough_date = request_date.split("-")
            date = datetime.datetime(int(rough_date[0]), int(rough_date[1]), int(rough_date[2]))
        images = self.request.files
        recipe = Recipe(name, date, description)
        session.add(recipe)
        session.commit()
        path = os.path.join(BASE_DIR, 'static', 'recipe_img')
        i = 0
        for image in images:
            img = images[image][0]
            i += 1
            extension = img["filename"].split(".")[-1]
            name = str(recipe.id) + "-" + str(i) + "." + extension
            filename = os.path.join(path, name)
            with open(filename, "wb") as f:
                f.write(img['body'])
            img_obj = Image(name)
            recipe.images.append(img_obj)
        session.commit()
        self.redirect(f"/success_add/{recipe.name}")


class SuccessAddRecipeHandler(tornado.web.RequestHandler):
    def get(self, name=None):
        self.render("success_add.html", title="Успешное добавление", name=name)


class RecipeHandler(tornado.web.RequestHandler):
    def get(self, recipe_id):
        recipe = session.query(Recipe).get(recipe_id)
        self.render("recipe.html", title=recipe.name, recipe=recipe)

    def post(self, recipe_id):
        name = self.get_argument("name")
        a = self.get_argument("image-id")
        recipe = session.query(Recipe).get(recipe_id)
        self.render("recipe.html", title="asdasdas", recipe=recipe)


class DeleteImageHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            image_id = self.get_argument("image_id")
            recipe_id = self.get_argument("recipe_id")
            recipe = session.query(Recipe).get(recipe_id)
            image = session.query(Image).get(image_id)
            recipe.images.remove(image)
            return
        except:
            return


def make_app():

    return tornado.web.Application([
        url(r"/", MainHandler, name="main"),
        url(r"/add_recipe/", AddRecipeHandler, name="add_recipe"),
        url(r"/success_add/(.*)", SuccessAddRecipeHandler, name="Success"),
        url(r"/recipe/(.*)", RecipeHandler, name="recipe"),
        url(r"/delete_img/", DeleteImageHandler, name="delete_img")
    ],
        template_path=os.path.join(BASE_DIR, 'templates'),
        static_path=os.path.join(BASE_DIR, 'static'),
    )

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()