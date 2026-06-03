## Agnes Image 2.1 Flash
**Agnes Image 2.1 Flash** 是由 **Sapiens AI** 推出的升级版图像生成模型，支持 **文生图** 和 **图生图** 工作流。

相比之前版本，Agnes Image 2.1 Flash 在 **高信息密度图像** 生成方面进行了优化，更适合需要复杂视觉细节、丰富构图和清晰语义对齐的场景。

---

### 模型概述
Agnes Image 2.1 Flash 面向高质量图像生成与图像编辑任务设计，适用于创意设计、营销素材、复杂场景生成和内容生产等场景。

---

### 核心能力
| 能力 | 说明 |
| --- | --- |
| Text-to-Image | 根据自然语言提示词生成高质量图像 |
| Image-to-Image | 根据提示词对现有图像进行转换或优化 |
| 高信息密度图像优化 | 更好地处理细节丰富、布局复杂、视觉元素密集的图像 |
| 构图保持 | 在编辑或转换输入图像时保持原始构图 |
| 灵活尺寸控制 | 支持自定义输出尺寸，例如 `1024x768` |
| URL 响应 | 以可访问 URL 的形式返回生成结果 |


---

### 适用场景
Agnes Image 2.1 Flash 适用于以下场景：

| 场景 | 示例用例 |
| --- | --- |
| 创意设计 | 概念艺术、视觉探索、海报草图 |
| 营销内容 | 活动图片、产品视觉、社交媒体创意图 |
| 高密度视觉生成 | 细节丰富的场景、复杂构图、复杂环境 |
| 图像转换 | 风格迁移、场景重新打光、背景转换 |
| 内容生产 | App 素材、缩略图、Banner、故事视觉图 |


---

### API 信息
#### Endpoint
| 项目 | 说明 |
| --- | --- |
| API Endpoint | `https://apihub.agnes-ai.com/v1/images/generations` |
| Request Method | `POST` |
| Content-Type | `application/json` |
| Authentication | `Bearer Token` |
| Authentication Header | `Authorization: Bearer YOUR_API_KEY` |


---

### 请求参数
| 参数 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `model` | string | 是 | 模型名称，固定为 `agnes-image-2.1-flash` |
| `prompt` | string | 是 | 用于图像生成或图像编辑的文本指令 |
| `size` | string | 否 | 输出图像尺寸，例如 `1024x768` |
| `extra_body` | object | 否 | 高级工作流所需的额外参数 |
| `extra_body.image` | array | 否 | 图生图任务中的输入图像 URL |
| `extra_body.response_format` | string | 否 | 响应格式，例如 `url` |


---

### 调用示例
#### 1. 文生图请求
用于根据文本提示词生成图像。

```plain
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "A luminous floating city above a misty canyon at sunrise, cinematic realism",
    "size": "1024x768"
  }'
```

---

#### 2. 图生图请求
用于在保持原始构图的基础上转换现有图像。

```plain
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Transform the scene into a rain-soaked cyberpunk night with neon reflections while preserving the composition",
    "size": "1024x768",
    "extra_body": {
      "image": [
        "https://example.com/input-image.png"
      ],
      "response_format": "url"
    }
  }'
```

---

### 推荐 Prompt 结构
为了获得更好的图像生成效果，建议使用清晰的 Prompt 结构：

```plain
[Subject] + [Scene / Environment] + [Style] + [Lighting] + [Composition] + [Quality Requirements]
```

#### 示例
```plain
A luminous floating city above a misty canyon at sunrise, cinematic realism, wide-angle composition, rich architectural details, soft golden light, high visual density
```

对于图生图任务，建议明确描述：

+ 需要改变什么
+ 需要保持什么不变

#### 图生图示例
```plain
Transform the scene into a rain-soaked cyberpunk night with neon reflections while preserving the original composition and main subject layout.
```

---

### 最佳实践
#### 文生图
生成复杂图像时，建议使用更详细的提示词，并包含以下信息：

+ 主体
+ 环境
+ 风格
+ 光照
+ 镜头角度
+ 期望的细节程度

#### 示例
```plain
A futuristic city marketplace filled with flying vehicles, holographic signs, dense crowds, neon lighting, cinematic realism, ultra-detailed, high-information-density composition
```

---

#### 图生图
编辑现有图像时，建议同时明确说明：

+ 需要进行的转换
+ 需要保留的内容

#### 示例
```plain
Convert the image into a fantasy winter landscape, add snow, warm window lights, and a magical atmosphere, while preserving the original building structure and camera angle.
```

---

#### 高信息密度图像
Agnes Image 2.1 Flash 针对复杂、细节丰富的视觉内容进行了优化。

为了获得更好的效果，建议在 Prompt 中清晰描述视觉层级，包括：

+ 主体
+ 背景环境
+ 重要的次要细节
+ 风格与光照
+ 构图限制
+ 如果是图生图任务，需要说明哪些内容应保持不变

---

### 价格
| 类型 | 价格 | 现价 |
| --- | --- | --- |
| Generated Images | `$0.003 / image` | `$0 / image` |


---

### 说明
+ 使用 `agnes-image-2.1-flash` 作为模型名称
+ 文生图任务必须包含 `model` 和 `prompt`
+ 图生图任务需要在 `extra_body.image` 中提供输入图像 URL
+ 当需要以图片 URL 返回生成结果时，可使用 `response_format: "url"`
+ 不要在公开文档中暴露临时 API Key，所有公开示例均应使用 `YOUR_API_KEY`

> 来自: [Agnes AI | AI Gateway, Free AI API & AI Applications](https://agnes-ai.com/doc/agnes-image-21-flash#heading-%E8%AF%B4%E6%98%8E)
>





