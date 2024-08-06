

import system_messages
from redisserver import redis_conn
import json

class ObservableList(list):
    def __init__(self, redis_key, *args):
        super().__init__(*args)
        self.redis_key = redis_key

    def append(self, item):
        # print(f"Adding item: {item}")
        super().append(item)
        self.on_change()

    def remove(self, item):
        # print(f"Removing item: {item}")
        super().remove(item)
        self.on_change()

    def on_change(self):
        # 这里执行你希望在数组变化时进行的操作
        redis_conn.set(self.redis_key+":history", json.dumps(self, ensure_ascii=False))

    def extend(self, iterable):
        # print(f"Extending list with: {iterable}")
        super().extend(iterable)
        self.on_change()

    def insert(self, index, item):
        # print(f"Inserting item: {item} at index: {index}")
        super().insert(index, item)
        self.on_change()

    def pop(self, index=-1):
        item = super().pop(index)
        # print(f"Popped item: {item}")
        self.on_change()
        return item

    def clear(self):
        # print("Clearing list")
        super().clear()
        self.on_change()

    def __setitem__(self, key, value):
        # print(f"Setting item at index {key} to {value}")
        super().__setitem__(key, value)
        self.on_change()

    def __delitem__(self, key):
        # print(f"Deleting item at index {key}")
        super().__delitem__(key)
        self.on_change()

class UserData:
    def __init__(self, userid, model) -> None:
        self.uid = userid
        self.model = model
        self._history = None
        self._chat_mode = True
        self._system = "助手"
        self.redis_key = "chat-feishu-userdata:" + userid + ":" + model
        self.gredis_key = "chat-feishu-userdata:" + userid
        self.pending = False
        self.last_task = None
        self.remain_message = []
    
    @property
    def history(self) -> ObservableList:
        if self._history is None:
            # 从数据库中读取
            reco = redis_conn.get(self.redis_key+":history")
            if reco == "" or reco is None:
                self._history = ObservableList(self.redis_key+":history", [])
            else:
                try:
                    self._history = ObservableList(self.redis_key+":history", json.loads(reco))
                except Exception as e:
                    self._history = ObservableList(self.redis_key+":history", [])
        return self._history
    

    @history.setter
    def history(self, value: list):
        self._history = ObservableList(self.redis_key+":history", value)
        redis_conn.set(self.redis_key+":history", json.dumps(value, ensure_ascii=False))
    
    @property
    def chat_mode(self):
        return redis_conn.get(self.gredis_key+":chat_mode") == "true"

    @chat_mode.setter
    def chat_mode(self, value: bool):
        redis_conn.set(self.gredis_key+":chat_mode", "true" if value else "false")

    @property
    def system(self):
        sys = redis_conn.get(self.gredis_key+":system") or "助手"
        if sys in system_messages.system_messages:
            return sys
        return "助手"
    
    @system.setter
    def system(self, value: str):
        redis_conn.set(self.gredis_key+":system", value)