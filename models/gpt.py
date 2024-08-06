
import time

import httpx

from common import modify, reply, talk
from .basechat import Chater
from openai import NOT_GIVEN, AsyncOpenAI, NotFoundError, RateLimitError, OpenAI
import asyncio

class ChatGPT(Chater):
    def __init__(self, model, mname, desc, model_name) -> None:
        super().__init__(model, mname, desc)
        self.model_key = model_name
        self.model: AsyncOpenAI = None
        self.gptmodel = ""

    def config(self, m):
        
        BASE_URL = None
        API_KEY = None
        PROXY = None
        if self.model_key in m:
            self.gptmodel = m[self.model_key]
        if "api_key" in m:
            API_KEY = m["api_key"]
        if "proxy" in m:
            PROXY = m["proxy"]
        if "api_base" in m:
            BASE_URL = m["api_base"]
        self.model = AsyncOpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
        )

        
        # http_client=httpx.AsyncClient(
        #     proxies=PROXY,
        #     transport=httpx.AsyncHTTPTransport(local_address="0.0.0.0"),
        # ),
            
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

    async def GPT4(self, userid, appid, messageid, retry=0):
        if retry > 20:
            return "重试错误已达最大值"
        result = ""
        try:
            message = [self.create_system_message(self.system_message(userid))]
            for it in self.get_userdata(userid).history:
                message.append(it)
                
            stream = await self.model.chat.completions.create(
                model=self.gptmodel,
                messages=message,
                stream=True
            )
            
            t = time.time()
            curt = 0
            tick = 15
            async for chunk in stream:
                # print(chunk.choices)
                if chunk.choices[0].delta.content is not None:
                    result += chunk.choices[0].delta.content
                    if curt < tick and time.time() - t > 5:
                        t = time.time()
                        modify(appid, messageid, result + "\n(编辑中)")
                        curt += 1
            self.get_userdata(userid).history.append(self.create_assistant_message(result ))
            return result
        except RateLimitError as e:
            return "对话频率达到限制！休息会吧！"
        # except NotFoundError as e:
        #     await asyncio.sleep(5)
        #     return self.GPT4(self, userid, appid, messageid, retry=retry+1)
        except Exception as e:
            await asyncio.sleep(5)
            print("错误，重试：" + str(retry))
            print(e)
            # raise e
            return await self.GPT4(userid, appid, messageid, retry=retry+1)
            # print(e)
            # return result + "\n\n【未知错误！】"
