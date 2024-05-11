from typing import Tuple
import requests
import json
import time

from models.basechat import Chater
import system_messages
from redisserver import redis_conn

class AccessKey:
    def __init__(self, timeout) -> None:
        self._key = ""
        self.timeout = timeout
        self.create_time = 0
    
    def reset(self):
        self.create_time = 0
    
    def newkey(self) -> Tuple[str, float]:
        return "", 0.0
    
    def key(self) -> str:
        if self._key == "" or time.time() - self.create_time > self.timeout:
            self._key, self.create_time = self.newkey()
        return self._key

class FeishuTenantKey(AccessKey):
    def __init__(self, appid, appsec) -> None:
        super().__init__(1 * 60 * 60)
        self.app_id = appid
        self.appsec = appsec
    
    def newkey(self) -> Tuple[str, float]:
        r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", data={
            "app_id": self.app_id,
            "app_secret": self.appsec
        })
        resp = r.json()
        return resp["tenant_access_token"], time.time()

class Config:
    def __init__(self) -> None:
        self._tenant_access_token = {}
    
    def tenant_access_token(self, appid: str):
        return self._tenant_access_token[appid]

config = Config()


models = None

def init_chatapp(mos):
    global models
    models = mos
    for k in models:
        models[k].model_id = k

def set_chatapp(oid, newm: str):
    redis_conn.set("chat-feishu-usermodel:"+oid, newm)

def chatapp(oid: str) -> Chater:
    m = redis_conn.get("chat-feishu-usermodel:"+oid)
    if m is None or not m in models:
        m = "qwen_turbo"
        set_chatapp(oid, m)
    return models[m]

async def gpt(appid, oid, content, message_id):
    ct = await chatapp(oid).chat(oid ,content, message_id, appid)
    if ct is not None:
        r = requests.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id", data={
            "content": json.dumps({ "text":  ct}, ensure_ascii=False),
            "receive_id": oid,
            "msg_type": "text",
        }, headers={
            "Authorization": f"Bearer { config.tenant_access_token(appid).key() }",
        })

def talk(appid, oid, content):
    r = requests.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id", data={
        "content": json.dumps({ "text": content }, ensure_ascii=False),
        "receive_id": oid,
        "msg_type": "text",
    }, headers={
        "Authorization": f"Bearer { config.tenant_access_token(appid).key() }",
    })
    j = r.json()
    return j["data"]["message_id"]

def reply(appid, message_id, content):
    r = requests.post(f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply", data={
        "content": json.dumps({ "text": content }, ensure_ascii=False),
        "msg_type": "text",
    }, headers={
        "Authorization": f"Bearer { config.tenant_access_token(appid).key() }",
    })

def modify(appid, message_id, content):
    r = requests.put(f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}", data={
        "content": json.dumps({ "text": content }, ensure_ascii=False),
        "msg_type": "text",
    }, headers={
        "Authorization": f"Bearer { config.tenant_access_token(appid).key() }",
    })

def card(appid, oid, content):
    r = requests.post(f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id", data={
        "content": json.dumps(content, ensure_ascii=False),
        "receive_id": oid,
        "msg_type": "interactive",
    }, headers={
        "Authorization": f"Bearer { config.tenant_access_token(appid).key() }",
    })

def send_persona_card(appid, oid):
    content = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "markdown",
                "content": "下面是可以选择的人格，改变人格会改变机器人的对话方式。"
            },
            {
                "tag": "markdown",
                "content": "当前人格：**" + chatapp(oid).get_userdata(oid).system + "**"
            },
            {
                "tag": "hr"
            },
        ],
        "header": {
            "template": "blue",
            "title": {
                "content": "选择人格",
                "tag": "plain_text"
            }
        }
    }
    def add_persona(pname, desc):
        content["elements"].append( {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**" + pname + "**：" + desc 
                },
                "extra": {
                    "tag": "button",
                    "text": {
                        "tag": "lark_md",
                        "content": "切换"
                    },
                    "type": "default",
                    "value": {
                        "btn_change_persona": pname
                    }
                }
            })
    for k in system_messages.system_messages:
        add_persona(k, system_messages.system_messages[k])
    card(appid, oid, content)


def send_models_card(appid, oid):
    content = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "markdown",
                "content": "下面是可以选择的模型，不同的模型能力有所不同。"
            },
            {
                "tag": "markdown",
                "content": "当前模型：**" + chatapp(oid).model_name + "**"
            },
            {
                "tag": "hr"
            },
        ],
        "header": {
            "template": "blue",
            "title": {
                "content": "选择模型",
                "tag": "plain_text"
            }
        }
    }
    def add_model(m: Chater):
        content["elements"].append( {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**" + m.model_name + "**：" + m.desc
                },
                "extra": {
                    "tag": "button",
                    "text": {
                        "tag": "lark_md",
                        "content": "切换"
                    },
                    "type": "default",
                    "value": {
                        "switch_model": m.model_id
                    }
                }
            })
    for m in models:
        add_model(models[m])
    card(appid, oid, content)

def send_detail_card(appid, oid):
    detail = chatapp(oid).show_detail(oid)
    content = {
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": "下面是当前机器人状态，是否符合你的需求呢？",
                    "tag": "plain_text"
                }
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "😎**当前人格**"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": detail["system"]
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "💭**语言模型**"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": detail["model"]
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "🧠**对话模式**"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": detail["mode"]
                        }
                    }
                ]
            }
        ],
        "header": {
            "template": "yellow",
            "title": {
                "content": "机器人简报",
                "tag": "plain_text"
            }
        }
    }

    card(appid, oid, content)