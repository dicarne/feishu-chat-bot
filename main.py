# http://127.0.0.1:32212
from fastapi import FastAPI
import json
import asyncio
from common import *

from models.wenyanyixin import Wenyanyixin
from models.gpt import ChatGPT
from models.glm import GLM4

import toml


models = {
    "gpt": ChatGPT(),
    "glm": GLM4(),
    "wenxin4": Wenyanyixin("WENXIN4", "文心一言4", "百度开发的大模型，能力较强。"),
    "wenxin3": Wenyanyixin("WENXIN3", "文心一言3", "上版本的百度开发的大模型，能力较弱但便宜。")
}
app = FastAPI()
distin = {}

conf = toml.load("config.toml")
if "models" in conf:
    ms = conf["models"]
    ks = list(models.keys())
    for k in ks:
        if k not in ms:
            models.pop(k)
if "openai" in conf:
    models["gpt"].config(conf["openai"])
else:
    models.pop("gpt")

if "baidu" in conf:
    models["wenxin4"].config(conf["baidu"])
    models["wenxin3"].config(conf["baidu"])
else:
    models.pop("wenxin4")
    models.pop("wenxin3")

if "glm" in conf:
    models["glm"].config(conf["glm"])
else:
    models.pop("glm")

feishu = conf["feishu"]
for k in feishu:
    it = feishu[k]
    config._tenant_access_token[it["app_id"]] = FeishuTenantKey(it["app_id"], it["app_secret"])


init_chatapp(models)

    

@app.post("/chatbot/")
async def post_by_feishu(data: dict):
    if "challenge" in data:
        return {
            "challenge": data["challenge"]
        }
    if "header" in data:
        event_type = data["header"]["event_type"]
        if event_type == "im.message.receive_v1":
            return handle_bot_chat(data)
        elif event_type == "application.bot.menu_v6":
            return handle_menu(data)
        print("unknown event")
        print(data)
        return {
            "code": 0,
            "message": "success"
        }
    if "action" in data:
        action = data["action"]
        value = action["value"]
        app_id = data["app_id"]
        if "tag" in action:
            if action["tag"] == "button":
                if "btn_change_persona" in value:
                    persona = value["btn_change_persona"]
                    oid = data["open_id"]
                    talk(app_id, oid, chatapp(oid).change_persona(oid, persona))
                if "switch_model" in value:
                    model_name = value["switch_model"]
                    oid = data["open_id"]
                    set_chatapp(oid, model_name)
                    talk(app_id, oid, "已切换模型：" + chatapp(oid).model_name)
    return {
        "code": 0,
        "msg": "success"
    }

def handle_bot_chat(data):
    event = data["event"]
    oid = event["sender"]["sender_id"]["open_id"]
    app_id = data["header"]["app_id"]
    message = event["message"]
    mid = message["message_id"]
    if(mid in distin):
        return {
            "code": 0,
            "message": "success"
        }
    distin[mid] = True
    messageobj = json.loads(message["content"])

    content = ""
    if "text" in messageobj:
        content = messageobj["text"]
    elif "content" in messageobj:
        for line in messageobj["content"]:
            for it in line:
                if it["tag"] == "text":
                    content += it["text"]
                elif it["tag"] == "a":
                    content += f"({it['text']})[{it['href']}]"
            content += "\n"

    asyncio.ensure_future(gpt(app_id, oid, content, mid))

    return {
        "code": 0,
        "msg": "success"
    }

def handle_menu(data):
    menukey = data["event"]["event_key"]
    oid = data["event"]["operator"]["operator_id"]["open_id"]
    appid = data["header"]["app_id"]
    if menukey == "reset_context":
        talk(appid, oid, chatapp(oid).menu_clear_history(oid))
    elif menukey == "mode_chat":
        talk(appid, oid, chatapp(oid).menu_mode_chat(oid))
    elif menukey == "mode_qa":
        talk(appid, oid, chatapp(oid).menu_mode_qa(oid))
    elif menukey == "request_switch_model":
        send_models_card(appid, oid)
    elif menukey == "change_persona":
        send_persona_card(appid, oid)
    elif menukey == "menu_show_detail":
        send_detail_card(appid, oid)
    return {
        "code": 0,
        "message": "success"
    }
