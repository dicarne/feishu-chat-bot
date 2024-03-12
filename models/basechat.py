
import json
from userdata import UserData
import system_messages


class Chater:
    def __init__(self, model: str, mname: str, desc: str = "") -> None:
        self.userdata = {}
        self.plugins = {}
        self.funcs = {}
        self.current_model = model
        self.model_name = mname
        self.desc = desc
        self.model_id = ""
    
    def config(self, conf):
        pass
    
    async def chat(userid, user_text, message_id, appid):
        return ""
    
    def summary(userid):
        pass



    def create_user_message(self, text: str):
        return {
            "role": "user",
            "content": text
        }

    def create_system_message(self, text: str):
        return {
            "role": "system",
            "content": text
        }

    def create_assistant_message(self, text: str):
        return {
            "role": "assistant",
            "content": text
        }
    def create_assistant_func_message(self, funccall):
        return {
            "role": "assistant",
            "function_call": funccall
        }


    def create_function_message(self, fname, result):
        return {
            "role": "function",
            "name": fname,
            "content": json.dumps(result, ensure_ascii=False)
        }
    
    def get_userdata(self, uid: str) -> UserData:
        if uid not in self.userdata:
            self.userdata[uid] = UserData(uid, self.current_model)
        return self.userdata[uid]

    def menu_clear_history(self, userid: str) -> bool:
        self.get_userdata(userid).history = []
        self.get_userdata(userid).pending = False
        self.get_userdata(userid).remain_message = []
        return "重置上下文成功"
    
    def menu_mode_chat(self, userid: str) -> bool:
        self.get_userdata(userid).chat_mode = True
        return "切换为对话模式"
    
    def menu_mode_qa(self, userid: str) -> bool:
        self.get_userdata(userid).chat_mode = False
        return "切换为提问模式"

    def change_persona(self, userid: str, sysname: str) -> bool:
        if sysname in system_messages.system_messages:
            self.get_userdata(userid).system = sysname
            return "切换为：" + sysname
        return "切换失败，该人格不存在！"
    
    def check_command(self, userid: str, text: str) -> bool:
        u = self.get_userdata(userid)
        return None

    def system_message(self, userid: str):
        text = ""
        s = self.get_userdata(userid).system
        if s in system_messages.system_messages:
            return system_messages.system_messages[s]
        return text
    
    def show_detail(self, oid):
        u = self.get_userdata(oid)
        return {
            "system": u.system,
            "model": self.model_name,
            "history_count": len(u.history),
            "mode": "对话" if u.chat_mode else "问答",
        }
