import json
from typing import Tuple
import time

import requests
import re
from common import AccessKey
from .basechat import Chater

class WenyanKey(AccessKey):
    def __init__(self) -> None:
        super().__init__(60 * 60 * 24 * 20)
    
    def newkey(self) -> Tuple[str, float]:
        r = requests.post(f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}", 
            headers={
                "Content-Type": "application/json",
        }).json()
        if "error" in r:
            print(r)
            return "", 0.0
        return r["access_token"], time.time()

class Wenyanyixin(Chater):
    def __init__(self, model: str, mname: str, desc: str) -> None:
        super().__init__(model, mname, desc=desc)
        self.access_key = WenyanKey()
    
    def config(self, conf):
        self.access_key.api_key = conf["api_key"]
        self.access_key.secret_key = conf["secret_key"]
        self.access_key.reset()
    
    async def chat(self, userid, user_text, message_id, appid):
        c = self.check_command(userid, user_text)
        if c is not None:
            return c
        user = self.get_userdata(userid)
        if user.pending:
            return "别着急~等我说完再说吧~"
        user.pending = True
        if not user.chat_mode:
            user.history.clear()

        if len(user.history) > 0 and user.history[-1]["role"] == "user":
            pass
        else:
            newconv = self.create_user_message(user_text)
            user.history.append(newconv)
            user.history = user.history[-19:]
            if len(user.history) % 2 == 0:
                user.history.append(self.create_assistant_message("我在听。"))
        res = ""
        if self.current_model == "WENXIN4":
            res = self.ERNIE_Bot4(userid)
        else:
            res = self.ERNIE_Bot_turbo(userid)
        user.pending = False
        return res
    
    def summary(self, userid):
        return super().summary()


    def ERNIE_Bot4(self, userid):
        body = {
            "messages": self.get_userdata(userid).history,
        }
        system = self.system_message(userid)
        if system != "":
            body["system"] = system
        r = requests.post(f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={self.access_key.key()}", 
            json=body,
            headers={
                "Content-Type": "application/json",
        }).json()

        if "result" in r:
            result = r["result"]
            self.get_userdata(userid).history.append(self.create_assistant_message(result))
            return result
        if "error_code" in r:
            result = {}
            result["error_func"] = "ERNIE_Bot4"
            result["error"] = r
            print(r)
            if r == 18:
                return "[当前过于繁忙，请稍后输入#重试]"
            return json.dumps(result, ensure_ascii=False)
        
    def ERNIE_Bot_turbo(self, userid):
        body = {
            "messages": self.get_userdata(userid).history,
        }
        system = self.system_message(userid)
        if system != "":
            body["system"] = system
            
        r = requests.post(f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token={self.access_key.key()}", 
            json=body,
            headers={
                "Content-Type": "application/json",
        }).json()
        
        if "error_code" in r:
            result = {}
            result["error_func"] = "ERNIE_Bot_turbo"
            result["error"] = r
            print(body)
            self.get_userdata(userid).history.clear()
            return json.dumps(result, ensure_ascii=False)
        
        result = r["result"]
        self.get_userdata(userid).history.append(self.create_assistant_message(result))
        return result
        

        

