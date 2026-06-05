## [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http%E5%8D%8F%E8%AE%AE) 推理服务_HTTP协议
## [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_1-%E6%8E%A5%E5%8F%A3%E8%AF%B4%E6%98%8E) 1. 接口说明
协议 ：HTTP 请求方法：POST 默认请求地址如下： (请根据服务发布时间及在线推理页面展示，选择对应的接口地址)

**如有并发提升(含免费模型)、一对一报价等需求**，可以直接添加专属同事微信沟通：  
![](https://cdn.nlark.com/yuque/0/2026/png/1598302/1780568458061-adda0d03-37bb-4702-9dd8-8041636ccce6.png)

## [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_2-%E6%8E%A5%E5%8F%A3%E8%AF%B7%E6%B1%82) 2. 接口请求
### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_2-1-%E8%AF%B7%E6%B1%82%E7%A4%BA%E4%BE%8B) 2.1 请求示例
下面是一个通用的 HTTP 请求 Python Demo 示例，展示了包括普通对话、流式对话和 JSON Mode 在内的多种调用方式。

**注意**：在使用demo之前，请务必替换 `api_key` 为您的API Key。

### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_2-2-%E8%AF%B7%E6%B1%82%E5%8F%82%E6%95%B0) 2.2 请求参数
| 参数 | 类型 | 是否必填 | 要求 | 说明 |
| --- | --- | --- | --- | --- |
| model | string | 是 | | 指定要调用的对话生成模型ID |
| messages | array | 是 | `[{"role": "user", "content":"用户输入内容"}]` | 表示对话上下文的消息列表，支持多轮对话交互。其中，`role`<br/> 用于标识消息发送方（例如 `user`<br/> 表示用户、`assistant`<br/> 表示模型回复），`content`<br/> 则为实际文本内容。 **注意**：仅限DeepSeekV3&R1使用对话前缀续写时，用户需确保 `messages`<br/> 列表里最后一条消息的 `role`<br/> 为 `assistant` |
| stream | boolean | 否 | 取值为 `true`<br/> 或 `false`<br/>，默认值为 `false` | 指定是否采用流式响应模式。若设置为 `true`<br/>，系统将逐步返回生成的回复内容；否则，将一次性返回完整响应 |
| temperature | float | 否 | 取值为`[0,1]`<br/>,默认值为`0.7` | 核采样阈值。用于决定结果随机性，取值越高随机性越强即相同的问题得到的不同答案的可能性越高 |
| max_tokens | int | 否 | 取值为`[1,推理上下文长度)`<br/>，默认值为`2048` | 限制生成回复的最大 tokens 数量，max_tokens的限制需要满足`输入promptToken + 设置参数max_tokens <= 推理上下文长度 - 1`<br/>,参数设置过大可能导致回答中断，请酌情调整，不同模型推理上下文长度存在差异，需结合使用模型进行配置。 |
| reasoning_effort | string | 否 | `low`<br/>, `medium`<br/>, `high`<br/>, 默认`high` | 指导模型在对提示做出响应之前应生成多少推理内容。`low`<br/> 优先考虑速度和节省token，`high`<br/> 优先考虑更完整的推理。**仅针对OpenAI开源的OSS模型生效**。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body`<br/> 对象中。 |
| `lora_id` | string | 否 | 调用微调模型时使用，对应模型服务卡片上的 `resourceId`<br/>。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_headers`<br/> 对象中。 | |
| stop | string[] | 否 | 仅限DeepSeekV3&R1支持 | 模型遇到 stop 字段所指定的字符串时将停止继续生成，这个词语本身不会输出。最多支持4个字符串如["你好”,"天气”] |
| continue_final_message | boolean | 否 | 仅限DeepSeekV3&R1支持，取值为 `true`<br/> 或 `false`<br/>，默认值为 `false` | 指定是否开启对话前缀续写功能，若设置为`true`<br/>，系统将对 `messages`<br/> 列表里最后一条消息的 `role`<br/> 为 `assistant`<br/>的内容进行续写。 |
| `search_disable` | boolean | 否 | `true`<br/> 或 `false`<br/>，默认 `true` | 关闭联网搜索。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body`<br/> 对象中。 |
| `show_ref_label` | boolean | 否 | 默认为 `false`<br/>。`true`<br/> 表示在联网搜索时返回信源信息。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body`<br/> 对象中。 | |
| `enable_thinking` | boolean | 否 | 默认为 `false`<br/>。`true`<br/> 表示开启深度思考模式（**仅部分模型支持**）。**注意**：使用 OpenAI SDK 时，此参数需放在 `extra_body`<br/> 对象中。 | |
| `response_format` | object | 否 | 用于指定模型的输出为 JSON 对象格式。设置为 `{"type": "json_object"}`<br/> 即可。**仅支持 DeepSeek R1 和 V3 模型**。详情见 `2.2.2 response_format 参数说明`<br/>。 | |
| tools | array | 否 | 工具列表，支持 function 类型的工具定义 | 模型可能会调用的工具列表，用于 Function Calling 功能。**注意**：目前仅支持 DeepSeek V3.2 和 GLM-4.7 系列模型。详情见 `2.2.3 tools 参数说明`<br/>。 |
| tool_choice | string | 否 | `auto`<br/>、`none`<br/>、`required`<br/>，默认为 `auto` | 控制模型如何选择和使用工具。`auto`<br/> 表示模型自主决策；`none`<br/> 表示禁用工具调用；`required`<br/> 表示必须调用至少一个工具。 |
| stream_options | object | 否 | 默认值为`{"include_usage": True}` | 针对流式响应模式的扩展配置，如控制是否在响应中包含API调用统计信息等附加数据。 |


#### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_2-2-1-messages-%E5%8F%82%E6%95%B0%E8%AF%B4%E6%98%8E) 2.2.1 `messages` 参数说明
messages 参数用于传递对话内容，包括用户输入和 AI 回复

| 字段 | 含义 | 数据类型 | 取值范围 | 默认值 | 说明 |
| --- | --- | --- | --- | --- | --- |
| role | 角色 | string | system,user,assistant,tool | | **通过system设置对话背景信息，user表示用户的问题，assistant表示AI的回复，tool表示工具调用的返回结果** |
| content | 文本内容 | string or array | -- | | 该角色的对话内容。支持字符串格式或数组格式。数组格式可用于传递多模态内容（如文本和图片的组合），数组中的每个元素可以是文本对象 `{"type": "text", "text": "内容"}`<br/> 或其他类型的内容对象 |


**示例：单轮交互** 单轮交互只需要传递一个user角色的数据

**示例：多轮交互** 多轮交互需要将之前的交互历史按照user->assistant->user->assistant规则进行拼接，并保证最后一条是user的当前问题。

**示例：content 数组格式**`content` 字段支持数组格式，可用于传递多模态内容或结构化内容。

**示例：工具调用交互** 当使用 tools 功能时，需要在 messages 中包含 tool 角色的消息，用于传递工具执行结果。

#### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_2-2-2-response-format-%E5%8F%82%E6%95%B0%E8%AF%B4%E6%98%8E) 2.2.2 `response_format` 参数说明
`response_format` 参数用于强制模型输出严格符合 RFC 8259 规范的 JSON 对象。

**开启方法**

将 `response_format` 参数设置为 `{"type": "json_object"}`。

**功能优势**

+ **可靠性**：确保模型输出的是一个语法正确的 JSON 对象。
+ **简化开发**：无需在 prompt 中反复强调输出 JSON，也无需对模型输出进行复杂的后处理和校验。

**支持模型**

目前仅 DeepSeek R1 和 V3 模型支持 `json_object` 模式。

**Prompt 建议**

为了让模型更好地理解您的意图并生成符合期望的 JSON，建议在 Prompt 中明确指示模型输出 JSON。例如：

**错误处理**

如果 Prompt 的内容与 JSON 输出要求存在冲突，或模型无法生成有效的 JSON，可能会导致输出不完整或返回错误。请确保 Prompt 的引导内容清晰、无歧义。

#### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_2-2-3-tools-%E5%8F%82%E6%95%B0%E8%AF%B4%E6%98%8E) 2.2.3 `tools` 参数说明
`tools` 参数用于定义模型可以调用的工具列表，支持 Function Calling 功能。

**支持模型**

目前 `tools` 功能仅支持部分模型，暂时仅支持以下模型系列：

+ DeepSeek V3.2 系列
+ GLM-4.7 系列

其他模型暂不支持 `tools` 功能，使用不支持的工具功能可能会导致请求失败。

**工具类型**

目前支持 `function` 类型的工具，用于定义可被模型调用的函数。

**工具定义格式**

**参数说明**

| 字段 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| type | string | 是 | 工具类型，目前支持 `function` |
| function | object | 是 | 函数定义对象 |
| function.name | string | 是 | 函数名称，必须是字母、数字或下划线组成，长度不超过32个字符 |
| function.description | string | 是 | 函数功能描述，用于帮助模型判断何时调用此函数 |
| function.parameters | object | 是 | 函数参数定义，必须符合 JSON Schema 格式，用于描述函数所需的参数及其类型 |


**tool_choice 参数说明**

`tool_choice` 参数用于控制模型如何选择和使用工具：

+ `auto`（默认）：模型自主决策是否调用工具
+ `none`：禁用工具调用功能
+ `required`：要求模型必须调用至少一个工具

**使用示例**

**注意事项**

1. 当模型决定调用工具时，响应中的 `message.tool_calls` 字段会包含工具调用信息
2. 需要在后续请求中将工具执行结果以 `tool` 角色的消息添加到 `messages` 中
3. `tool` 角色的消息需要包含 `tool_call_id` 字段，对应 `tool_calls` 中的 `id`

## [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_3-%E6%8E%A5%E5%8F%A3%E5%93%8D%E5%BA%94) 3. 接口响应
### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_3-1-%E5%93%8D%E5%BA%94%E7%A4%BA%E4%BE%8B) 3.1 响应示例
#### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_3-1-1-%E6%88%90%E5%8A%9F%E5%93%8D%E5%BA%94%E7%A4%BA%E4%BE%8B) 3.1.1 成功响应示例
关闭联网检索或不返回检索信源时，返回结构如下：

开启联网检索且返回检索信源时，返回结构如下：

调用工具（Function Calling）时，返回结构如下：

#### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_3-1-2-%E5%BC%82%E5%B8%B8%E7%BB%93%E6%9E%9C%E7%A4%BA%E4%BE%8B) 3.1.2 异常结果示例
### [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_3-2-%E5%93%8D%E5%BA%94%E6%95%B0%E6%8D%AE%E5%8F%82%E6%95%B0) 3.2 响应数据参数
字段说明如下：

| 字段名 | 类型 | 字段说明 |
| --- | --- | --- |
| id | string | 唯一标识符，标识本次对话调用的唯一ID，用于跟踪和调试 |
| choices | array | 包含模型生成回复候选项的数组 |
|   •finish_reason | string | 指示回复生成结束的原因，如`"stop"`<br/>（正常结束）、`"tool_calls"`<br/>（需要调用工具）、`"length"`<br/>（达到最大长度限制）等 |
|   •index | int | 回复候选项在数组中的索引位置，从0开始 |
|   •logprobs | object | 如启用token概率日志，则返回具体信息 |
|   •message | object | 描述回复消息内容的对象，其内部字段如下 |
|     ◦content | string | 模型生成的回复文本内容 |
|     ◦reasoning_content | string | 模型生成的思考文本内容(支持深度思考的模型才有此字段) |
|     ◦plugins_content | array | 联网检索的信源结果列表(支持联网检索的模型才有此字段) |
|         ◦name | string | 联网检索插件名称ifly_search等 |
|         ◦name | string | 联网检索插件结果，此为信源结果列表，`index`<br/>序号，`url`<br/>信源地址，`title`<br/>信源标题 |
|     ◦refusal | object | 模型拒绝回答时返回拒绝信息 |
|     ◦role | string | 消息发送方，通常为`"assistant"` |
|     ◦audio | object | 如支持语音回复则返回音频数据 |
|     ◦function_call | object | 模型调用外部函数时返回调用信息（已废弃，建议使用 tool_calls） |
|     ◦tool_calls | array | 模型调用工具时返回调用详情，包含工具调用列表。每个工具调用包含 `id`<br/>（调用标识）、`type`<br/>（类型，通常为 `function`<br/>）、`function`<br/>（函数信息，包含 `name`<br/> 和 `arguments`<br/>） |
| created | int | 响应生成时间的Unix时间戳（秒级） |
| model | string | 实际调用的模型名称 |
| object | string | 表示响应对象类型 |
| service_tier | string | 表示调用所属的服务层级 |
| system_fingerprint | string | 系统指纹或配置标识 |
| usage | object | 包含token使用统计信息，其内部字段如下： |
|   •completion_tokens | int | 回复文本消耗的token数量 |
|   •prompt_tokens | int | 输入prompt消耗的token数量 |
|   •total_tokens | int | prompt与回复消耗token数量的总和 |
|   •completion_tokens_details | object | 回复生成过程中token的详细统计信息，若无则为`null` |
|   •prompt_tokens_details | object | prompt部分token的详细统计信息 |


## [#](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html#_4-%E9%94%99%E8%AF%AF%E7%A0%81%E5%88%97%E8%A1%A8) 4 . 错误码列表
| 错误码 | 原因 | 解决方案 |
| --- | --- | --- |
| 401-无效的身份验证 | 身份验证无效。 | 确保使用正确的API密钥及请求组织。 |
| 401-提供的API密钥不正确 | 请求的API密钥不正确。 | 检查所用API密钥是否正确，清除浏览器缓存或生成新的密钥。 |
| 403-不支持的国家、地区或领土 | 您正在从不支持的国家、地区或领土访问API。 | 请参考相关页面获取更多信息。 |
| 429-请求速率限制已达上限 | 您发送请求过快。 | 控制请求频率，阅读速率限制指南。 |
| 429-超出当前配额，请检查计划和计费详情 | 您的额度已用尽或已达到每月最高消费限制。 | 购买更多额度或了解如何提高使用限制。 |
| 500-服务器处理请求时发生错误 | 服务器内部出现问题。 | 稍后重试请求；若问题持续，请联系我们查看状态页面。 |
| 503-引擎当前过载，请稍后重试 | 服务器流量过大。 | 稍候重试您的请求。 |




> 来自: [推理服务_HTTP协议 | 讯飞开放平台文档中心](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html)
>





