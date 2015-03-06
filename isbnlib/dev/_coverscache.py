# -*- coding: utf-8 -*-

"""Read and write cover cache.


    NOTE
    1. shelve has different incompatible formats in py2 and py3
    2. if some methods detect that the cache is not consistent
       they delete the cache and create a new one.
    3. After purge the cache keeps the records with more hits
       and the newests.
    4. The design is for safety not for performance! Increasing
       MAXLEN can have an high detrimental impact on performance.

    Examples:
    cc = CoversCache('.covers')
    cc.['gooc.9780000000000.2'] = (
        "http://books.google.com/books/content?id=uUcvgfTYTRnjh"\
        "&printsec=frontcover"\
        "&img=1&zoom=2&edge=curl&source=gbs_api",
        ".covers/slot01/9780000000000.jpg"
        )
    cc['gooc.9780000000000.2']
    cc.hits('gooc.9780000000000.2')
    cc.keys()
    cc.files()
    cc.sync()
    cc.make()
    cc.delete()
    del cc['gooc.9780000000000.2']

"""

import os
import shutil
from random import randint

from ._shelvecache import ShelveCache


class CoversCache(object):

    """Covers cache."""

    CACHEFOLDER = '.covers'
    INDEXFN = '.index'
    MAXLEN = 3000
    NSLOTS = 10

    def __init__(self, cachepath=CACHEFOLDER):
        """Initialize attributes."""
        self.cachepath = cachepath
        self._indexpath = os.path.join(cachepath, self.INDEXFN)
        if not os.path.isfile(self._indexpath):
            self.make()
        self._index = ShelveCache(self._indexpath)
        self._index.MAXLEN = self.MAXLEN
        if len(self._index) > self.MAXLEN:
            self.purge()

    def __getitem__(self, key):
        """Read cache."""
        try:
            return self._index[key]
        except:
            return None

    def __setitem__(self, key, value):
        """Write to cache."""
        url, pth = value
        try:
            if pth and os.path.isfile(pth):
                target = os.path.join(self._get_slot(), os.path.basename(pth))
                shutil.copyfile(pth, target)
            if os.path.isfile(target) and url:
                self._index[key] = (url, target)
                return True
            else:
                raise
        except:
            return False

    def __delitem__(self, key):
        """Delete record with key."""
        try:
            del self._index[key]
            return True
        except:
            return False

    def __len__(self):
        """Return the number of keys in cache."""
        return len(self._index.keys()) if self._index.keys() else 0

    def keys(self):
        """Return the number of keys in cache."""
        return self._index.keys()

    def hits(self, key):
        """Return the number of hits for key."""
        return self._index.hits(key)

    def _create_slots(self):
        for slot in range(self.NSLOTS):
            name = "slot%02d" % (slot,)
            pth = os.path.join(self.cachepath, name)
            if not os.path.exists(pth):
                os.mkdir(pth)

    def make(self):
        """Init the cache."""
        # 1. Delete if available
        if os.path.isdir(self.cachepath):
            self.delete()
        # 2. Make folder
        os.mkdir(self.cachepath)
        # 3. Create Index
        self._index = ShelveCache(self._indexpath)
        # 4. Create slots
        self._create_slots()

    def _get_slot(self):
        slot = "slot%02d" % (randint(0, 9),)
        return os.path.join(self.cachepath, slot)

    def files(self):
        pths = []
        for root, _, fls in os.walk(self.cachepath):
            for fn in fls:
                pths.append(os.path.join(root, fn))
        return pths

    def sync(self):
        """Sync index entries with disk files."""
        # clear index entries not on disk
        checked = [self._indexpath]
        for key in self._index.keys():
            url, pth = self._index[key]
            if not os.path.isfile(pth):
                self._index[key] = (url, None)
            checked.append(self._index[key][1])
        # delete files not on index
        print checked
        diff = tuple(set(self.files()) - set(checked))
        for fp in diff:
            os.remove(fp)

    def purge(self):
        try:
            self._index.purge()
            self.sync()
            return True
        except:
            return False

    def delete(self):
        self._index = None
        return shutil.rmtree(self.cachepath)
