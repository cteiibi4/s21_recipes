from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Date, Boolean, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import ARRAY
from common import BASE

engine = create_engine(f'sqlite:///{BASE}', echo=True)

Base = declarative_base()


class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column('id', Integer, primary_key=True, unique=True)
    name = Column('name', String)
    date = Column('date', Date)
    images = relationship('Image', back_populates='recipe')
    hidden = Column('hidden', Boolean, default=False)
    description = Column('description', String)
    views = Column('views', Integer, default=0)
    media_group_id = Column('media_group_id', String, default=None)

    def __init__(self, name, date, description=None):
        self.name = name
        self.date = date
        self.description = description


class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    image = Column(String)
    recipe = relationship('Recipe', back_populates='images')
    recipe_id = Column(String, ForeignKey('recipes.id'))
    photo_id = Column(String, unique=True, nullable=True, default=None)

    def __init__(self, image):
        self.image = image


class User(Base):
    __tablename__ = 'user'
    user_id = Column(String, primary_key=True, unique=True)
    last_message = Column(String)
    last_state = Column(Integer, default=0)

    def __init__(self, client_id):
        self.user_id = client_id


Base.metadata.create_all(engine)
