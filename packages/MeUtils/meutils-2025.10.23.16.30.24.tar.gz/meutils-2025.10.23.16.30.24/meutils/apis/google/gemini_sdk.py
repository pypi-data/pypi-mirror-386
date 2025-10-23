#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : st
# @Time         : 2025/4/3 15:24
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.async_utils import async_to_sync

from meutils.io.files_utils import to_url, to_bytes
from meutils.schemas.openai_types import CompletionRequest

from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig, Content, HarmCategory, HarmBlockThreshold, Part, \
    ThinkingConfig
from google.genai.chats import _is_part_type

config = GenerateContentConfig(

    temperature=0.7,
    top_p=0.8,
    response_modalities=['Text', 'Image'],
)

# self._http_options.base_url = 'https://generativelanguage.googleapis.com/'
# self._http_options.api_version = 'v1beta'
client = genai.Client(
    api_key="AIzaSyCa8PYURpxFKz7yOtQB_O_wRfrX0gYh9L4",
    http_options=HttpOptions(
        base_url="https://all.chatfire.cc/genai"
    )
)

GOOGLE_CREDENTIALS_JSON="""{
  "type": "service_account",
  "project_id": "mystic-gradient-460414-s3",
  "private_key_id": "074dc3f29316a8d663c6af1eb3e9b60f9c440230",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCtAW0wwjk0GheH\nF1PEps5Q+smR9Fc9lBcK6R5cTpJo0aNC/9xvz6yqFXYpTjTqwUYK8EH62RFP4K9g\neZRTAQdF4qXP7S1cPsyeBEtk2whsjUIThS0dK1FZzOM3CLM+JRUU9AJdkQWuY4pT\ngfcZ+x5KtfbbTZQ3rf91ZPbaJID/cEd1yjiquhSWG6UGYxN09YPEmPOMAUSBmphI\nWhPdMLih3lghxHRbIhXF2y8uTAIVifyT4xFb7C9IT4NphMt/Ee5hpN+GzlveNsPK\n6UdO7XBgpWX+GjxCoxKgvuvpsJxBprv87BVar4jOFS8YaIMBaSKV37ZKDs1/JNaa\nYn0nCepJAgMBAAECggEABCMNOH3idoqbrqsqAYEwHItcq9DtD5/Fi8kehNxLn7ZI\nmkLqQ2GyyifkeREhzo3D1iHf4AbWBUQVCYBqwa/b+8mzR5UvMR4e0DX/1AfxTAA2\nOOeFuEV3hudRdRjQCW/DUOqTTme3/C8s6PmJ/jztIOH4Rs70eP7gBY9+ICIAlCsR\n258PYn3AkLq6u3f0lYVeafV2I52aX861FlQTGNfTg3Npixx0ygWKrppX67bhlzm8\nyedpkCc3S+ZIjfYAG8mO57vYWUi0oPA6TDbzAQBHqq1Su2+WvsCaqpJ3PtPVigSj\n/KSsUmCXGMXDl3/yRBvuzV6SMlpylBx72SJY8Pn0gQKBgQDz9f6+58l7BBG1fFKe\nYJdRViuGjNG6pKfXnPFaZEpwwgJx2C4chkEKBB6ge6hiIrk9CCE365xjVl82l99x\nqukOWf6dsW6nX7U4oMNQ53ZMPpCdHvaFI9E/B9Exl01GGx61Ajx88NMFVXDYbWa+\n+gKZ6DFeMukMwqWAPqRmMbp8gQKBgQC1iwn6mbsxiSteZ9SzfE+rPb9FkxC/W0VO\nQMBwTVD52M5STZbuXj+oRP1DXFEz1HWNWhrX2w92faLgaZQv5rbXXXkI5zD1Ymlo\n82yjxjoe2fs79GzuQjs5pVzr9Gd7qjqDiHQETV67uqkjjjrBDxtnh2pBJrQ7NAX4\nWQ5YvO2pyQKBgQDlWaLAftAf4ldzswlI863OPaB1wfV57koMnfMY86g4EWyS8pWH\nI4AJlo3kedx3RgW3pujz1YEUsqKYhHcAOZkYcOq5/ZD1sTiBoEF+0duZGkiCLhW8\nXUveYc79PCzdd6mKqiuLmiwIm6aXEWLCr++6GVwwHtSRtnw48KtFmAKmAQKBgEHn\n6AeCJ+Mj2Qq8xwsh5gpUsEuhyEKv78ko2LPsXalWfBCE+nYu4Q1Ffmwl55TZXJOk\nUnpqnIJ3udmeep2pNFebJ4WD6NIsl/fx507Nd+wbVom9go48nSOgVMuUPr02X2fA\n8d1d+TZN3Xl6+Pl9coVzM6/TTTrw9/ng2sR8UguBAoGBAJ6SMKAqa+yjZezDUkC3\nUkmywTRX9vfhH5mDv+kj1MHW++hLYhLE7WRNtMhgf9idLEQBbw7jzoS4wmx9jtPu\nP0mUh67fjctbtR6uxbuZl5sY3eMx03hmv5H33aazhMA7mQXjMPS7gXTIxMoE2Wmw\nFpJyddFAuwMDZecDr74xNU9b\n-----END PRIVATE KEY-----\n",
  "client_email": "xxxxx-350@mystic-gradient-460414-s3.iam.gserviceaccount.com",
  "client_id": "115968049812880579488",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxxx-350%40mystic-gradient-460414-s3.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}"""


client = genai.Client(
    vertexai=True,
    credentials=GOOGLE_CREDENTIALS_JSON,
    http_options=HttpOptions(
        base_url="https://all.chatfire.cc/genai"
    )
)
if __name__ == '__main__':
    model = "gemini-2.0-flash-exp-image-generation"
    model = "gemini-2.5-flash-preview-04-17"

    request = CompletionRequest(
        model=model,
        messages=[
            {
                "role": "user", "content": [
                {
                    "type": "text",
                    "text": "一句话总结"
                },
                {
                    "type": "image_url",
                    "image_url": {

                        "url": "https://oss.ffire.cc/files/kling_watermark.png"

                    }
                }
            ]
            }],

    )

    response = client.aio.chats.create(
        model=model,
        config=GenerateContentConfig(
            system_instruction=None,
            max_output_tokens=None,
            # response_modalities=['Text', 'Image'],

            thinking_config=ThinkingConfig(include_thoughts=True, thinking_budget=24576),
        ),

        # history=[
        #
        #     Content(
        #         role="user",
        #         parts=[
        #             Part.from_text(
        #                 text="画条狗"
        #             )
        #         ]
        #     ),
        #     Content(
        #         role="model",
        #         parts=[
        #             Part.from_text(
        #                 text="Ok"
        #             ),
        #
        #             Part.from_bytes(
        #                 data=async_to_sync(to_bytes)("https://oss.ffire.cc/files/kling_watermark.png"),
        #                 mime_type="image/png"
        #             ),
        #         ]
        #     )
        #
        # ]
    )

    # "mime_type": "image/png"

    p = Part.from_uri(file_uri="https://oss.ffire.cc/files/kling_watermark.png", mime_type="image/png")
    pp = Part.from_bytes(
        data=async_to_sync(to_bytes)("https://oss.ffire.cc/files/kling_watermark.png"),
        mime_type="image/png"
    )


    # pt = Part.from_text(text="文本")

    # {'video_metadata': None,
    #  'thought': None,
    #  'code_execution_result': None,
    #  'executable_code': None,
    #  'file_data': {'file_uri': 'https://oss.ffire.cc/files/kling_watermark.png',
    #                'mime_type': 'image/png'},
    #  'function_call': None,
    #  'function_response': None,
    #  'inline_data': None,
    #  'text': None}

    #
    async def main():
        message = [
            Part.from_text(text="1+1"),
            # pp
        ]

        print(_is_part_type(message))
        chunks = await response.send_message_stream(message)

        async for chunk in chunks:
            logger.debug(chunk)
            if chunk.candidates:
                parts = chunk.candidates[0].content.parts
                for part in parts or []:
                    if len(str(part)) < 500:
                        logger.debug(part)
                    if part.inline_data:
                        image_url = await to_url(part.inline_data.data, mime_type=part.inline_data.mime_type)
                        logger.info(image_url)

                    if part.text:
                        logger.info(part.text)
            # print(i.model_dump_json(indent=4, exclude_none=True))  # inline_data


    # response = client.models.generate_content(
    #     model="gemini-2.0-flash-exp-image-generation",
    #     contents=['画条狗'],
    #
    #     # model="gemini-2.5-pro-exp-03-25",
    #     # model="gemini-2.0-flash",
    #
    #     # contents=[
    #     #     Part.from_uri(file_uri='https://generativelanguage.googleapis.com/v1beta/files/test', mime_type='image/png'),
    #     #
    #     #           "一句话总结"],
    #     config=config
    # )
    #
    # # client.aio.
    # # client.aio.chats.create()
    #
    # if __name__ == '__main__':
    #     arun(file_object)

    arun(main())

# ValueError: Message must be a valid part type: typing.Union[google.genai.types.File, google.genai.types.Part, PIL.Image.Image, str] or typing.Union[google.genai.types.File, google.genai.types.Part, PIL.Image.Image, str, google.genai.types.PartDict], got <class 'list'>

"""
curl "https://all.chatfire.cc/genai/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent?key=AIzaSyCa8PYURpxFKz7yOtQB_O_wRfrX0gYh9L4" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [
    {
      "parts": [
        {
          "text": "9.8 9.11 哪个大"
        }
      ]
    }
  ],
  "generationConfig": {
    "thinkingConfig": {
        "includeThoughts": true,
          "thinkingBudget": 1024
    }
  }
}'
"""

from litellm import completion
import os

# auth: run 'gcloud auth application-default'
os.environ["VERTEXAI_PROJECT"] = "hardy-device-386718"
os.environ["VERTEXAI_LOCATION"] = "us-central1"

response = completion(
  model="vertex_ai/gemini-1.5-pro",
  messages=[{ "content": "Hello, how are you?","role": "user"}]
)