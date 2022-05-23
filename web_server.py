import os
import json
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
        recipes = session.query(Recipe).order_by(Recipe.id)
        self.render("main.html", title="Каталог", name="Список рецептов", recipes=recipes)


class AddRecipeHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("add_recipe.html", title="Add recipe")

    def post(self):
        name = self.get_argument("name")
        date = self.get_argument("date") if self.get_argument("date") else None
        images = self.request.files
        recipe = Recipe(name, date)
        session.add(recipe)
        i = 0
        for image in images:
            i += 1
            name = str(recipe.id) + str(i)
            # with open name:
            #     name.write(image['body'])
        self.render("add_recipe.html", title="Success")

def make_app():

    return tornado.web.Application([
        url(r"/", MainHandler, name="main"),
        url(r"/add_recipe/", AddRecipeHandler, name="add_recipe"),
    ],
        template_path=os.path.join(BASE_DIR, 'templates'),
        static_path=os.path.join(BASE_DIR, 'static'),
    )

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()