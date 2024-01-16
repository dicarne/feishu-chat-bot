# 飞书聊天机器人

用于飞书自建应用的聊天机器人。

支持ChatGPT、文心一言、ChatGLM。

## 配置文件
需要创建一个配置文件`config.toml`，详细内容如下。可以在`models`中选择性填写想要使用的模型。`feishu`相关的配置是你的自建应用的id和secret。如果某个配置没有填写，便不会使用那个模型。

```toml
models = [
    "gpt",
    "glm",
    "wenxin4",
    "wenxin3",
]

[openai]
api_key = "xxxxxxxxxxxxxxxx"
proxy = "http://xxxxxxxxxxxxxx:xxxx"
model = "gpt-4-1106-preview"

[baidu]
api_key = "xxxxxxxxxxxxxxxxx"
secret_key = "xxxxxxxxxxxxxxxxxx"

[glm]
api_key = "xxxxxxxxxxxxxxxxxxxxxx"

[feishu.myapp]
app_id = "xxxxxxxxxxxxxxxxxx"
app_secret = "xxxxxxxxxxxxxxxxxxxxxxxxx"
```

## 菜单
可以手动给机器人增加菜单。需要在飞书开放平台设置。

`reset_context`：重置上下文

`mode_chat`：切换为对话模式

`mode_qa`：切换为问答模式

`request_switch_model`：回复选择模型的卡片

`change_persona`：返回选择人格的卡片

`menu_show_detail`：返回当前模式信息