

import system_messages
from redisserver import redis_conn


class UserData:
    def __init__(self, userid, model) -> None:
        self.uid = userid
        self.model = model
        self.history = []
        self._chat_mode = True
        self._system = "助手"
        self.redis_key = "chat-feishu-userdata:" + userid + ":" + model
        self.pending = False
        self.last_task = None
        self.remain_message = []
    
    @property
    def chat_mode(self):
        return redis_conn.get(self.redis_key+":chat_mode") == "true"

    @chat_mode.setter
    def chat_mode(self, value: bool):
        redis_conn.set(self.redis_key+":chat_mode", "true" if value else "false")

    @property
    def system(self):
        sys = redis_conn.get(self.redis_key+":system") or "助手"
        if sys in system_messages.system_messages:
            return sys
        return "助手"
    
    @system.setter
    def system(self, value: str):
        redis_conn.set(self.redis_key+":system", value)