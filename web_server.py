import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from common import BASE
from init_db import Recipe

engine = create_engine(f'sqlite:///{BASE}', echo=True)
conn = engine.connect()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        s = select(Recipe).order_by(Recipe.id)
        recipes = conn.execute(s)
        self.render("templates/main.html", title="My title", name="Список рецептов", recipes=recipes)


class AddRecipeHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("templates/add_recipe.html", title="Add recipe")

    def post(self):
        print(self.request.body)
        self.render("templates/add_recipe.html", title="Succes")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/add_recipe", AddRecipeHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()