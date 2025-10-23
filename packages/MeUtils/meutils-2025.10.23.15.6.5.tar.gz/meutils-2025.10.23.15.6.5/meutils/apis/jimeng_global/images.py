#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : images
# @Time         : 2024/12/16 17:46
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
"""
guidance 控制精细度 => sample_strength 0-1 数值越大生成的效果质量越好，耗时会更久
 paths: ["/mweb/v1/generate", "/mweb/v1/super_resolution", "/mweb/v1/painting", "/commerce/v1/subscription/make_unauto_order", "/commerce/v1/benefits/credit_receive", "/commerce/v1/purchase/make_order", "/mweb/v1/get_explore", "/mweb/v1/feed_short_video", "/mweb/v1/feed", "/mweb/v1/get_homepage", "/mweb/v1/get_weekly_challenge_work_list", "/mweb/v1/mget_item_info", "/mweb/v1/get_item_info", "/mweb/v1/get_history_by_ids", "/mweb/search/v1/search"],

"""

from meutils.pipe import *
from meutils.caches import rcache

from meutils.decorators.retry import retrying
from meutils.notice.feishu import send_message_for_images

from meutils.schemas.jimeng_types import BASE_URL_GLOBAL as BASE_URL, MODELS_MAP, FEISHU_URL
from meutils.schemas.image_types import ImageRequest
from meutils.schemas.task_types import TaskResponse
from meutils.apis.jimeng.common import get_headers, check_token
from meutils.apis.jimeng.files import upload_for_image
from meutils.str_utils.regular_expression import parse_url

from meutils.config_utils.lark_utils import get_next_token_for_polling
from fastapi import status, HTTPException

from fake_useragent import UserAgent

ua = UserAgent()

VERSION = "3.2.5"


#
async def create_draft_content(request: ImageRequest, token: str):
    """
    创建草稿内容
    """
    # 参考人物
    face_recognize_data = request.controls.get("face_recognize_data", {})
    image_uri = face_recognize_data.pop("image_uri", None)

    request.model = MODELS_MAP.get(request.model, MODELS_MAP["default"])

    height = width = 1328
    if 'x' in request.size:
        width, height = map(int, request.size.split('x'))

    main_component_id = str(uuid.uuid4())
    if (urls := parse_url(request.prompt)) or image_uri:  # 图生  # todo: image base64
        request.model = "high_aes_general_v20_L:general_v2.0_L"  # 2.1不支持图片编辑 某些不支持

        if image_uri:
            pass

        else:
            url = urls[-1]
            image_uri = await upload_for_image(url, token)

            request.prompt = request.prompt.replace(url, '')

        component = {
            "type": "image_base_component",
            "id": main_component_id,
            "min_version": "3.0.2",
            "generate_type": "blend",
            "aigc_mode": "workbench",
            "abilities": {
                "type": "",
                "id": str(uuid.uuid4()),
                "blend": {
                    "type": "",
                    "id": str(uuid.uuid4()),
                    "core_param": {
                        "type": "",
                        "id": str(uuid.uuid4()),
                        "model": request.model,
                        "prompt": f"##{request.prompt}",
                        "sample_strength": 0.5,
                        "image_ratio": 1,
                        "large_image_info": {
                            "type": "",
                            "id": str(uuid.uuid4()),
                            "height": height,
                            "width": width,

                            # "resolution_type": "2k"
                        },
                    },
                    "ability_list": [
                        {
                            "type": "",
                            "id": str(uuid.uuid4()),
                            "name": "byte_edit",  # bg_paint face_gan
                            "image_uri_list": [
                                image_uri
                            ],
                            "image_list": [
                                {
                                    "type": "image",
                                    "id": str(uuid.uuid4()),
                                    "source_from": "upload",
                                    "platform_type": 1,
                                    "name": "",
                                    "image_uri": image_uri,
                                    "width": 0,
                                    "height": 0,
                                    "format": "",
                                    "uri": image_uri
                                }
                            ],

                            "strength": 0.5
                        }
                    ],
                    "history_option": {
                        "type": "",
                        "id": str(uuid.uuid4()),
                    },
                    "prompt_placeholder_info_list": [
                        {
                            "type": "",
                            "id": str(uuid.uuid4()),
                            "ability_index": 0
                        }
                    ],
                    "postedit_param": {
                        "type": "",
                        "id": str(uuid.uuid4()),
                        "generate_type": 0
                    }
                }
            }
        }

        if face_recognize_data:
            face_recognize_data['name'] = "face_gan"
            component["abilities"]["blend"]["ability_list"][0].update(face_recognize_data)

    else:  # 文生

        component = {
            "type": "image_base_component",
            "id": main_component_id,
            "min_version": "3.0.2",
            "generate_type": "generate",
            "aigc_mode": "workbench",
            # 国际版
            "metadata": {
                "type": "",
                "id": str(uuid.uuid4()),
                "created_platform": 3,
                "created_platform_version": "",
                "created_time_in_ms": f"{time.time() * 1000}//1",
                "created_did": ""
            },
            "abilities": {
                "type": "",
                "id": str(uuid.uuid4()),
                "generate": {
                    "type": "",
                    "id": str(uuid.uuid4()),
                    "core_param": {
                        "type": "",
                        "id": str(uuid.uuid4()),
                        "model": request.model,
                        "prompt": request.prompt,
                        "negative_prompt": request.negative_prompt or "",
                        "seed": request.seed or 1192648548,
                        "sample_strength": request.guidance or 0.5,  # 精细度
                        "image_ratio": 1,
                        "large_image_info": {
                            "type": "",
                            "id": str(uuid.uuid4()),
                            "height": height,
                            "width": width,

                            "resolution_type": "1k"
                        }
                    },
                    "history_option": {
                        "type": "",
                        "id": str(uuid.uuid4()),
                    }
                }
            }
        }
        component = {
            "type": "image_base_component",
            "id": main_component_id,
            "min_version": "3.0.2",
            "metadata": {
                "type": "",
                "id": "85295e81-9b68-fba4-6570-81fc96c4b76e",
                "created_platform": 3,
                "created_platform_version": "",
                "created_time_in_ms": "1749271549726",
                "created_did": ""
            },
            "generate_type": "generate",
            "aigc_mode": "workbench",
            "abilities": {
                "type": "",
                "id": "91c763e9-1574-162d-1e7a-3356200dbc00",
                "generate": {
                    "type": "",
                    "id": "3862c659-7761-841a-95a1-5d02b5326e72",
                    "core_param": {
                        "type": "",
                        "id": "fcbc04a9-26ba-c890-c753-39d2a0ff9ef7",
                        "model": "high_aes_general_v30l:general_v3.0_18b",
                        "prompt": "a dog",
                        "negative_prompt": "",
                        "seed": 1192648548,
                        "sample_strength": 0.5,
                        "image_ratio": 1,
                        "large_image_info": {
                            "type": "",
                            "id": "04242843-bfee-0584-9162-a611c5ff1b54",
                            "height": 1328,
                            "width": 1328,
                            "resolution_type": "1k"
                        }
                    },
                    "history_option": {
                        "type": "",
                        "id": "4e5867c5-06e9-c101-a1a8-bb972623d701"
                    }
                }
            }
        }

    draft_content = {
        "type": "draft",
        "id": str(uuid.uuid4()),
        "min_version": "3.0.2",
        "min_features": [],
        "is_from_tsn": True,
        "version": VERSION,
        "main_component_id": main_component_id,
        "component_list": [component]
    }
    logger.debug(draft_content)
    # logger.debug(bjson(draft_content))

    return draft_content


def key_builder(*args, **kwargs):
    logger.debug(args)
    logger.debug(kwargs)

    return args[1].prompt


@retrying()
@rcache(ttl=1 * 1 * 3600, serializer="pickle", key_builder=lambda *args, **kwargs: f"{args[1].seed} {args[1].prompt}")
async def create_task(request: ImageRequest, token: Optional[str] = None):  # todo: 图片
    token = token or await get_next_token_for_polling(FEISHU_URL, check_token)

    send_message_for_images(request, __name__)

    url = "/mweb/v1/aigc_draft/generate"

    headers = get_headers(url, token)

    if "http" in request.prompt:  # 图生
        request.model = "high_aes_general_v20_L:general_v2.0_L"

    draft_content = await create_draft_content(request, token)

    logger.debug(json.dumps(draft_content))

    payload = {
        "extend": {
            "root_model": request.model,
            "template_id": ""
        },
        "submit_id": str(uuid.uuid4()),
        "metrics_extra": "{\"templateId\":\"\",\"generateCount\":1,\"promptSource\":\"custom\",\"templateSource\":\"\",\"lastRequestId\":\"\",\"originRequestId\":\"\"}",
        "draft_content": json.dumps(draft_content),
        # "http_common_info": {
        #     "aid": 513695
        # }
    }
    # logger.debug(bjson(payload))
    # payload = {"extend": {"root_model": "high_aes_general_v30l:general_v3.0_18b", "template_id": ""},
    #            "submit_id": "6e356f64-2bc3-45c7-83b6-64371bac9b64",
    #            "metrics_extra": "{\"templateId\":\"\",\"generateCount\":1,\"promptSource\":\"custom\",\"templateSource\":\"\",\"lastRequestId\":\"\",\"originRequestId\":\"\"}",
    #            "draft_content": "{\"type\":\"draft\",\"id\":\"0a47b141-8c2a-f4ce-ae51-5670688d3fdf\",\"min_version\":\"3.0.2\",\"min_features\":[],\"is_from_tsn\":true,\"version\":\"3.2.5\",\"main_component_id\":\"d7cf2d3f-db61-9775-2970-b3be2c193a71\",\"component_list\":[{\"type\":\"image_base_component\",\"id\":\"d7cf2d3f-db61-9775-2970-b3be2c193a71\",\"min_version\":\"3.0.2\",\"metadata\":{\"type\":\"\",\"id\":\"85295e81-9b68-fba4-6570-81fc96c4b76e\",\"created_platform\":3,\"created_platform_version\":\"\",\"created_time_in_ms\":\"1749271549726\",\"created_did\":\"\"},\"generate_type\":\"generate\",\"aigc_mode\":\"workbench\",\"abilities\":{\"type\":\"\",\"id\":\"91c763e9-1574-162d-1e7a-3356200dbc00\",\"generate\":{\"type\":\"\",\"id\":\"3862c659-7761-841a-95a1-5d02b5326e72\",\"core_param\":{\"type\":\"\",\"id\":\"fcbc04a9-26ba-c890-c753-39d2a0ff9ef7\",\"model\":\"high_aes_general_v30l:general_v3.0_18b\",\"prompt\":\"a dog\",\"negative_prompt\":\"\",\"seed\":1192648548,\"sample_strength\":0.5,\"image_ratio\":1,\"large_image_info\":{\"type\":\"\",\"id\":\"04242843-bfee-0584-9162-a611c5ff1b54\",\"height\":1328,\"width\":1328,\"resolution_type\":\"1k\"}},\"history_option\":{\"type\":\"\",\"id\":\"4e5867c5-06e9-c101-a1a8-bb972623d701\"}}}}]}"}

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        logger.debug(bjson(data))

    # {
    #     "ret": "1000",
    #     "errmsg": "invalid parameter",
    #     "systime": "1744354538",
    #     "logid": "20250411145538E30D2FF8347A9A710F49",
    #     "data": {
    #         "aigc_data": null,
    #         "fail_code": "",
    #         "fail_starling_key": "",
    #         "fail_starling_message": ""
    #     }
    # }

    aigc_data = (data.get("data") or {}).get("aigc_data") or {}

    logger.debug(bjson(aigc_data))

    if task_id := aigc_data.get("history_record_id"):  # bug
        return TaskResponse(task_id=task_id, system_fingerprint=token)
    else:

        # {
        #     "ret": "1018",
        #     "errmsg": "account punish limit ai generate",
        #     "systime": "1737962056",
        #     "logid": "202501271514162E3DA8ECD70A3EE1400F",
        #     "data": null
        # }

        raise HTTPException(
            status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
            detail=f"可能触发内容审核，请联系管理员：{data.get('errmsg')}"
        )


@retrying(max_retries=3, min=3)
async def get_task(task_id, token):
    url = "/mweb/v1/get_history_by_ids"
    headers = get_headers(url, token)

    payload = {
        "history_ids": [
            task_id
        ]
    }

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

        logger.debug(response.text)

        task_info = {}
        if response.text:
            data = response.json()
            logger.debug(bjson(data))
            task_info = (data.get("data") or {}).get(task_id, {})
        else:
            logger.debug("走 /mweb/v1/get_history")

            data = await get_task_plus(task_id, token)

            records_list = (data.get("data") or {}).get("records_list", [])

            for record in records_list:
                if record.get("history_record_id") == task_id:
                    task_info = record

        # {'ret': '1015', 'errmsg': 'login error', 'systime': '1734524280', 'logid': '20241218201800AC3267447B287E9E6C46', 'data': None}
        item_list = task_info.get("item_list", [])  # "status": 30,

        status_code = task_info.get("status")
        fail_msg = f"""{task_info.get("fail_msg")}"""

        logger.debug(f"status: {status_code}")

        # 敏感词存储
        # if status_code != 50:
        #     send_message_for_images(task_info, __name__)

        """
        "status": 30, # 内容审核
        "status": 50,
        """

        image_data = map(lambda x: x.get("image", {}).get("large_images", []), item_list)

        task_data = sum(image_data, []) | xmap_(lambda x: {"url": x.get("image_url")})

        response = TaskResponse(
            task_id=task_id,
            data=task_data,
            message=data.get("errmsg"),
            status="success" if item_list else 'processing',
            code=status_code,
        )

        if status_code == 30:
            response.status = "fail"
            response.message = fail_msg

        return response


@retrying(max_retries=3, min=3)
async def get_task_plus(task_id, token):
    url = "/mweb/v1/get_history"
    headers = get_headers(url, token)

    params = {
        "aid": 513695,
        "da_version": "3.2.2",
        "aigc_features": "app_lip_sync",
    }

    payload = {
        "count": 20,
        "history_type_list": [
            1,
            4,
            5,
            6,
            7,
            8
        ],
        "direction": 1,
        "mode": "workbench",
        "image_info": {
            "width": 2048,
            "height": 2048,
            "format": "webp",
            "image_scene_list": [
                {
                    "scene": "smart_crop",
                    "width": 240,
                    "height": 240,
                    "uniq_key": "smart_crop-w:240-h:240",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 320,
                    "height": 320,
                    "uniq_key": "smart_crop-w:320-h:320",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 480,
                    "height": 480,
                    "uniq_key": "smart_crop-w:480-h:480",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 480,
                    "height": 320,
                    "uniq_key": "smart_crop-w:480-h:320",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 240,
                    "height": 160,
                    "uniq_key": "smart_crop-w:240-h:160",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 160,
                    "height": 213,
                    "uniq_key": "smart_crop-w:160-h:213",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 320,
                    "height": 427,
                    "uniq_key": "smart_crop-w:320-h:427",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 1080,
                    "height": 1080,
                    "uniq_key": "1080",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 900,
                    "height": 900,
                    "uniq_key": "900",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 720,
                    "height": 720,
                    "uniq_key": "720",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 480,
                    "height": 480,
                    "uniq_key": "480",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 360,
                    "height": 360,
                    "uniq_key": "360",
                    "format": "webp"
                },
                {
                    "scene": "normal",
                    "width": 2400,
                    "height": 2400,
                    "uniq_key": "2400",
                    "format": "webp"
                }
            ]
        },
        "origin_image_info": {
            "width": 96,
            "format": "webp",
            "image_scene_list": [
                {
                    "scene": "smart_crop",
                    "width": 240,
                    "height": 240,
                    "uniq_key": "smart_crop-w:240-h:240",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 320,
                    "height": 320,
                    "uniq_key": "smart_crop-w:320-h:320",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 480,
                    "height": 480,
                    "uniq_key": "smart_crop-w:480-h:480",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 480,
                    "height": 320,
                    "uniq_key": "smart_crop-w:480-h:320",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 240,
                    "height": 160,
                    "uniq_key": "smart_crop-w:240-h:160",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 160,
                    "height": 213,
                    "uniq_key": "smart_crop-w:160-h:213",
                    "format": "webp"
                },
                {
                    "scene": "smart_crop",
                    "width": 320,
                    "height": 427,
                    "uniq_key": "smart_crop-w:320-h:427",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 1080,
                    "height": 1080,
                    "uniq_key": "1080",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 900,
                    "height": 900,
                    "uniq_key": "900",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 720,
                    "height": 720,
                    "uniq_key": "720",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 480,
                    "height": 480,
                    "uniq_key": "480",
                    "format": "webp"
                },
                {
                    "scene": "loss",
                    "width": 360,
                    "height": 360,
                    "uniq_key": "360",
                    "format": "webp"
                },
                {
                    "scene": "normal",
                    "width": 2400,
                    "height": 2400,
                    "uniq_key": "2400",
                    "format": "webp"
                }
            ]
        },
        "history_option": {
            "story_id": "",
            "multi_size_image_config": [
                {
                    "height": 100,
                    "width": 100,
                    "format": "webp"
                },
                {
                    "height": 360,
                    "width": 360,
                    "format": "webp"
                },
                {
                    "height": 720,
                    "width": 720,
                    "format": "webp"
                }
            ]
        },
        "is_pack_origin": True
    }

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.post(url, json=payload, params=params)
        response.raise_for_status()

        return response.json()


# @cache: todo: cache 积分异常消耗
# @cache(ttl=3600)
async def generate(request: ImageRequest):
    # logger.debug(request)

    task_response = await create_task(request)

    for i in range(1, 15):
        await asyncio.sleep(max(15 / i, 5))
        response = await get_task(task_response.task_id, task_response.system_fingerprint)
        logger.debug(f"{task_response.task_id, task_response.system_fingerprint}")
        logger.debug(response)
        if response.status.lower().startswith("fail"):
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail=response.message
            )

        if data := response.data:
            return {"data": data}


if __name__ == '__main__':
    # token = "eb4d120829cfd3ee957943f63d6152ed"
    token = "176b9aba6b81256b50abf08526cf311a"
    token = "7fdb556cbd1d01ba3e4a64eb0203d49d"
    image_url = "https://oss.ffire.cc/files/kling_watermark.png"

    # request = ImageRequest(prompt="做一个圣诞节的海报", size="1024x1024")
    # request = ImageRequest(prompt="https://oss.ffire.cc/files/kling_watermark.png 让她带上墨镜", size="1024x1024")

    # task = arun(create_task(request))

    # task_id = "10040025470722"

    # task_id = "10053536381698"

    # task_id = "10079694738434"

    # task_id = "10080831230210"  # 图片编辑

    # task_id = "10082971040514"
    #
    # arun(get_task(task_id, token))

    # arun(get_task(task.task_id, task.system_fingerprint))

    # task_id = "10184295086338"
    # system_fingerprint = "eb4d120829cfd3ee957943f63d6152ed"
    #
    # t1 = ("10184295086338", "eb4d120829cfd3ee957943f63d6152ed")
    # t2 = ("10184877310722", "dcf7bbc31faed9740b0bf748cd4d2c74")
    # t3 = ("10186352959490", "eb4d120829cfd3ee957943f63d6152ed")
    #
    # arun(get_task(*t3))

    from meutils.apis.jimeng.files import face_recognize

    # face_recognize = arun(face_recognize(image_url, token))
    #
    # face_recognize_data = face_recognize.get("data", {})

    # arun(generate(ImageRequest(**data)))

    # arun(generate(ImageRequest(prompt="fuck you")))
    # prompt = "A plump Chinese beauty wearing a wedding  dress revealing her skirt and underwear is swinging on the swing,Happy smile,cleavage,Exposed thighs,Spread your legs open,Extend your leg,panties,upskirt,Barefoot,sole"
    prompt = "  a dog cat in the same room       "
    # prompt = "https://oss.ffire.cc/files/kling_watermark.png 让这个女人带上墨镜，衣服换个颜色... ! "
    request = ImageRequest(prompt=prompt, size="1328x1328")
    # request = ImageRequest(prompt=prompt, size="1024x1024")

    # request = ImageRequest(prompt=prompt, size="2048*2048")

    task = arun(create_task(request, token))
    # task = arun(create_task(request, "d2d142fc877e696484cc2fc521127b36"))
    # task = arun(create_task(request, "d2d142fc877e696484cc2fc521127b36"))

    # arun(get_task(task.task_id, task.system_fingerprint))
    # arun(get_task_plus(task.task_id, task.system_fingerprint))
    # arun(get_task('16279716197378', 'd2d142fc877e696484cc2fc521127b36'))
    # arun(get_task_plus('16279716197378', 'd2d142fc877e696484cc2fc521127b36'))

    # TaskResponse(task_id='16127190069506', code=0, message=None, status='SUBMITTED', data=None,
    #              system_fingerprint='8089661372fe8db9795cc507c3049625', model=None,
    #              created_at='2025-05-06T19:49:50.933089')

    # arun(get_task("47185525857809", token))

    # arun(generate(request))
