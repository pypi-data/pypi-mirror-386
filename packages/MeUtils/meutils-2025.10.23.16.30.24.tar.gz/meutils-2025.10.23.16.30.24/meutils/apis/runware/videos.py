#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/10/13 13:46
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.clients import AsyncClient
from meutils.notice.feishu import send_message_for_images
from meutils.io.files_utils import to_url, to_url_fal
from meutils.schemas.video_types import SoraVideoRequest, Video

from openai import APIStatusError

from meutils.apis.translator import deeplx

MODELS_MAPPING = {
    "sora2": "openai:3@1",
}


async def create_task(request: SoraVideoRequest, api_key: str, base_url: Optional[str] = None):
    payload = [
        {
            "taskType": "videoInference",

            "taskUUID": str(uuid.uuid4()),

            "model": MODELS_MAPPING.get(request.model, request.model),
            "positivePrompt": request.prompt,

            "numberResults": 1,

            "duration": int(request.seconds),

            "includeCost": True,

            "webhookURL": "https://openai-dev.chatfire.cn/sys/webhook/runware?expr=%24..taskUUID"  # task_id
        },

    ]

    payload[0]["width"], payload[0]["height"] = map(int, request.size.split("x"))

    if request.input_reference:  # todo 多图
        if not isinstance(request.input_reference, list):
            request.input_reference = [request.input_reference]

        urls = await to_url_fal(request.input_reference, content_type="image/png")
        payload[0]["frameImages"] = [
            {
                "inputImage": url
            }
            for url in urls
        ]

    logger.debug(bjson(payload))

    try:
        client = AsyncClient(base_url="https://api.runware.ai/v1", api_key=api_key, timeout=300)
        response = await client.post(
            "/",
            body=payload,
            cast_to=object
        )

        video = Video(
            id=response["data"][0]["taskUUID"],
            model=request.model,
            seconds=request.seconds,
        )

        # await redis_aclient.set(video.id, api_key) # 回调接口即可

        return video

    except APIStatusError as e:
        if (errors := e.response.json().get("errors")):
            logger.debug(bjson(errors))

        raise e


async def get_task(task_id):
    video = Video(id=task_id)

    webhook_id = f"webhook:runware:{task_id}"
    if not (data := await redis_aclient.lrange(webhook_id, 0, -1)):
        raise ValueError(f"task_id not found")

    runware_response = json.loads(data[0])
    if data := runware_response["data"]:
        if video_url := data[0].get("videoURL"):
            video.progress = 100
            video.video_url = video_url

    return video


if __name__ == '__main__':
    model = "openai:3@1"

    request = SoraVideoRequest(model=model, prompt="a cat")

    # logger.info(request)

    # arun(generate(request, api_key="Fk3Clsgcwc3faIvbsjDajGFATJLfaWpE"))

    # https://openai-dev.chatfire.cn/sys/webhook/runware?expr=%24..taskUUID
    arun(get_task("3f7fcfc4-e257-4cb7-bf97-439bceaa7cc3"))

    # {
    #     "data": [
    #         {
    #             "taskType": "videoInference",
    #             "taskUUID": "8a5a1c09-d0a5-4b1b-9b67-8943cacc935f"
    #         }
    #     ]
    # }

"""
curl --request POST \
--url 'https://api.runware.ai/v1' \
--header "Authorization: Bearer Fk3Clsgcwc3faIvbsjDajGFATJLfaWpE" \
--header "Content-Type: application/json" \
--data-raw '[
  {
    "taskType": "videoInference",
    "duration": 4,
    "fps": 30,
    "height": 720,
    "width": 1280,
    "model": "openai:3@1",
    "numberResults": 1,
    "positivePrompt": "a cat",
    "taskUUID": "3f7fcfc4-e257-4cb7-bf97-439bceaa7cc3",
    "webhookURL": "https://openai-dev.chatfire.cn/sys/webhook/runware?expr=%24..taskUUID"
  }
]'
"""
