"""
LLM Client - 大模型 API 封装层
支持 OpenAI、豆包等多家提供商，统一接口
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests


# ==========================================
# 安全配置管理 - 支持多种配置来源
# ==========================================
class SecureConfig:
    """安全配置管理，支持环境变量和 .env 文件"""
    
    _config = None
    
    @classmethod
    def _load_config(cls):
        if cls._config is not None:
            return cls._config
        
        cls._config = {}
        
        # 1. 从 .env 文件加载
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        if env_path.exists():
            cls._load_from_env_file(env_path)
        
        # 2. 从环境变量加载（覆盖 .env 文件）
        cls._load_from_env_vars()
        
        return cls._config
    
    @classmethod
    def _load_from_env_file(cls, env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        cls._config[key.strip()] = value.strip().strip('"').strip("'")
        except Exception:
            pass
    
    @classmethod
    def _load_from_env_vars(cls):
        for key in ['LLM_API_KEY', 'LLM_PROVIDER', 'LLM_BASE_URL', 'LLM_MODEL']:
            value = os.environ.get(key)
            if value:
                cls._config[key] = value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return cls._load_config().get(key, default)
    
    @classmethod
    def get_api_key(cls) -> str:
        """获取 API Key，按优先级从环境变量、.env 文件获取"""
        return cls.get('LLM_API_KEY', '')
    
    @classmethod
    def get_provider(cls) -> str:
        """获取默认提供商"""
        return cls.get('LLM_PROVIDER', 'doubao')
    
    @classmethod
    def get_base_url(cls) -> str:
        """获取基础 URL"""
        return cls.get('LLM_BASE_URL', '')
    
    @classmethod
    def get_model(cls) -> str:
        """获取默认模型"""
        return cls.get('LLM_MODEL', '')
    
    @classmethod
    def get_temperature(cls) -> float:
        """获取默认温度参数"""
        return float(cls.get('LLM_TEMPERATURE', 0))
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置 API Key"""
        return bool(cls.get_api_key())


def call_teg_llm(api_key, base_url, model_id, img_url, prompt, temperature, top_k, max_tokens):
    """
    调用 TEG LLM API（支持图片输入）
    
    Args:
        api_key: API Key
        base_url: API 基础 URL
        model_id: 模型 ID
        img_url: 图片 URL（可选）
        prompt: 提示词
        temperature: 温度参数
        top_k: Top-K 参数
        max_tokens: 最大 token 数
    
    Returns:
        LLM 返回的内容
    """
    llm_res = '调用失败无返回'
    retry_count = 0
    while retry_count < 3:
        # 根据是否有图片选择不同的 content 格式
        if img_url and img_url.strip():
            # 有图片：使用 multimodal 格式
            content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        else:
            # 无图片：使用纯文本格式
            content = [
                # {
                #     "type": "image_url",
                #     "image_url": {
                #         "url": img_url
                #     }
                # },
                {
                    "type": "text",
                    "text": prompt
                }
            ] #prompt
        
        data = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "top_k": top_k,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        try:
            print(f"DEBUG - TEG API Request:")
            print(f"  URL: {base_url}/chat/completions")
            print(f"  Model: {model_id}")
            print(f"  Has Image: {bool(img_url and img_url.strip())}")
            print(f"  Prompt length: {len(prompt)} chars")
            
            response = requests.post(
                base_url + "/chat/completions",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "accept": "application/json",
                    "Authorization": "Bearer " + api_key,
                    "MTimeOut": "60000"
                },
                timeout=(3, 60)
            )
            
            print(f"DEBUG - TEG API Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"DEBUG - TEG API Response Text: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            llm_res = result["choices"][0]["message"]["content"]
            
            if len(llm_res) == 0:
                print(f'{img_url} call_teg_llm error, error_info: {response.text}')
                time.sleep(20)
                retry_count += 1
            else:
                break
        except Exception as e:
            print(f'call_teg_llm error: {str(e)}')
            time.sleep(20)
            retry_count += 1
    
    return llm_res


class LLMClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, provider: str = None, api_key: str = None, base_url: str = None, model_id: str = None, temperature: float = 0.7):
        if self._initialized:
            return

        # 优先使用传入的参数，否则从安全配置获取
        self.provider = provider or SecureConfig.get_provider()
        self.api_key = api_key or SecureConfig.get_api_key()
        self.base_url = base_url or SecureConfig.get_base_url()
        self.model_id = model_id or SecureConfig.get_model()
        self.temperature = temperature

        self._cache: Dict[str, Any] = {}
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "call_count": 0
        }

        self._pricing = {
            "openai": {"prompt": 0.015 / 1000, "completion": 0.02 / 1000},
            "doubao": {"prompt": 0.003 / 1000, "completion": 0.006 / 1000},
            "anthropic": {"prompt": 0.015 / 1000, "completion": 0.075 / 1000},
            "qwen": {"prompt": 0.02 / 1000, "completion": 0.06 / 1000}
        }

        self._initialized = True

    def configure(self, provider: str = None, api_key: str = None, base_url: str = None, model_id: str = None, temperature: float = None):
        if provider:
            self.provider = provider
        if api_key:
            self.api_key = api_key
        if base_url:
            self.base_url = base_url
        if model_id:
            self.model_id = model_id
        if temperature is not None:
            self.temperature = temperature

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2000,
        cache: bool = True
    ) -> Dict[str, Any]:
        cache_key = self._make_cache_key(messages, temperature, max_tokens)

        if cache and cache_key in self._cache:
            return self._cache[cache_key]

        if self.provider == "teg":
            result = self._call_teg(messages, temperature, max_tokens)
        elif self.provider == "openai":
            result = self._call_openai(messages, temperature, max_tokens)
        elif self.provider == "doubao":
            result = self._call_doubao(messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            result = self._call_anthropic(messages, temperature, max_tokens)
        elif self.provider == "qwen":
            result = self._call_qwen(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        self._update_usage(result)
        self._token_usage["call_count"] += 1

        if cache:
            self._cache[cache_key] = result

        return result

    def chat_with_image(
        self,
        prompt: str,
        img_url: str = None,
        model_id: str = None,
        temperature: float = 1.0,
        top_k: int = 1,
        max_tokens: int = 50000
    ) -> Dict[str, Any]:
        """
        支持图片输入的聊天接口（兼容 call_teg_llm 调用方式）

        Args:
            prompt: 提示词
            img_url: 图片 URL（可选）
            model_id: 模型 ID（可选，使用配置的模型或默认值）
            temperature: 温度参数
            top_k: Top-K 参数
            max_tokens: 最大 token 数

        Returns:
            包含 content 的字典
        """
        if not self.api_key:
            return {"error": "API key not configured", "content": ""}

        # 使用 TEG API 方式调用
        base_url = self.base_url or "https://api.example.com"
        model = model_id or self.model_id or SecureConfig.get_model() or "teg-model"
        temp = temperature if temperature != 1.0 else self.temperature

        result = call_teg_llm(
            api_key=self.api_key,
            base_url=base_url,
            model_id=model,
            img_url=img_url,
            prompt=prompt,
            temperature=temp,
            top_k=top_k,
            max_tokens=max_tokens
        )

        return {
            "content": result,
            "model": model,
            "provider": "teg",
            "prompt_tokens": 0,
            "completion_tokens": 0
        }

    def _call_teg(self, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
        """调用 TEG LLM API"""
        if not self.api_key:
            return {"error": "API key not configured", "content": ""}

        prompt = ""
        img_url = ""
        
        # 解析 messages，提取文本和图片
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                prompt += f"{msg.get('role', 'user')}: {content}\n"
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        prompt += item.get("text", "") + "\n"
                    elif item.get("type") == "image_url":
                        img_url = item.get("image_url", {}).get("url")

        base_url = self.base_url or "https://api.example.com"
        model = self.model_id or SecureConfig.get_model() or "teg-model"
        temp = temperature if temperature != 0.0 else self.temperature

        result = call_teg_llm(
            api_key=self.api_key,
            base_url=base_url,
            model_id=model,
            img_url=img_url,
            prompt=prompt,
            temperature=temp,
            top_k=40,
            max_tokens=max_tokens
        )

        return {
            "content": result,
            "model": model,
            "provider": "teg",
            "prompt_tokens": 0,
            "completion_tokens": 0
        }

    def _get_effective_temperature(self, temperature: float) -> float:
        """获取有效的 temperature 值"""
        if temperature != 0.0:
            return temperature
        return self.temperature

    def _make_cache_key(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        content = json.dumps({"messages": messages, "temperature": temperature, "max_tokens": max_tokens}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _call_openai(self, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "API key not configured", "content": ""}

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": self._get_effective_temperature(temperature),
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["choices"][0]["message"]["content"],
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "model": result.get("model", "gpt-3.5-turbo"),
                "provider": "openai"
            }
        except Exception as e:
            return {"error": str(e), "content": ""}

    def _call_doubao(self, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "API key not configured", "content": ""}

        url = self.base_url or "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "doubao-pro",
            "messages": messages,
            "temperature": self._get_effective_temperature(temperature),
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["choices"][0]["message"]["content"],
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "model": result.get("model", "doubao-pro"),
                "provider": "doubao"
            }
        except Exception as e:
            return {"error": str(e), "content": ""}

    def _call_anthropic(self, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "API key not configured", "content": ""}

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        system_msg = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                filtered_messages.append(msg)

        data = {
            "model": "claude-3-haiku",
            "messages": filtered_messages,
            "temperature": self._get_effective_temperature(temperature),
            "max_tokens": max_tokens
        }
        if system_msg:
            data["system"] = system_msg

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["content"][0]["text"],
                "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
                "model": result.get("model", "claude-3-haiku"),
                "provider": "anthropic"
            }
        except Exception as e:
            return {"error": str(e), "content": ""}

    def _call_qwen(self, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "API key not configured", "content": ""}

        url = self.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "qwen-plus",
            "messages": messages,
            "temperature": self._get_effective_temperature(temperature),
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["choices"][0]["message"]["content"],
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "model": result.get("model", "qwen-plus"),
                "provider": "qwen"
            }
        except Exception as e:
            return {"error": str(e), "content": ""}

    def _update_usage(self, result: Dict[str, Any]):
        prompt_tokens = result.get("prompt_tokens", 0)
        completion_tokens = result.get("completion_tokens", 0)

        self._token_usage["prompt_tokens"] += prompt_tokens
        self._token_usage["completion_tokens"] += completion_tokens

        provider = result.get("provider", self.provider)
        pricing = self._pricing.get(provider, self._pricing["doubao"])
        cost = prompt_tokens * pricing["prompt"] + completion_tokens * pricing["completion"]
        self._token_usage["total_cost"] += cost

    def get_usage(self) -> Dict[str, Any]:
        return {
            **self._token_usage,
            "estimated_cost_yuan": round(self._token_usage["total_cost"], 4)
        }

    def clear_cache(self):
        self._cache.clear()

    def reset_usage(self):
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "call_count": 0
        }


_llm_client = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# ==========================================
# 生成 .env 示例文件
# ==========================================
def generate_env_example():
    """生成 .env 文件示例"""
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        return
    
    example_content = """# LLM API 配置文件
# 请将此文件复制为 .env 并填写实际配置

# API Key（必填）
LLM_API_KEY=your-api-key-here

# 默认提供商（可选，默认 doubao）
# 可选值: doubao, openai, anthropic, qwen
LLM_PROVIDER=doubao

# 自定义 API 基础 URL（可选）
# 用于使用代理或私有部署的 API
LLM_BASE_URL=

# 自定义模型（可选）
LLM_MODEL=
"""
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(example_content)


# 自动生成示例配置文件（仅在首次运行时）
generate_env_example()