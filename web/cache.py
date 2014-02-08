from collections import defaultdict


class Cache(object):

    def __init__(self, limit=100):
        self.limit = limit
        self.cache = dict()
        self.age = defaultdict(int)

    def __contains__(self, key):
        return key in self.cache

    def __getitem__(self, key):
        self._update_age(key)
        return self.cache[key]

    def __setitem__(self, key, value):
        if len(self.cache.keys()) >= self.limit:
            self._delete_oldest()
        self.cache[key] = value

    def __delitem__(self, key):
        del self.cache[key]
        del self.age[key]

    def __iter__(self):
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)

    def __repr__(self):
        return str(self.cache)

    def __str__(self):
        return str(self.cache)

    def add(self, key, value, price=None):
        self.__setitem__(key, value)
        if price:
            self.age[key] = -price

    def _delete_oldest(self):
        oldest = max(self.age, key=self.age.get)
        self.__delitem__(oldest)

    def _update_age(self, key=None):
        for k in self.age.keys():
            if k != key:
                self.age[k] += 1
            else:
                self.age[k] = 0
