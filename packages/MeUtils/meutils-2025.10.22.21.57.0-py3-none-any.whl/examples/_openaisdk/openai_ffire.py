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

client = OpenAI(
    base_url=os.getenv("FFIRE_BASE_URL"),
    api_key=os.getenv("FFIRE_API_KEY") + "-29512"
    # api_key=os.getenv("FFIRE_API_KEY"),

    # base_url=os.getenv("ONEAPIS_BASE_URL"),
    # api_key=os.getenv("ONEAPIS_API_KEY") + "-3"

)
#
for i in range(1):
    try:
        completion = client.chat.completions.create(
            # model="kimi-k2-0711-preview",
            # model="deepseek-reasoner",
            # model="qwen3-235b-a22b-thinking-2507",
            # model="qwen3-235b-a22b-instruct-2507",
            # model="qwen-image",
            # model="glm-4.5",
            # model="deepseek-v3-1-think",
            # model="kimi-k2-0905-preview",
            # model="kimi-k2-0711-preview",

            # model="glm-4.5-air",
            # model="deepseek-v3-2-exp",
            model = "doubao-seed-1-6-thinking-250715",
            # model="doubao-seed-1-6-lite-251015",
            # model="doubao-1-5-thinking-vision-pro-250428",
            # model="deepseek-r1-250528",
            # model="deepseek-v3-1-250821",

            #
            messages=[
                {"role": "user", "content": 'are you ok?'}
            ],
            # stream=True,
            max_completion_tokens=1,
            # extra_body={"xx": "xxxxxxxx"}
            # extra_body={
            #     "thinking": {"type": "enabled"},
            #
            #     # "enable_thinking": True  # parameter.enable_thinking only support stream
            # }
        )
        print(completion)
        for i in completion:
            print(i)
    except Exception as e:
        print(e)

# model = "doubao-embedding-text-240715"
#
# r = client.embeddings.create(
#     input='hi',
#     model=model
# )
# print(r)
