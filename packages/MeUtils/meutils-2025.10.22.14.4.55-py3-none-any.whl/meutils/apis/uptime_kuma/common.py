#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : commom
# @Time         : 2024/11/26 15:44
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *

from uptime_kuma_api import UptimeKumaApi, MonitorType

with UptimeKumaApi('https://status.chatfire.cn/') as api:
    # _ = api.login('chatfire', 'chatfirechatfire!')
    _ = api.login_by_token(token="uk2_IwihsMXDSMDJ2FswTbJoO1BJcz2SL2x08JZHHyxK")
    print(_)
    # print(api.get_monitors())
    #
    # api.delete_monitor(21)
    # result = api.add_monitor(
    #     type=MonitorType.HTTP,
    #     method="POST",
    #     name="gpt-3.5-turbo",
    #     url="https://api.chatfire.cn/v1/chat/completions",
    #     body='{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "你好"}]}',
    #     headers='{"authorization":"Bearer sk-5bqzNIxlLOlutnHcZfkjmCKaMHzRKnF3oscA5sTvJy3541C8"}'
    # )


    # result = api.add_monitor(
    #     name="Chatfire",
    #     type=MonitorType.PING,
    #     method="GET",
    #     hostname="api.chatfire.cn"
    # )
    #
    #
    # print(result)
    # api.save_status_page(
    #     slug="test222",
    #     id="test222",
    #     title="test222",
    #     publicGroupList=[
    #         {
    #             'name': 'Services',
    #             'weight': 1,
    #             'monitorList': [
    #                 {
    #                     "id": int(result.get('monitorID'))
    #                 }
    #             ]
    #         }
    #     ]
    # )


"""
curl --location --request POST 'https://api.x.cn/v1/videos' \
--header 'User-Agent: Apifox/1.0.0 (https://apifox.com)' \
--header 'Authorization: Bearer sk-ZFltlL1TbLDXp9g0xdykhZlLyjqSOSg2Ujs46iUeUCZi1MDK' \
--form 'model="sora-2-hd"' \
--form 'prompt="牛飞起来"'


curl --location --request GET 'https://api..cn/v1/videos/sora-2-hd:task_01k7dww579ef9rkrn2hb4rvkrc' \
--header 'User-Agent: Apifox/1.0.0 (https://apifox.com)' \
--header 'Authorization: Bearer sk-ZFltlL1TbLDXp9g0xdykhZlLyjqSOSg2Ujs46iUeUCZi1MDK'
"""