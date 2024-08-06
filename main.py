# http://127.0.0.1:32212
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from common import *

from models.deepseek import DeepSeekGPT
from models.qwen import QwenGPT
from models.wenyanyixin import Wenyanyixin
from models.gpt import ChatGPT
from models.glm import GLM
from models.moonshot import MoonshotGPT
from models.spark import Spark
from minio import Minio
from io import BytesIO
import toml


models = {
    "qwen_turbo": QwenGPT("qwen_turbo", "通义千问", "通义千问8k", "qwen_turbo"),
    "deepseek": DeepSeekGPT("deepseek", "DeepSeek", "DeepSeek，价格便宜，自己说自己很强。", ""),
    "gpt": ChatGPT("GPT4", "GPT4", "最为强大的语言模型，俗称为ChatGPT。", "gpt4"),
    "gpt(mini)": ChatGPT("GPT4(mini)", "GPT4(mini)", "廉价版，应该效果不错（至少比国产模型强）", "gpt4omini"),
    "gpt3.5": ChatGPT("GPT3.5", "GPT3.5", "ChatGPT的廉价版本。", "gpt3_5"),
    "glm4": GLM("glm-4", "GLM4", "适用于复杂的对话交互和深度内容创作设计的场景"),
    "glm3.5": GLM("glm-3-turbo", "GLM3.5", "适用于对知识量、推理能力、创造力要求较高的场景"),
    "wenxin4": Wenyanyixin("WENXIN4", "文心一言4", "百度开发的大模型，能力较强。"),
    "wenxin3": Wenyanyixin("WENXIN3", "文心一言3", "上版本的百度开发的大模型，能力较弱但便宜。"),
    "moonshot8": MoonshotGPT("MOONSHOT8", "MoonShot8", "月之暗面 8k 上下文", "moonshot_8k"),
    "moonshot32": MoonshotGPT("MOONSHOT32", "MoonShot32", "月之暗面 32k 上下文", "moonshot_32k"),
    "moonshot128": MoonshotGPT("MOONSHOT128", "MoonShot128", "月之暗面 128k 上下文", "moonshot_128k"),
    "spark_pro": Spark("SPARK_PRO", "Spark Pro", "讯飞星火，据说比较专业。", "generalv3")
}
app = FastAPI()

# app.add_middleware(
#        CORSMiddleware,
#        allow_origins=["*"],  # 可以设置为允许的源，如 ["http://example.com"]
#        allow_credentials=True,
#        allow_methods=["*"],  # 可以设置为允许的 HTTP 方法，如 ["GET", "POST"]
#        allow_headers=["*"],  # 可以设置为允许的请求头，如 ["X-Custom-Header"]
#    )

distin = {}

conf = toml.load("config.toml")
if "models" in conf:
    ms = conf["models"]
    ks = list(models.keys())
    print(ks)
    for k in ks:
        if k not in ms:
            models.pop(k)

if "openai" in conf:
    if "gpt" in models:
        models["gpt"].config(conf["openai"])
    if "gpt3.5" in models:
        models["gpt3.5"].config(conf["openai"])
    if "gpt(mini)" in models:
        models["gpt(mini)"].config(conf["openai"])
else:
    models.pop("gpt")
    models.pop("gpt3.5")
    models.pop("gpt(mini)")

# if "openai-cf" in conf:
#     models["gpt(cf)"].config(conf["openai-cf"])
# else:
#     models.pop("gpt(cf)")

if "baidu" in conf:
    models["wenxin4"].config(conf["baidu"])
    if "wenxin3" in models:
        models["wenxin3"].config(conf["baidu"])
else:
    models.pop("wenxin4")
    models.pop("wenxin3")

if "glm" in conf:
    models["glm4"].config(conf["glm"])
    if "glm3.5" in models:
        models["glm3.5"].config(conf["glm"])
else:
    models.pop("glm4")
    models.pop("glm3.5")

if "moonshot" in conf:
    models["moonshot8"].config(conf["moonshot"])
    if "moonshot32" in models:
        models["moonshot32"].config(conf["moonshot"])
    models["moonshot128"].config(conf["moonshot"])
else:
    models.pop("moonshot")

if "ali" in conf:
    models["qwen_turbo"].config(conf["ali"])
else:
    models.pop("qwen_turbo")

if "spark" in conf:
    models["spark_pro"].config(conf["spark"])
else:
    models.pop("spark_pro")

if "deepseek" in conf:
    models["deepseek"].config(conf["deepseek"])
else:
    models.pop("deepseek")

feishu = conf["feishu"]
for k in feishu:
    it = feishu[k]
    config._tenant_access_token[it["app_id"]] = FeishuTenantKey(it["app_id"], it["app_secret"])

minioClient = Minio(conf['minio']['endpoint'],
                    access_key=conf['minio']['access_key'],
                    secret_key=conf['minio']['secret_key'],
                    secure=False)

init_chatapp(models)

def error(m: str):
    return {
        'code': 10000,
        'message': m,
    }

@app.post("/chatbot/gpt")
async def gen_gpt(data: dict):
    if 'token' not in data:
        return error('need token')
    if data['token'] != conf['token']:
        return error('token error')
    if 'model' not in data:
        return error('need model')
    model = data['model']

    if 'messages' not in data:
        return error('need messages')
    messages = data['messages']

    if model not in models:
        return error(f'{model} not available')
    m: Chater = models[model]

    config = {}
    if 'config' in data:
        config = data['config']
    result = await m.gpt(messages, config)
    return {
        "content": result
    }

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
        elif event_type == "card.action.trigger":
            return handle_card_callback(data)
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

def handle_card_callback(data):
    event = data["event"]
    action = event["action"]
    value = action["value"]
    app_id = data["header"]["app_id"]
    oid = data["event"]["operator"]["open_id"]
    if action["tag"] == "select_static":
        if 'card_change_model' in value:
            model_name = action["option"]
            set_chatapp(oid, model_name)
        if 'card_change_person' in value:
            model_name = action["option"]
            chatapp(oid).change_persona(oid, model_name)
        if 'card_change_mode' in value:
            model_name = action["option"]
            if model_name == "对话":
                chatapp(oid).menu_mode_chat(oid)
            else:
                chatapp(oid).menu_mode_qa(oid)
    return {
        "code": 0,
        "msg": "success"
    }

def getImgUrl(mid, app_id, img_key):
    data = requests.get(f"https://open.feishu.cn/open-apis/im/v1/messages/{mid}/resources/{img_key}?type=image", headers={
        "Authorization": f"Bearer { config.tenant_access_token(app_id).key() }",
    })
    ftype = data.headers["Content-Type"]
    minioClient.put_object(conf['minio']['bucket'], "imgs/" + img_key, BytesIO(data.content), len(data.content), ftype)
    return f"https://{conf['minio']['endpoint']}/{conf['minio']['bucket']}/imgs/{img_key}"
    
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
                    if isinstance(content, str):
                        content += it["text"]
                    else:
                        content.append({
                            "type": "text",
                            "text": it["text"]
                        })
                elif it["tag"] == "a":
                    if isinstance(content, str):
                        content += f"({it['text']})[{it['href']}]"
                    else:
                        content.append({
                            "type": "text",
                            "text": f"({it['text']})[{it['href']}]"
                        })
                elif it["tag"] == "img":
                    if isinstance(content, str):
                        content = [{
                            "type": "text",
                            "text": content
                        }]
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": getImgUrl(mid, app_id, it["image_key"])
                        }
                    })
            # content += "\n"
    elif "image_key" in messageobj:
        content = [{
            "type": "image_url",
            "image_url": {
                "url": getImgUrl(mid, app_id, messageobj["image_key"])
            }
        }]
    print(content)
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
        # 旧的
        # send_models_card(appid, oid)
        send_config_card(appid, oid)
    elif menukey == "change_persona":
        send_persona_card(appid, oid)
    elif menukey == "menu_show_detail":
        send_detail_card(appid, oid)
    return {
        "code": 0,
        "message": "success"
    }
