from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy import Column, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import datetime

from config import sqlitedb, t_format


Base = declarative_base()
engine = create_engine(sqlitedb)


class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    private = Column(Boolean)
    usernode = Column(Boolean)
    name = Column(String)
    parent = Column(Integer)

    views = Column(Integer, nullable=True)
    children = Column(Integer, nullable=True)
    descendants = Column(Integer, nullable=True)
    k = Column(Integer, nullable=True)
    bookmarked = Column(Integer, nullable=True)
    content = Column(String, nullable=True)

    def __init__(self, data):
        self.id = data['id']
        if isinstance(data['created'], basestring):
            self.created = datetime.datetime.strptime(data['created'], t_format)
        else:
            self.created = data['created']
        self.owner_id = data['owner']['id']
        self.private = True if data['content'] is None else False
        self.usernode = True if data['id'] == data['owner']['id'] else False
        self.name = data['name']
        self.parent = data['parent']

        self.content = data['content']
        self.views = data['views']
        self.children = data['children']
        self.descendants = 0 if data['descendants'] == '' else data['descendants']
        self.k = data['k']
        self.bookmarked = data['bookmarked']


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)


class Log(Base):
    __tablename__ = 'logs'
    node_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    error = Column(String)
    data = Column(String)
