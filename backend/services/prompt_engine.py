"""
Prompt Engine - Prompt 模板管理
集中管理所有大模型 Prompt，支持模板变量替换
"""

PROMPTS = {
    "paper_summary": {
        "system": """你是一个资深的算法工程师，擅长解读学术论文。你需要从专业角度分析论文的核心价值，用简洁易懂的语言总结。

请用中文回复，结构如下：

📌 核心创新点（3条）
请列出论文最关键的创新点，用bullet point格式，每条不超过30字

📊 关键数据和实验结论
请提取论文最重要的实验数据和数据对比

💡 对算法工程师的启发点
从工程实践角度分析这篇论文对你的工作有什么启发
""",
        "template": """论文标题：{title}

论文摘要：
{abstract}

正文前3000字（如果不够就全部使用）：
{content}"""
    },

    "auto_tag": {
        "system": """你是一个专业的学术文献分类助手。你需要根据文章内容，从已有标签系统中选择最匹配的标签，并推荐可能需要新建的标签。

请用中文回复。
""",
        "template": """已有标签系统：
{existing_tags}

请分析以下文章内容：
标题：{title}
摘要：{abstract}
全文前2000字：{content_preview}

请输出 JSON 格式：
{{
  "recommended_tags": ["tag1", "tag2", "tag3"],
  "new_tags": ["new_tag1"],
  "reason": "简短理由，20字以内"
}}"""
    },

    "related_content": {
        "system": """你是一个知识管理专家，擅长发现内容之间的关联。你需要判断多篇内容是否相关，并解释关联原因。

请用中文回复。
""",
        "template": """当前内容：
标题：{current_title}
摘要：{current_abstract}

候选内容列表：
{candidates}

请为每篇候选内容判断关联度（0-100%），并说明关联理由。

请输出 JSON 格式：
[
  {{
    "id": 1,
    "title": "候选内容标题",
    "relevance_score": 85,
    "reason": "关联理由，30字以内"
  }},
  ...
]"""
    },

    "note_summary": {
        "system": """你是一个知识整理助手，擅长总结和归纳。你需要根据笔记内容，提取核心观点，并尝试与已有知识建立联系。

请用中文回复。
""",
        "template": """笔记内容：
标题：{title}
正文：
{content}

请用简洁的语言总结这篇笔记的核心观点，并给出3个相关标签建议。"""
    }
}


class PromptEngine:
    @staticmethod
    def build(tag: str, **kwargs) -> list:
        if tag not in PROMPTS:
            raise ValueError(f"Unknown prompt tag: {tag}")

        prompt = PROMPTS[tag]
        system_content = prompt["system"]
        user_content = prompt["template"].format(**kwargs)

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    @staticmethod
    def get_available_tags() -> list:
        return list(PROMPTS.keys())