#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2024/10/21 20:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://platform.minimaxi.com/document/video_generation?key=66d1439376e52fcee2853049
# https://useapi.net/docs/start-here/setup-minimax
# token 过期时间一个月: 看下free hailuo
# https://jwt.io/

# todo: check token

import oss2

from meutils.pipe import *
from meutils.hash_utils import md5
from meutils.io.files_utils import to_bytes
from meutils.jwt_utils import decode_jwt_token
from meutils.str_utils.json_utils import json_path

from meutils.schemas.image_types import ImageRequest, ImagesResponse

from meutils.schemas.hailuo_types import BASE_URL, FEISHU_URL
# from meutils.schemas.hailuo_types import BASE_URL_ABROAD as BASE_URL, FEISHU_URL_ABROAD as FEISHU_URL
from meutils.schemas.hailuo_types import BASE_URL_ABROAD
from meutils.schemas.hailuo_types import VideoRequest, VideoResponse
from meutils.llm.check_utils import check_tokens
from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.decorators.retry import retrying
from meutils.notice.feishu import send_message as _send_message, VIDEOS

from meutils.apis.hailuoai.yy import get_yy

send_message = partial(
    _send_message,
    title=__name__,
    url=VIDEOS
)

MODEL_MAPPING = {
    # video-01 video-01 video-01-live2d S2V-01

    "t2v-01": "23000",  # 23010
    "t2v-01-director": "23010",

    "i2v-01": "23001",
    "i2v-01-live": "23011",
    "video-01-live2d": "23011",
    "s2v-01": "23021",
}


def get_base_url(token):
    data = decode_jwt_token(token)
    if "小螺帽" not in str(data):
        logger.debug(data)

        return BASE_URL_ABROAD
    else:
        return BASE_URL


# minimax_video-01,minimax_video-01-live2d,,minimax_t2v-01,minimax_i2v-01,minimax_i2v-01-live,minimax_s2v-01


async def upload(file: bytes, token: str):
    data = await get_request_policy(token)

    access_key_id = data["accessKeyId"]
    access_key_secret = data["accessKeySecret"]
    security_token = data["securityToken"]
    bucket_name = data["bucketName"]
    endpoint = data["endpoint"]
    dir = data["dir"]

    # 创建OSS客户端    with timer():
    #         arun(hailuo_upload(file))
    auth = oss2.StsAuth(access_key_id, access_key_secret, security_token)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    # file
    size = len(file)

    # 要上传的文件路径和文件名
    mimeType = "png"
    filename = f"{uuid.uuid4()}.{mimeType}"
    object_name = f"{dir}/{filename}"  # png写死
    bucket.put_object(object_name, file)

    params = {}
    payload = {
        "originFileName": "_.png",
        # "originFileName": "503af3b5-9c3b-4bdc-a6d4-256debce3dd5_00001_.png",

        "filename": filename,
        # "fileName": "db884a7c-99a4-40f5-929e-db8769dbf64a.png",

        "dir": dir,
        "endpoint": "oss-cn-wulanchabu.aliyuncs.com",
        "bucketName": "minimax-public-cdn",
        "size": f"{size}",
        "mimeType": mimeType,
        "fileMd5": md5(file),
        "fileScene": 10
    }
    headers = {
        'token': token
    }
    logger.debug(headers)

    BASE_URL = get_base_url(token)
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=120) as client:
        response = await client.post("/v1/api/files/policy_callback", params=params, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.debug(bjson(data))
        return data

    # {'data': {'fileID': '307139766909288449',
    #           'ossPath': 'https://cdn.hailuoai.com/prod/2024-10-28-10/user/multi_chat_file/c9d8fc64-d9bf-42c0-8779-f39973579fca.png?image_process=resize,fw_320/format,webp'},
    #  'statusInfo': {'code': 0,
    #                 'debugInfo': '',
    #                 'httpCode': 0,
    #                 'message': '成功',
    #                 'requestID': '33a42a75-15e5-4d4e-b425-eeefc4d3f374',
    #                 'serverAlert': 0,
    #                 'serviceTime': 1730083971}}


@alru_cache(ttl=1 * 24 * 60 * 60)
@retrying()
async def get_access_token(token: str):
    BASE_URL = get_base_url(token)
    logger.debug(BASE_URL)

    logger.debug(f"get_access_token:{token}")

    params = {
        'device_platform': 'web',
        'app_id': '3001',
        'version_code': '22201',
        'uuid': '8c059369-00bf-4777-a426-d9c9b7984ee6',
        'device_id': '243713252545986562',
        'os_name': 'Mac',
        'browser_name': 'chrome',
        'device_memory': '8',
        'cpu_core_num': '10',
        'browser_language': 'zh-CN',
        'browser_platform': 'MacIntel',
        'screen_width': '1920',
        'screen_height': '1080',
        'unix': f'{int(time.time())}000'
    }
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'token': token,
        'yy': get_yy(payload, params=params, url="/v1/api/user/renewal")
    }

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.post("/v1/api/user/renewal", params=params, content=json.dumps(payload))
        response.raise_for_status()
        logger.debug(response.json())
        return response.json()['data']['token']


@alru_cache(ttl=1 * 60)
async def get_request_policy(token):
    """
    {
        "data": {
            "accessKeyId": "STS.NUVNbdQfqTNixCxUTAhdeJToq",
            "accessKeySecret": "DRBsh8Qm8VnXXxTwFMX5KkXVoqbbsPj4ewEfgTLysGvM",
            "securityToken": "CAISiwN1q6Ft5B2yfSjIr5bjBdjQvLlQ44yCemXJsVQUZOtJpZHEkzz2IHhMf3VpAusWsPw1n2tT6/sdlrBoS4JMREPJN5EhtsQLrl75PdKY4Jzltedb0EIf6JFQUUyV5tTbRsmkZj+0GJ70GUem+wZ3xbzlD2vAO3WuLZyOj7N+c90TRXPWRDFaBdBQVH0AzcgBLinpKOqKOBzniXayaU1zoVhYiHhj0a2l3tbmvHi4tlDhzfIPrIncO4Wta9IWXK1ySNCoxud7BOCjmCdb8EpN77wkzv4GqzLGuNCYCkkU+wiMN+vft9ZjKkg7RNBjSvMa8aWlzKYn57OCyt2v8XsXY7EJCRa4bZu73c7JFNmuMtsEbrvhMxzPqIvXbsKp6lh/MSxDblgRIId8dWURExUpTSrBIaOh6M4Bo5NbzHzuOsgSpnkVpz2AlbLiT9M/1aieRiRTcymwO/ayjeq6CeAF3mM8Mm0qPRouTM2+Zo5YD3N1opjTpiapdUYLox8awbuQLp25tMiF6FiLDvouuRqAAQJZHVcOeb5qnR6mkzw5hwzSOXoMXVFzDE2aB7dvRYFD9HiG6T66hE4Xlfpph9H7xWrpaBf5vqHQXp4gyuqVOgFIjdPECwisXlyAKQWMak7bGToh3cetCux3pjq74sP/KAjzSzDkwciJBbn8vZzNKKR/ozxqve925vtPPPWGPowwIAA=",
            "expiration": "2024-10-22T02:55:14Z",
            "dir": "cdn-yingshi-ai-com/prod/2024-10-22-09/user/multi_chat_file",
            "endpoint": "oss-cn-wulanchabu.aliyuncs.com",
            "bucketName": "minimax-public-cdn",
            "serverTime": "2024-10-22T02:10:07Z"
        }
    }
    """
    token = await get_access_token(token)

    headers = {
        'token': token,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }

    logger.debug(headers)

    BASE_URL = get_base_url(token)

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.get("/v1/api/files/request_policy")
        response.raise_for_status()
        return response.json()['data']
    # return {'accessKeyId': 'STS.NTjAXdazuDwvBugixueiNTwvW',
    #         'accessKeySecret': '4Uj1cuUQt2Xxnr21Yv41CUfGjnH8wBM3SB2Hn9sNrdDS',
    #         'bucketName': 'hailuo-video',
    #         'dir': 'moss/prod/2024-11-08-18/user/multi_chat_file',
    #         'endpoint': 'oss-us-east-1.aliyuncs.com',
    #         'expiration': '2024-11-08T11:38:31Z',
    #         'securityToken': 'CAISjwN1q6Ft5B2yfSjIr5ffCuLQjKVU87WdQFPWjXggaeZiu7LdtTz2IHhMe3lrB+kZsvo0lGFR5vcelrBoS4JMREPJNpMvv8UGq1LxMtKZ45PtseRZ0Fx+t9xLUUyV5tTbRsmkZsW/E67fejKpvyt3xqSAK1fGdle5MJqPpId6Z9AMJGeRZiZHA9EkUGkHr9QBZ0PMKdGnMBPhngi1C1Fz6C59kn9H4L6j2bfMiHzkgUb91/UeqqnoP5GgdLMMBppkVMqv1+EEAsiz2SVLuR9R7/U03u4W+T7GusyaRkdQ7xiBdKj2ioAzcFQhP/JmRfUe86Ghy6JC17aNx9Sn+XFkJvpIVinTfoekzfbfFfmhXtRDLu6jZCSWjInQaseu41J9MSNHLnNDY9tkMWNrTBs3UXTaI66j5VePfAavRq+VN3TYejPRcjQClPr9xDjnK93xuU5wsa8t6v7tUjA8KaFMoG7n3kGenWkdc5K/Z6udEt4wZ+3GM2OsuFNOQI8ZwZ+aRbfi3op7DyGXmSCG59Z1DPwagAF6Ybpx1FU5RRhp1G6yFZrwSz1uWkDL+5K5SYiq9g758m0ElogR5mgmkISgo2qy8/2br2XEA4eyRt5iIHSVX+lLrE2DIv4Cd65nZSQWX8G+av0D5qxCmspJEz3+VL4kdSxT42GuFpu9jhUtWLAX4K/5laoNyKR5LJHtZR3/pteBSCAA',
    #         'serverTime': '2024-11-08T10:38:31Z'}


@retrying(predicate=lambda r: r.base_resp.status_code in {1000061, 1500009})  # 限流
async def create_task(request: ImageRequest, token: Optional[str] = None):
    refresh_token = token or await get_next_token_for_polling(FEISHU_URL, from_redis=True, check_token=check_token)
    BASE_URL = get_base_url(refresh_token)

    token = refresh_token
    # token = await get_access_token(refresh_token) ##########

    payload = {
        "desc": request.prompt,
        "useOriginPrompt": False,
        "fileList": [],
        "modelID": request.model.removeprefix("hailuo-"),  # hailuo- "image-01"
        "quantity": f"{request.n}",
        "aspectRatio": request.aspect_ratio or "1:1",
    }

    if request.prompt.startswith("http"):
        url = request.prompt.split(maxsplit=1)[0]

        data = await upload(await to_bytes(url), token=refresh_token)

        file_data = {
            "id": data['data']['fileID'],
            "name": "_.png",
            "type": "png",
            "url": data['data']['ossPath'],

            # "characterID": "334024935389642756"

        }

        payload["fileList"].append(file_data)
        payload['desc'] = request.prompt.replace(url, " ")

    logger.debug(bjson(payload))

    params = {
        'device_platform': 'web',
        'app_id': '3001',
        'version_code': '22202',
        'biz_id': '0',
        'uuid': '8c059369-00bf-4777-a426-d9c9b7984ee6',
        'device_id': '243713252545986562',
        'os_name': 'Mac',
        'browser_name': 'chrome',
        'device_memory': '8',
        'cpu_core_num': '10',
        'browser_language': 'zh-CN',
        'browser_platform': 'MacIntel',
        'screen_width': '1920',
        'screen_height': '1080',
        'unix': f'{int(time.time())}000'
    }

    path = "/v1/api/multimodal/generate/image"
    headers = {
        'Content-Type': 'application/json',
        'token': token,
        'yy': get_yy(payload, params, url=path),
    }
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.post(path, params=params, content=json.dumps(payload))
        response.raise_for_status()

        data = response.json()

        logger.debug(bjson(data))

        task_id = (data.get('data') or {}).get('id', '')
        response = VideoResponse(
            task_id=f"hailuoai-{task_id}",
            base_resp=data.get('statusInfo', {}),
            system_fingerprint=refresh_token
        )
        if response.base_resp.status_code != 0:  # 451
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                                detail=response.base_resp)

        return response


async def get_task(task_id: str, token: str):
    BASE_URL = get_base_url(token)

    task_id = task_id.rsplit('-', 1)[-1]

    params = {
        'device_platform': 'web',
        'app_id': '3001',
        'version_code': '22202',
        'biz_id': '0',
        'uuid': '8c059369-00bf-4777-a426-d9c9b7984ee6',
        'device_id': '243713252545986562',
        'os_name': 'Mac',
        'browser_name': 'chrome',
        'device_memory': '8',
        'cpu_core_num': '10',
        'browser_language': 'zh-CN',
        'browser_platform': 'MacIntel',
        'screen_width': '1920',
        'screen_height': '1080',
        'unix': f'{int(time.time())}000',
    }

    payload = {
        "batchInfoList": [{"batchID": task_id, "batchType": 1}]
    }

    path = "/v4/api/multimodal/video/processing"
    # path = "/api/multimodal/video/processing"

    headers = {
        'Content-Type': 'application/json',
        'token': token,
        'yy': get_yy(payload, params, url=path),
    }

    logger.debug(headers['yy'])

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        response = await client.post("/v4/api/multimodal/video/processing", params=params, content=json.dumps(payload))
        response.raise_for_status()
        data = response.json()

        logger.debug(bjson(data))

        urls = json_path(data, "$..downloadURL") or []

        return urls


@alru_cache(ttl=3600)
async def check_token(token, threshold: int = 30, **kwargs):
    BASE_URL = get_base_url(token)

    if not isinstance(token, str):
        return await check_tokens(token, check_token)

    try:
        token = await get_access_token(token)
        headers = {
            "token": token
        }
        params = {}
        async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
            response = await client.get("/v1/api/user/equity", params=params)
            response.raise_for_status()
            data = response.json()

            logger.debug(bjson(data))

            return "Unlimited" in str(data) or "高级会员" in str(data)  # Unlimited
    except Exception as e:
        logger.error(e)
        logger.debug(token)
        return False


async def generate(request: ImageRequest):
    task_response = await create_task(request)
    for i in range(1, 10):
        await asyncio.sleep(max(10 / i, 1))
        if urls := await get_task(task_response.task_id, task_response.system_fingerprint):
            logger.debug(urls)

            return ImagesResponse(data=[{"url": url} for url in urls])


if __name__ == '__main__':  # 304752356930580482
    vip = True
    # vip = False
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI5NzAyMjIsInVzZXIiOnsiaWQiOiIyNDM3MTMyNTI3OTc2NDA3MDgiLCJuYW1lIjoi5bCP6J665bi9NzA4IiwiYXZhdGFyIjoiaHR0cHM6Ly9jZG4ueWluZ3NoaS1haS5jb20vcHJvZC91c2VyX2F2YXRhci8xNzA2MjY3MzY0MTY0NDA0MDc3LTE3MzE5NDU3MDY2ODk2NTg5Nm92ZXJzaXplLnBuZyIsImRldmljZUlEIjoiMjQzNzEzMjUyNTQ1OTg2NTYyIiwiaXNBbm9ueW1vdXMiOnRydWV9fQ.X3KW00hAhSMk1c7DrXWYR27BROHNbfSiHD7Y-aweA6o"
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM1NjMzNTIsInVzZXIiOnsiaWQiOiIyMjkwODQ3NTA2MDEzODgwMzciLCJuYW1lIjoi5bCP6J665bi9ODAzNyIsImF2YXRhciI6Imh0dHBzOi8vY2RuLnlpbmdzaGktYWkuY29tL3Byb2QvdXNlcl9hdmF0YXIvMTcwNjI2NzcxMTI4Mjc3MDg3Mi0xNzMxOTQ1NzA2Njg5NjU4OTZvdmVyc2l6ZS5wbmciLCJkZXZpY2VJRCI6IjMwNzIzNzc4MjU1NjE0NzcxMyIsImlzQW5vbnltb3VzIjpmYWxzZX19.MzZA9tW0YG2WFRWSkdD6bpEQt_0I-uIrxPJjxisKRNk"
    # 海外
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM4MDQwOTksInVzZXIiOnsiaWQiOiIzMDc5OTkyOTg5MDAwNzA0MDUiLCJuYW1lIjoiRGF2aWQgUGhpbGxpcHMiLCJhdmF0YXIiOiIiLCJkZXZpY2VJRCI6IiJ9fQ.wmmDC7XBmmlQvcPM5TpdGVQDQDIkMpF9nkYBSB7UBWw"
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM1NjQ5NDYsInVzZXIiOnsiaWQiOiIzMDQ3NjQzOTU5NDEwOTMzNzYiLCJuYW1lIjoiTWFyaWEiLCJhdmF0YXIiOiIiLCJkZXZpY2VJRCI6IiJ9fQ.QYLSWMj85hB43blHcrfSNBYJ2v_gFmQO9DmIYC5sVuQ"

    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM1NDgxMzUsInVzZXIiOnsiaWQiOiIzMDI4MzM4Njc3NzE5NDkwNTgiLCJuYW1lIjoibWUgYmV0dGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSWdTU0NoczFENHNUajFTVGs3UHNUbTd5NTNKRFg5OW84QnhwWmNWNjU2MEFKYlJnPXM5Ni1jIiwiZGV2aWNlSUQiOiIifX0.b8lAlOd961nVrJunpW9tRAEETe6VwlEXvf7y2faNCeY"
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM0MDY1MzUsInVzZXIiOnsiaWQiOiIzMDI4MzM4Njc3NzE5NDkwNTgiLCJuYW1lIjoibWUgYmV0dGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSWdTU0NoczFENHNUajFTVGs3UHNUbTd5NTNKRFg5OW84QnhwWmNWNjU2MEFKYlJnPXM5Ni1jIiwiZGV2aWNlSUQiOiIifX0.mcozMacSciz0MORdleOMS_uhrixhIlpQmFmUwvn81I4"
    # arun(get_access_token(token, vip=vip))
    # arun(get_request_policy(token, vip=vip))
    # arun(get_access_token(vip=False))

    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM4MDQwOTksInVzZXIiOnsiaWQiOiIzMDc5OTkyOTg5MDAwNzA0MDUiLCJuYW1lIjoiRGF2aWQgUGhpbGxpcHMiLCJhdmF0YXIiOiIiLCJkZXZpY2VJRCI6IiJ9fQ.wmmDC7XBmmlQvcPM5TpdGVQDQDIkMpF9nkYBSB7UBWw"

    # p = "/Users/betterme/PycharmProjects/AI/MeUtils/meutils/data/cowboy-hat-face.webp"
    # arun(upload(Path(p).read_bytes(), token=token, vip=vip))
    # arun(upload(Path(p).read_bytes(), vip=False))
    # access_token = arun(get_access_token())
    # arun(upload(Path("img.png").read_bytes(), token=access_token))
    # arun(upload(Path("img.png").read_bytes(), token=access_token))

    # arun(get_task(task_id="307137575113703427", token=token)) # 307173162217783304
    # arun(get_task(task_id="307148849188945924", token=token))

    # arun(get_task(task_id="307267574751313927", token=token))

    # arun(get_task(task_id="307177115102699528", token=token))

    token = None
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDQ3MDMwNzIsInVzZXIiOnsiaWQiOiIzMDI4MzM4Njc3NzE5NDkwNTgiLCJuYW1lIjoibWUgYmV0dGVyIiwiYXZhdGFyIjoiIiwiZGV2aWNlSUQiOiIzMDI4MzM3NTk1MTI3NjQ0MTciLCJpc0Fub255bW91cyI6ZmFsc2V9fQ.Mjb64ZjkKyV9pj-_bXyLczU6kU729VLaKbYj9NmrK-4"
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDg3Mzg4MTQsInVzZXIiOnsiaWQiOiIyMjkwODQ3NTA2MDEzODgwMzciLCJuYW1lIjoi5bCP6J665bi9ODAzNyIsImF2YXRhciI6Imh0dHBzOi8vY2RuLmhhaWx1b2FpLmNvbS9wcm9kL3VzZXJfYXZhdGFyLzE3MDYyNjc3MTEyODI3NzA4NzItMTczMTk0NTcwNjY4OTY1ODk2b3ZlcnNpemUucG5nIiwiZGV2aWNlSUQiOiIyNDM3MTMyNTI1NDU5ODY1NjIiLCJpc0Fub255bW91cyI6ZmFsc2V9fQ.o0SoZMSTWkXNHxJjt3Ggby5MJWSfd-rnK_I95T_WMP8"
    request = ImageRequest(
        model="hailuo-image-01",

        prompt="a cat",  # 307145017365086216
        # prompt="https://oss.ffire.cc/files/kling_watermark.png 哭起来",
        # first_frame_image="https://oss.ffire.cc/files/kling_watermark.png"  # 307173162217783304
    )

    # r = arun(create_task(request, token=token))
    # arun(get_task(task_id=r.task_id, token=r.system_fingerprint))

    # arun(get_access_token(token))

    # arun(generate(request))
    #
    #
    # data = {
    #     "model": "video-01",
    #     "prompt": "画面中两个人非常缓慢地拥抱在一起",
    #     "prompt_optimizer": True,
    #     # "first_frame_image": "https://hg-face-domestic-hz.oss-cn-hangzhou.aliyuncs.com/avatarapp/ai-cache/54883340-954c-11ef-8920-db8e7bfa3fdf.jpeg"
    # }
    # request = VideoRequest(**data)
    # r = arun(create_task(request, vip=vip))
    # arun(get_task(task_id=r.task_id, token=r.system_fingerprint))

    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Mzg0Njk5MTUsInVzZXIiOnsiaWQiOiIzMjY0MzI4MjI3OTYxMzY0NTYiLCJuYW1lIjoiRGVib3JhaCBNaWxsZXIiLCJhdmF0YXIiOiIiLCJkZXZpY2VJRCI6IjMxMzMxNTk1MzEwMDQxMDg4NyIsImlzQW5vbnltb3VzIjpmYWxzZX19.ZnpAgRPwtc4JZ2B0PbEfgMU_I4_YRtifzNRVHa5g90U"

    # arun(get_task("hailuoai-307495165395488768", token=token))
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzUwMTc3ODAsInVzZXIiOnsiaWQiOiIzMTEyOTUzMTkzMjc1NzYwNjQiLCJuYW1lIjoiVUdIUiBKVkJYIiwiYXZhdGFyIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS3RuR2NjdGZsWV9fR2tiQ1MzdnhzSXdWSEFUX0ZmMFdyb3RvMnN4bFdWZW1KMm53PXM5Ni1jIiwiZGV2aWNlSUQiOiIzMTMzMTU5NTMxMDA0MTA4ODciLCJpc0Fub255bW91cyI6ZmFsc2V9fQ.cyZifq4FQl46P5_acTNT04qu2GVDDeSBbwjw3J1vWPo"
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzUwMzQ1MjcsInVzZXIiOnsiaWQiOiIzMTMzODk5MjA0NjA5MzkyNjgiLCJuYW1lIjoiY2l4ZiB4YmNnIiwiYXZhdGFyIjoiIiwiZGV2aWNlSUQiOiIzMTM0MDgyMjg0NTEwOTg2MjYiLCJpc0Fub255bW91cyI6ZmFsc2V9fQ.eOtAUe3MmarOGNk64j0bfaLNBZ4yxkqwIi1tUhOFD5c"
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTAxMjg4NTIsInVzZXIiOnsiaWQiOiIzNzQwMTM3NzUyNzg4ODY5MTciLCJuYW1lIjoiTmFodWVsIE1vbGluYSIsImF2YXRhciI6IiIsImRldmljZUlEIjoiMzEzMzc0MTIyMjEyMjc4MjczIiwiaXNBbm9ueW1vdXMiOmZhbHNlfX0.uxTtDTcPT07piVA-x3N2ms2VrRN3JwcU99g_HJLwqLE"
    arun(check_token(token))
