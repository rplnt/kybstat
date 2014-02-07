from sqlalchemy.orm import sessionmaker
from calendar import monthrange
import datetime
import sys

from db import *

from bottle import route, view, template


class Cache(object):

    def __init__(self):
        self.cache = dict()
        self.age = dict()

    def __contains__(self, key):
    	return key in self.cache

    def __getitem__(self, key):
        return self.cache[key]

    def __setitem__(self, key, value):
        self.cache[key] = value

    def __delitem__(self, key):
    	del self.cache[key]

    def __iter__(self):
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)

