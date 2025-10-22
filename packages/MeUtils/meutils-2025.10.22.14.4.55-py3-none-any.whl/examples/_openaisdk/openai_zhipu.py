#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

# e21bd630f681c4d90b390cd609720483.WSFVgA3KkwNCX0mN
client = OpenAI(
    # base_url="https://free.chatfire.cn/v1",
    # api_key="9df724995f384c2e91d673864d1d32eb.aeLMBoocPyRfGBx8",
    api_key="627d56dddc0f4bf8b09d7269ea34605c.F2HiZyi39n5a6bU0",
    base_url="https://open.bigmodel.cn/api/paas/v4"

    # api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YmFmYWQzYTRmZDU0OTk3YjNmYmNmYjExMjY5NThmZiIsImV4cCI6MTczODAyNDg4MiwibmJmIjoxNzIyNDcyODgyLCJpYXQiOjE3MjI0NzI4ODIsImp0aSI6IjY5Y2ZiNzgzNjRjODQxYjA5Mjg1OTgxYmY4ODMzZDllIiwidWlkIjoiNjVmMDc1Y2E4NWM3NDFiOGU2ZmRjYjEyIiwidHlwZSI6InJlZnJlc2gifQ.u9pIfuQZ7Y00DB6x3rbWYomwQGEyYDSE-814k67SH74",
    # base_url="https://any2chat.chatfire.cn/glm/v1"
)

message = """
你好
"""

try:
    completion = client.chat.completions.create(
        model="glm-4.5",
        # model="xxxxxxxxxxxxx",
        messages=[

            {"role": "user", "content": message}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        # stream=True,
        max_tokens=10,
        # stream_options={
        #     "include_usage": True,
        # }
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

print(completion)
for chunk in completion:
    print(bjson(chunk))
    print(chunk.choices[0].delta.content, flush=True)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )
