
from http import HTTPStatus
import time

from common import modify, reply, talk
from .basechat import Chater
import dashscope


class QwenGPT(Chater):
    def __init__(self, model, mname, desc, model_name) -> None:
        super().__init__(model, mname, desc)
        self.model_key = model_name
        self.api_key = ""

    def config(self, m):
        self.api_key = m["api_key"]
            
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
        user.history = user.history[-9:]
        
        res = await self.GPT(userid, appid, mid)
        user.pending = False
        modify(appid, mid, res)

        if len(user.remain_message) != 0:
            a = user.remain_message.pop(0)
            await self.chat(userid, a, "", appid)
    
    def summary(self, userid):
        return super().summary()

    async def GPT(self, userid, appid, messageid):
        result = ""

        try:
            message = [self.create_system_message(self.system_message(userid))]
            for it in self.get_userdata(userid).history:
                message.append(it)
            response = dashscope.Generation.call(
                dashscope.Generation.Models.qwen_turbo,
                messages=message,
                result_format='message',  # set the result to be "message" format.
                api_key=self.api_key,
                stream=True
            )

            t = time.time()
            curt = 0
            tick = 15
            for resp in response:
                chunk = resp.output
                if len(chunk.choices) != 0 and chunk.choices[0].message.content is not None:
                    result = chunk.choices[0].message.content
                    if curt < tick and time.time() - t > 2:
                        t = time.time()
                        modify(appid, messageid, result + "\n(编辑中)")
                        curt += 1
            # if response.status_code == HTTPStatus.OK:
            #     result = response.output.choices[0].message.content
            #     self.get_userdata(userid).history.append(self.create_assistant_message(result ))
            # else:
            #     result = ('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            #         response.request_id, response.status_code,
            #         response.code, response.message
            #     ))

            
            return result
        except Exception as e:
            print(e)
            return result + "\n\n【未知错误！】"
