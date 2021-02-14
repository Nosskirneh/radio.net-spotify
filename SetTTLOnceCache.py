from cachetools import TTLCache
from cachetools import Cache


class SetTTLOnceCache(TTLCache):
    def __setitem__(self, key, value, cache_setitem=Cache.__setitem__):
        if key in self:
            cache_setitem(self, key, value)
        else:
            super(SetTTLOnceCache, self).__setitem__(key, value)
