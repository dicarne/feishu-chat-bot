
import time
import asyncio

from common import modify, reply, talk
from zhipuai import ZhipuAI
from .basechat import Chater

# 在此氪金：https://maas.aminer.cn/overview


class GLM4(Chater):
    def __init__(self) -> None:
        super().__init__("GLM4", "GLM4", desc="智谱开发的大模型，据说是最强中文模型。")
        self.client = None

    def config(self, conf):
        self.client = ZhipuAI(api_key=conf["api_key"])


    async def chat(self, userid, user_text, message_id, appid):
        c = self.check_command(userid, user_text)
        if c is not None:
            return c
        user = self.get_userdata(userid)

        if not user.chat_mode:
            user.history.clear()
            user.remain_message.clear()
            user.pending = False

        if user.pending:
            reply(appid, message_id, "别着急，等我说完哦~")
            user.remain_message.append(user_text)
            return
        user.pending = True
        mid = talk(appid, userid, "…… …… ……")
        

        newconv = self.create_user_message(user_text)
        user.history.append(newconv)
        user.history = user.history[-19:]
        await asyncio.to_thread(self.GLM4, userid=userid, appid=appid, messageid=mid)
        if len(user.remain_message) != 0:
            a = user.remain_message.pop(0)
            asyncio.ensure_future(self.chat(userid, a, "", appid))

    def GLM4(self, userid, appid, messageid):
        result = ""
        try:
            user = self.get_userdata(userid)
            message = [self.create_system_message(self.system_message(userid))]
            for it in user.history:
                message.append(it)
            stream = self.client.chat.completions.create(
                model="glm-4",
                messages=message,
                stream=True
            )
            
            t = time.time()
            curt = 0
            tick = 15
            for chunk in stream:
                result += chunk.choices[0].delta.content
                if curt < tick and time.time() - t > 1:
                    t = time.time()
                    modify(appid, messageid, result + "\n(编辑中)")
                    curt += 1
            self.get_userdata(userid).history.append(self.create_assistant_message(result ))
            user.pending = False
            modify(appid, messageid, result)
            
            return result #a["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(e)
            return result + "\n\n【未知错误！】"
