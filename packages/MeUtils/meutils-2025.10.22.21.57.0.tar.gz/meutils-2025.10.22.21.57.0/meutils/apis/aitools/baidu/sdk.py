#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : sdk
# @Time         : 2025/1/17 10:54
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *


client_id = "6e4ca6247dea4186a09fc64362f72e51"
client_secret = "114d33c9-079b-2684-f93a-e6a1031260e1"

# BAIDU_AI=38243958:ayIjRRUv3MNNpss9r4YkCIKF:NqcBofQtvdAWKtiGAMjIkASWNxCKW8Fv # 25308860:GmAPqlyBDNLaoAqO2mrFhjS2:vXIoxFUdx2jiuRnGLvZSDMEczEaZsc1K

# DZjHpNLUauqYNFgpNujNhH5p 0p3XGiy0Y7troeGukFiEnlRMsq5smw9W
def main(client_id, client_secret):
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"

    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


from baidubce.bce_client_configuration import BceClientConfiguration
from baidubce.auth.bce_credentials import BceCredentials
from baidubce.services.bos import storage_class, bos_client

# 设置BosClient的Host，Access Key ID和Secret Access Key
bos_host = "hkg.bcebos.com"
access_key_id = "ALTAKRFJAQgNsEt2FTdrr5avOh"
secret_access_key = "b45cee038ca14852a8be3697595dec28"
config = BceClientConfiguration(credentials=BceCredentials(access_key_id, secret_access_key), endpoint=bos_host)

client = bos_client.BosClient(config)

if __name__ == '__main__':
    # client_id="DZjHpNLUauqYNFgpNujNhH5p"
    # client_secret = "0p3XGiy0Y7troeGukFiEnlRMsq5smw9W"
    # main(client_id, client_secret)
    user_metadata = {"name": "my-data"}


    _ = client.put_object_from_string("chatfire", "object_key", data="data")

