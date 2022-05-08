import os
import tornado.ioloop
import tornado.web
from tornado.web import url
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from common import BASE
from init_db import Recipe

BASE_DIR = os.path.dirname(__file__)
engine = create_engine(f'sqlite:///{BASE}', echo=True)
conn = engine.connect()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        s = select(Recipe).order_by(Recipe.id)
        recipes = conn.execute(s)
        self.render("main.html", title="Каталог", name="Список рецептов", recipes=recipes)


class AddRecipeHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("add_recipe.html", title="Add recipe")

    def post(self):
        print(self.request.body)
        print(self.request)
        self.render("add_recipe.html", title="Succes")

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