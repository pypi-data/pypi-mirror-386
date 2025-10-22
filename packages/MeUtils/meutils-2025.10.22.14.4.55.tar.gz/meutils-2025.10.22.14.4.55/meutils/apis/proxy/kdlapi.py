#!/usr/bin/env Python
# -*- coding: utf-8 -*-

from meutils.pipe import *
from meutils.caches import rcache
from meutils.decorators.retry import retrying

username = "d1982743732"
password = "1h29rymg"


@rcache(ttl=2.5 * 60)
@retrying()
async def get_proxy_list(n: int = 1):
    secret_id = os.getenv("KDLAPI_SECRET_ID")
    signature = os.getenv("KDLAPI_SIGNATURE")
    url = f"https://dps.kdlapi.com/api/getdps/?secret_id={secret_id}&signature={signature}&num={n}&pt=1&format=json&sep=1"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        proxy_list = response.json().get('data').get('proxy_list')

        logger.debug(f"获取到的代理: {proxy_list}")

        return [f"http://{username}:{password}@{proxy}" for proxy in proxy_list]


async def get_one_proxy():
    proxy_list = await get_proxy_list()
    return proxy_list[-1]


if __name__ == '__main__':
    # arun(get_proxy_list())

    page_url = "https://icanhazip.com/"  # 要访问的目标网页


    # page_url = "https://httpbin.org/ip"

    async def fetch(url):
        proxy = await get_one_proxy()
        # proxy = "http://154.9.253.9:38443"
        # # proxy="https://tinyproxy.chatfire.cn"
        # # proxy="https://pp.chatfire.cn"
        # proxy = "http://110.42.51.201:38443"
        # proxy = "http://110.42.51.223:38443"
        # proxy = "http://110.42.51.223:38443"

        # proxy=None
        # proxy = "https://npjdodcrxljt.ap-northeast-1.clawcloudrun.com"

        async with httpx.AsyncClient(proxy=proxy, timeout=30) as client:
            resp = await client.get(url)
            logger.debug((f"status_code: {resp.status_code}, content: {resp.text}"))


    def run():
        loop = asyncio.get_event_loop()
        # 异步发出5次请求
        tasks = [fetch(page_url) for _ in range(3)]
        loop.run_until_complete(asyncio.wait(tasks))


    # run()

    arun(get_one_proxy())


# 'http://d1982743732:1h29rymg@58.19.55.11:33145