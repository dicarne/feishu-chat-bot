
import time

from common import modify, reply, talk
from .basechat import Chater
from openai import NOT_GIVEN, AsyncOpenAI, OpenAI, RateLimitError



class MoonshotGPT(Chater):
    def __init__(self, model, mname, desc, model_name) -> None:
        super().__init__(model, mname, desc)
        self.model_key = model_name
        self.model: AsyncOpenAI = None
        self.gptmodel = ""

    def config(self, m):
        if self.model_key in m:
            self.gptmodel = m[self.model_key]
        self.model = AsyncOpenAI(
            api_key = m["api_key"],
            base_url = "https://api.moonshot.cn/v1"
        )
    
    async def gpt(self, messages, config):
        response_format = NOT_GIVEN
        if 'response_format' in config:
            response_format = config['response_format']
        result = await self.model.chat.completions.create(
                model=self.gptmodel,
                messages=messages,
                response_format=response_format,
        )
        return result.choices[0].message.content
            
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
        
        res = await self.GPT4(userid, appid, mid)
        user.pending = False
        modify(appid, mid, res)

        if len(user.remain_message) != 0:
            a = user.remain_message.pop(0)
            await self.chat(userid, a, "", appid)
    
    def summary(self, userid):
        return super().summary()

    async def GPT4(self, userid, appid, messageid):
        result = ""

        try:
            message = [self.create_system_message(self.system_message(userid))]
            for it in self.get_userdata(userid).history:
                message.append(it)
            stream = await self.model.chat.completions.create(
                model=self.gptmodel,
                messages=message,
                stream=True,
            )
            
            t = time.time()
            curt = 0
            tick = 15
            async for chunk in stream:
                if len(chunk.choices) != 0 and chunk.choices[0].delta.content is not None:
                    result += chunk.choices[0].delta.content
                    if curt < tick and time.time() - t > 2:
                        t = time.time()
                        modify(appid, messageid, result + "\n(编辑中)")
                        curt += 1
            self.get_userdata(userid).history.append(self.create_assistant_message(result ))
            return result
        except RateLimitError as e:
            return "对话频率达到限制！休息会吧！"
        except Exception as e:
            print(e)
            return result + "\n\n【未知错误！】"
