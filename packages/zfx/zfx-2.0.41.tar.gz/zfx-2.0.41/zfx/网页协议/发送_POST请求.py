import requests
from requests import Response
from typing import Any, Union


def 发送_POST请求(
    url: str,
    严格模式: bool = True,
    **kwargs: Any
) -> Union[Response, str]:
    """
    安全发送 HTTP POST 请求。如果请求成功那么返回的一定是 Response 对象，如果请求失败就返回错误信息，
    所以只要检测返回值是不是字符串，就能判断是否请求失败。

    功能说明：
        封装 requests.post()，在功能上完全兼容原生接口，
        但在出现异常（网络错误、超时、SSL错误等）时不会抛出异常，
        而是返回错误信息字符串。可选“严格模式”控制状态码判断。

    参数：
        url (str):
            请求的完整 URL，例如 "https://www.example.com/api"。
        严格模式 (bool):
            是否将非 2xx 状态码视为异常。
              - True：状态码非 2xx 将触发异常并返回错误信息。
              - False：始终返回 Response 对象。
            默认值为 True。
        **kwargs (Any):
            透传给 requests.post() 的任意参数，
            包括 data、json、headers、timeout、proxies、cookies 等。

    返回：
        requests.Response | str:
            - 请求成功（或严格模式关闭）时返回 Response 对象；
              可直接访问属性：.text、.json()、.status_code。
            - 出现任何异常时返回错误信息字符串，如 "请求失败: 连接超时"。

    使用示例：只要检测返回值是不是字符串，就能判断是否请求失败
        示例一：发送表单数据
            响应 = 发送_POST请求(
                "https://www.example.com/api/login",
                data={"username": "admin", "password": "123456"},
                timeout=10
            )
            print(响应.status_code if not isinstance(响应, str) else 响应)

        示例二：发送 JSON 数据
            响应 = 发送_POST请求(
                "https://www.example.com/api/submit",
                json={"task": "run", "priority": "high"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            if isinstance(响应, str):
                print("请求失败：", 响应)
            else:
                print("请求成功，状态码：", 响应.status_code)

        示例三：通过返回结果是否为对象判断
            响应 = 发送_POST请求("https://www.example.com/api/test")
            if isinstance(响应, requests.Response):
                print("请求成功:", 响应.status_code)
            else:
                print("请求失败:", 响应)

    说明：
        1. 可替代原生 requests.post() 安全使用；
           无论何种异常均不会抛出错误。
        2. 若需批量采集或无人值守任务，推荐启用严格模式=True。
        3. 若需完全控制 HTTP 状态码逻辑，可关闭严格模式。
        4. 若 API 需要 JSON 请求体，请使用 json=payload 而非 data=payload。
    """
    try:
        resp = requests.post(url, **kwargs)
        if 严格模式:
            resp.raise_for_status()
        return resp
    except Exception as e:
        return f"请求失败: {repr(e)}"