import os

from meutils.pipe import *
from wecom.tx import WXBizMsgCrypt

from fastapi import FastAPI, Form, Depends, File, UploadFile, Body, Request, Response, Form, Cookie

from meutils.serving.fastapi import App

app = App()


class VerifyMessage(BaseModel):
    msg_signature: str
    timestamp: str
    nonce: str
    echostr: str


sToken = os.getenv('sToken', '8gVZ1fYiE6b9IYpIVxJAkupmdMhI')
sEncodingAESKey = os.getenv('sEncodingAESKey', 'etII6uK707WB39rSI2illsdSEuRQ8gcmWqO9Uxd8QCM')
sCorpID = 'ww3c6024bb94ecef59'


@app.api_route('/index', methods=['GET', 'POST'])
def index(request: Request):
    wxcpt = WXBizMsgCrypt(sToken, sEncodingAESKey, sCorpID)

    # 获取url验证时微信发送的相关参数
    sVerifyMsgSig = request.query_params.get('msg_signature')
    sVerifyTimeStamp = request.query_params.get('timestamp')
    sVerifyNonce = request.query_params.get('nonce')
    sVerifyEchoStr = request.query_params.get('echostr')

    logger.info(f"sVerifyEchoStr: {sVerifyEchoStr}")

    # 验证url
    if request.method == 'GET':
        ret, sEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)

        logger.info(f"ret: {ret}")
        logger.info(f"sEchoStr: {sEchoStr}")

        if (ret != 0):
            print(f"ERR: VerifyURL ret:{ret}")
            sys.exit(1)
        return sEchoStr


@app.api_route('/get_and_post', methods=["GET", "POST"])
async def get_and_post(request: Request):
    wxcpt = WXBizMsgCrypt(sToken, sEncodingAESKey, sCorpID)

    print(request.method)
    print(request.query_params._dict)

    vm = VerifyMessage.parse_obj(request.query_params)

    if request.method == 'GET':
        query_params = request.query_params._dict  # 直接get
        print(query_params)

        ret, sEchoStr = wxcpt.VerifyURL(vm.msg_signature, vm.timestamp, vm.nonce, vm.echostr)

        return sEchoStr  # .decode()
    else:
        data = await request.json()
        logger.info(data)

        ret, sMsg = wxcpt.DecryptMsg(data, vm.msg_signature, vm.timestamp, vm.nonce)

        return sMsg


if __name__ == '__main__':
    app.run(port=8000)
