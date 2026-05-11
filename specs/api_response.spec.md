# 接口响应格式规约

## 目标
统一全项目API响应格式，保证前端解析一致性，简化错误处理逻辑。

## 输入输出

### 统一响应格式
```json
{
    "code": 状态码,
    "data": 响应数据,
    "msg": 提示信息
}
```

### 字段说明
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | Integer | 是 | 状态码，0表示成功，非0表示错误 |
| data | Any | 是 | 响应数据，成功时返回业务数据，失败时返回null或空对象 |
| msg | String | 是 | 提示信息，成功时可为空或"success"，失败时返回错误详情 |

## 规则

### 1. 成功响应示例
```json
{
    "code": 0,
    "data": {
        "paper_list": [],
        "total_count": 100
    },
    "msg": "success"
}
```

### 2. 失败响应示例
```json
{
    "code": 40001,
    "data": null,
    "msg": "论文不存在"
}
```

### 3. 全局错误码标准
| 状态码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40000 | 通用请求错误 |
| 40001 | 资源不存在 |
| 40002 | 参数缺失 |
| 40003 | 参数非法 |
| 50000 | 服务器内部错误 |
| 50001 | 数据库操作失败 |
| 50002 | 外部服务调用失败 |

### 4. Flask 封装示例
```python
from flask import jsonify

def success_response(data=None, msg="success"):
    return jsonify({"code": 0, "data": data, "msg": msg})

def error_response(code, msg, data=None):
    return jsonify({"code": code, "data": data, "msg": msg})
```

## 约束
- 所有接口必须严格遵循此统一响应格式
- 禁止直接返回裸数据（如直接返回数组、字符串等）
- code字段必须使用整数类型，不能用字符串
- 异常捕获后也需包装成此统一格式返回

## 验收标准
- 所有API接口返回完全符合{"code": xxx, "data": xxx, "msg": xxx}格式
- 无裸数据响应
- 状态码严格遵循全局错误码标准
