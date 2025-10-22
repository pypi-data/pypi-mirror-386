#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chattts
# @Time         : 2024/6/4 10:50
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 声音克隆
# https://dzkaka-chattts.hf.space/
# Hilley/ChatTTS-OpenVoice
# lenML/ChatTTS-Forge
from meutils.pipe import *
from gradio_client import Client, file

# client = Client("Dzkaka/ChatTTS", hf_token="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", output_dir="tmp")
# client = Client("markmagic/ChatTTS", hf_token="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", output_dir="tmp")
#
# #
# result = client.predict(
#     text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
#     temperature=0.3,
#     top_P=0.7,
#     top_K=20,
#     audio_seed_input=42,
#     text_seed_input=42,
#     refine_text_flag=True,
#     api_name="/generate_audio"
# )
# print(result)


# client = Client("markmagic/ChatTTS", hf_token="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", output_dir="tmp")

# result = client.predict(
#     text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
#     temperature=0.3,
#     top_P=0.7,
#     top_K=20,
#     audio_seed_input=42,
#     text_seed_input=42,
#     refine_text_flag=True,
#     api_name="/generate_audio"
# )
# print(result)


from gradio_client import Client, file

# 克隆
client = Client("Hilley/ChatTTS-OpenVoice", hf_token="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", output_dir="tmp")


client = Client("betterme/ChatTTS-OpenVoice", hf_token="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", output_dir="tmp")

# result = client.predict(
#     text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
#     audio_ref=file(
#         'https://hilley-chattts-openvoice.hf.space/file=/tmp/gradio/8373380c451c716ded54e6d1de959cc7c5fc4d72/speaker.mp3'),
#     temperature=0.3,
#     top_P=0.7,
#     top_K=20,
#     audio_seed_input=42,
#     text_seed_input=42,
#     refine_text_flag=True,
#     refine_text_input="[oral_2][laugh_0][break_6]",
#     api_name="/generate_audio"
# )
# print(result)

with timer():

    result = client.predict(
        text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
        audio_ref=file('/Users/betterme/PycharmProjects/AI/ChatLLM/examples/openaisdk/audio.wav'),
        temperature=0.3,
        top_P=0.7,
        top_K=20,
        audio_seed_input=42,
        text_seed_input=42,
        refine_text_flag=True,
        refine_text_input="[oral_2][laugh_0][break_6]",
        api_name="/generate_audio"
    )
    print(result)
