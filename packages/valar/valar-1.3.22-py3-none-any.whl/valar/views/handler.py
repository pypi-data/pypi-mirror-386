import traceback

from ..channels.counter import Counter
from ..channels.sender import ValarChannelSender
from ..dao import Dao
from ..dao.engine import ValarEngine

import time


def valar_test_handler(sender: ValarChannelSender):
    data = sender.data
    length = data.get('length', 100)
    counter = Counter(length)
    for i in range(length):
        time.sleep(0.1)
        tick = counter.tick()
        tick.update({'name': 'test1'})
        sender.load(tick)
    return "aba"


def batch_handler(sender: ValarChannelSender):
    data = sender.data
    entity, db, method = data.get("entity"), data.get("db"), data.get("method")
    dao = Dao(entity, db)
    if method == 'save_many':
        array = data.get("data", [])
        counter = Counter(array)
        keys = []
        for item in array:
            item.update({'saved': True})
            bean = dao.save_one(item)
            keys.append(bean.id)
            payload = counter.tick()
            sender.load(payload)
        return keys
    elif method == 'delete_many':
        conditions = data.get("data", [])
        paths = dao.delete(conditions)
        counter = Counter(len(paths))
        minio = ValarEngine().get_minio_bucket(entity)
        for path in paths:
            minio.remove(path)
            payload = counter.tick()
            sender.load(payload)
    return []
