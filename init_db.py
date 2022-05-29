from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Date, Boolean, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
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

    def __init__(self, image):
        self.image = image


Base.metadata.create_all(engine)
