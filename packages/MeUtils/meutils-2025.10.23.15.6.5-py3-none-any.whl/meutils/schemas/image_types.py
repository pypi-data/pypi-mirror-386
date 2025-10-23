#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : image_types
# @Time         : 2024/8/21 14:18
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo: 通用比例适配

from meutils.pipe import *
from meutils.str_utils import parse_url, parse_command_string
from meutils.math_utils import size2aspect_ratio

from pydantic import constr
from openai.types import ImagesResponse as _ImagesResponse, Image

# {v:k for k, v in ASPECT_RATIOS.items()}
ASPECT_RATIOS = {
    "1:1": "1024x1024",

    "1:2": "512x1024",
    "2:1": "1024x512",

    '2:3': "768x512",
    '3:2': "512x768",

    "4:3": "1280x960",  # "1024x768"
    "3:4": "960x1280",

    "5:4": "1280x960",
    "4:5": "960x1280",

    "16:9": "1366x768",  # "1024x576"
    "9:16": "768x1366",

    "21:9": "1344x576",

    '1024x1024': '1:1',
    '512x1024': '1:2',
    '1024x512': '2:1',
    '768x512': '2:3',
    '512x768': '3:2',

    '1280x960': '4:3',
    '960x1280': '3:4',
    "1024x768": '4:3',
    "768x1024": '3:4',

    '1366x768': '16:9',

    '768x1366': '9:16',
    '1024x576': '16:9',
    '576x1024': '9:16',

    '1344x576': '21:9'

}


class ImagesResponse(_ImagesResponse):
    created: int = Field(default_factory=lambda: int(time.time()))

    data: Optional[List[Union[Image, dict]]] = []

    image: Optional[Union[str, List[str]]] = None

    metadata: Optional[Any] = None

    timings: Optional[Any] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        if not self.data and self.image is not None:
            if isinstance(self.image, str):
                self.image = [self.image]

            self.data = [{"url": image} for image in self.image]

        elif self.data and "imageURL" in self.data[0]:
            self.image = [d["imageURL"] for d in self.data]

    # class Config:
    #     extra = "allow"


class ImageRequest(BaseModel):  # openai
    """
    图生图 两种方式： prompt + controls

        background: Optional[Literal["transparent", "opaque", "auto"]] | NotGiven = NOT_GIVEN,
        model: Union[str, ImageModel, None] | NotGiven = NOT_GIVEN,
        output_compression: Optional[int] | NotGiven = NOT_GIVEN,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | NotGiven = NOT_GIVEN,
        partial_images: Optional[int] | NotGiven = NOT_GIVEN,

    """
    model: str = ''

    prompt: constr(min_length=1, max_length=10240) = " "

    moderation: Optional[Literal["low", "auto"]] = None

    style: Optional[Union[str, Literal["vivid", "natural"]]] = None
    background: Optional[Union[str, Literal["transparent", "opaque", "auto"]]] = None
    input_fidelity: Optional[Union[str, Literal["high", "low"]]] = None
    quality: Optional[Union[str, Literal["standard", "low", "medium", "high", "auto"]]] = None

    # 测试默认值 Optional[Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]]
    n: Optional[int] = 1
    size: Optional[str] = '1024x1024'  # null auto

    output_format: Optional[Literal["png", "jpeg", "webp"]] = None
    response_format: Optional[Literal["url", "b64_json", "oss_url", "glb", "stl"]] = "url"

    seed: Optional[int] = None
    stream: Optional[bool] = None

    # oneapi https://github.com/QuantumNous/new-api/blob/main/dto/dalle.go
    extra_fields: Optional[Any] = None  ###

    negative_prompt: Optional[str] = None
    guidance: Optional[float] = None
    steps: Optional[int] = None

    controls: Optional[dict] = None  # 额外参数

    safety_tolerance: Optional[int] = None

    aspect_ratio: Optional[str] = None

    user: Optional[str] = None

    image: Optional[Union[str, List[str], bytes, List[bytes]]] = None  # url b64 file_bytes
    watermark: Optional[bool] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        # 规避空字符
        self.style = self.style or None
        self.quality = self.quality or None
        self.background = self.background or None
        self.input_fidelity = self.input_fidelity or None

        if not self.model.startswith(("doubao-seed",)):

            if self.aspect_ratio:  # 适配比例
                self.size = ASPECT_RATIOS.get(self.aspect_ratio, '1024x1024')

            elif self.size == 'auto':
                self.size = self.aspect_ratio = None

            elif self.size:  # 适配尺寸
                self.aspect_ratio = size2aspect_ratio(self.size)
                self.size = self.size if 'x' in self.size else '512x512'

    @cached_property
    def image_urls(self) -> List[str]:
        if self.image:
            if isinstance(self.image, str):
                return [self.image]
            else:
                return self.image
        else:
            image, _ = self.image_and_prompt
            if image:
                return [image]

        return []

    @cached_property
    def image_and_prompt(self):  # image prompt 目前是单图
        if self.prompt.startswith('http') and (prompts := self.prompt.split(maxsplit=1)):
            if len(prompts) == 2:
                self.prompt = prompts[-1]
                return prompts
            else:
                return prompts + [' ']  # 只有 单url

        elif "http" in self.prompt and (images := parse_url(self.prompt)):
            self.prompt = self.prompt.replace(images[0], "")
            return images[0], self.prompt

        else:
            return None, self.prompt

    def prompt2aspect_ratio(self, aspect_ratios):  # 提示词优先级最高：从支持的比例中选择匹配
        for aspect_ratio in aspect_ratios:
            if aspect_ratio in self.prompt:
                return aspect_ratio

    class Config:
        extra = "allow"

        # frozen = True
        # populate_by_name = True

        json_schema_extra = {
            "examples": [
                {
                    "model": "stable-diffusion-3-medium",  # sd3
                    "prompt": "画条狗",
                },
            ]
        }


class ImageEditRequest(BaseModel):
    model: Union[str, Literal["dall-e-2", "dall-e-3", "gpt-image-1"]]

    # image: Union[FileTypes, SequenceNotStr[FileTypes]],
    # prompt: str,
    # mask: FileTypes | NotGiven = NOT_GIVEN,

    prompt: str
    image: Any  # 图片

    mask: Optional[Any] = None  # 图片

    background: Optional[Union[str, Literal["transparent", "opaque", "auto"]]] = None
    input_fidelity: Optional[Union[str, Literal["high", "low"]]] = None
    quality: Optional[Union[str, Literal["standard", "low", "medium", "high", "auto"]]] = None

    n: Optional[int] = 1
    size: Optional[
        Union[str, Literal["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "auto"]]] = "1024x1024"

    aspect_ratio: Optional[str] = None

    user: Optional[str] = None
    stream: Optional[bool] = None

    response_format: Optional[Literal["url", "b64_json"]] = None
    output_format: Optional[Literal["png", "jpeg", "webp"]] = None

    # output_compression: Optional[int] | NotGiven = NOT_GIVEN,
    # partial_images: Optional[int] | NotGiven = NOT_GIVEN,

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        # 规避空字符
        self.quality = self.quality or None
        self.background = self.background or None
        self.input_fidelity = self.input_fidelity or None

        if not isinstance(self.image, list):
            self.image = [self.image]

        if not self.model.startswith(("doubao-seed",)):

            if self.aspect_ratio:  # 适配比例
                self.size = ASPECT_RATIOS.get(self.aspect_ratio, '1024x1024')

            elif self.size == 'auto':
                self.size = self.aspect_ratio = None

            elif self.size:  # 适配尺寸
                # if self.size.lower().endswith('k'):
                #     size = int(self.size.lower().split('k')[0]) * 1024
                #     self.size = f"{size}x{size}"
                self.aspect_ratio = size2aspect_ratio(self.size)
                self.size = self.size if 'x' in self.size else '512x512'


class FalImageRequest(ImageRequest):
    prompt: str
    seed: Optional[int] = None
    sync_mode: Optional[bool] = None
    num_images: Optional[int] = 1
    enable_safety_checker: Optional[bool] = True
    safety_tolerance: Optional[str] = "6"
    output_format: Optional[str] = "png"
    aspect_ratio: Literal['21:9', '16:9', '4:3', '1:1', '3:4', '9:16', '9:21'] = "1:1"
    raw: Optional[bool] = None


class FluxImageRequest(ImageRequest):
    model: str = 'flux1.0-schnell'
    image_size: Optional[str] = None

    num_inference_steps: Optional[int] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.image_size = self.size


class TogetherImageRequest(ImageRequest):  # together
    model: str = 'flux1.0-turbo'
    steps: Optional[int] = None

    height: int = 1024
    width: int = 1024

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        try:
            self.width, self.height = map(int, self.size.split('x'))
        except Exception as e:
            logger.error(e)

        if "pro" in self.model:
            self.model = 'flux1.1-pro'


class SDImageRequest(ImageRequest):
    model: str = "stable-diffusion"
    image_size: Optional[str] = None  # 512x512, 512x1024, 768x512, 768x1024, 1024x576, 576x1024
    batch_size: Optional[int] = None
    guidance_scale: Optional[float] = 7.5
    num_inference_steps: Optional[int] = 25

    image: Optional[str] = None  # base64

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.n = self.batch_size or self.n


class HunyuanImageRequest(ImageRequest):
    model: str = "hunyuan"
    size: Literal["1:1", "3:4", "4:3", "9:16", "16:9"] = "1:1"
    style: Optional[Literal[
        '摄影',
        '童话世界',
        '奇趣卡通',
        '二次元',
        '纯真动漫',

        '清新日漫',
        '3D'
        '赛博朋克',
        '像素',
        '极简',

        '复古',
        '暗黑系',
        '波普风',
        '中国风',
        '国潮',

        '糖果色',
        '胶片电影',
        '素描',
        '水墨画',
        '油画',

        '水彩',
        '粉笔',
        '粘土',
        '毛毡',
        '贴纸',

        '剪纸',
        '刺绣',
        '彩铅',
        '梵高',
        '莫奈',

        '穆夏',
        '毕加索',
    ]] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)


class KlingImageRequest(ImageRequest):
    model: str = "kling"
    n: Optional[int] = 4
    size: str = "1:1"

    # 图生图
    image: Optional[str] = None
    image_fidelity: Optional[float] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.size = "1:1" if self.size not in {"1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"} else self.size


class KolorsRequest(ImageRequest):
    model: Union[str, Literal["kolors-1.0", "kolors-1.5"]] = "kolors-1.0"
    n: Optional[int] = 4

    """
    1:1(1024*1024)
    4:3(1152*896)
    3:4(768*1024)
    16:9(1024 576)
    9:16(576 1024)
    3:2(1024*640)
    2:3(640*1024)
    """
    size: Literal[
        "1024x1024", "1152x896", "768x1024", "1024x576", "576x1024", "1024x640", "640x1024"
    ] = "1024x1024"

    # 图生图
    image: Optional[str] = None
    image_fidelity: Optional[float] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)


class CogviewImageRequest(ImageRequest):
    model: str = "cogview-3"
    size: Optional[Literal["1024x1024", "768x1344", "864x1152", "1344x768", "1152x864", "1440x720", "720x1440"]] = None


class StepImageRequest(ImageRequest):
    image_size: str
    batch_size: int
    guidance_scale: float
    num_inference_steps: int


class RecraftImageRequest(ImageRequest):
    transform_model: str = "recraftv3"  # recraftv3-halloween
    image_type: Optional[
        Union[
            str,
            Literal[
                'any',
                'digital_illustration',
                'digital_illustration',
                'digital_illustration_pixel_art',
                'digital_illustration_3d',
                'digital_illustration_psychedelic',
                'digital_illustration_hand_drawn',
                'digital_illustration_grain',
                'digital_illustration_glow',
                'digital_illustration_80s',
                'digital_illustration_watercolor',
                'digital_illustration_voxel',
                'digital_illustration_infantile_sketch',
                'digital_illustration_2d_art_poster',
                'digital_illustration_kawaii',
                'digital_illustration_halloween_drawings',
                'digital_illustration_2d_art_poster_2',
                'digital_illustration_engraving_color',
                'digital_illustration_flat_air_art',
                'digital_illustration_hand_drawn_outline',
                'digital_illustration_handmade_3d',
                'digital_illustration_stickers_drawings',

                'realistic_image',
                'realistic_image_mockup',
                'realistic_image_b_and_w',
                'realistic_image_enterprise',
                'realistic_image_hard_flash',
                'realistic_image_hdr',
                'realistic_image_natural_light',
                'realistic_image_studio_portrait',
                'realistic_image_motion_blur',

                'vector_illustration',
                'vector_illustration_seamless',
                'vector_illustration_line_art',
                'vector_illustration_doodle_line_art',
                'vector_illustration_flat_2',
                'vector_illustration_70s',
                'vector_illustration_cartoon',
                'vector_illustration_kawaii',
                'vector_illustration_linocut',
                'vector_illustration_engraving',
                'vector_illustration_halloween_stickers',
                'vector_illustration_line_circuit',

            ]]] = "any"
    user_controls: dict = {}
    layer_size: Optional[dict] = None
    random_seed: Optional[int] = None
    num_images_per_prompt: Optional[int] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.num_images_per_prompt = self.n
        self.random_seed = self.seed

        max_size = 2048  # 最大像素
        w, h = map(int, self.size.split('x'))
        scale_factor = max_size // max(w, h)
        w, h = w * scale_factor, h * scale_factor

        self.layer_size = {"width": w, "height": h}

        self.image_type = self.style or self.image_type
        if self.image_type in {"natural", }:
            self.image_type = "any"


class ImageProcessRequest(BaseModel):
    task: Optional[str] = None
    image: str


BAIDU_TASKS = {
    'matting': 'matting',
    'ai-matting': 'matting',
    'ai-removewatermark': 'removewatermark'  # TODO： 变清晰
}


class BaiduImageProcessRequest(ImageProcessRequest):
    task: Optional[str] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.task = BAIDU_TASKS.get(self.task, self.task)


HUNYUAN_TASKS = {
    'clarity': 'clarity',
    'removewatermark': 'removewatermark',
    'style': 'style',
}


class HunyuanImageProcessRequest(ImageProcessRequest):
    task: Optional[Literal[
        'removewatermark',
        'style',
        'clarity',
    ]] = 'removewatermark'
    style: Optional[Literal[
        '摄影',
        '童话世界',
        '奇趣卡通',
        '二次元',
        '纯真动漫',

        '清新日漫',
        '3D'
        '赛博朋克',
        '像素',
        '极简',

        '复古',
        '暗黑系',
        '波普风',
        '中国风',
        '国潮',

        '糖果色',
        '胶片电影',
        '素描',
        '水墨画',
        '油画',

        '水彩',
        '粉笔',
        '粘土',
        '毛毡',
        '贴纸',

        '剪纸',
        '刺绣',
        '彩铅',
        '梵高',
        '莫奈',

        '穆夏',
        '毕加索',
    ]] = None

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.task = HUNYUAN_TASKS.get(self.task, self.task)


TEXTIN_TASKS = {
    # 文本解析
    "image-to-markdown": "pdf_to_markdown",
    "pdf-to-markdown": "pdf_to_markdown",
    "textin-pdf-to-markdown": "pdf_to_markdown",

    # 去水印
    'textin-removewatermark': 'watermark-remove',

    'textin-ocr': 'text_recognize_3d1',
    'text-recognize': 'text_recognize_3d1',

    # 图片提取表格
    "textin-table": "table",

    "textin-crop-enhance": "crop_enhance_image",

    # 票据识别
    "textin-bill-recognize": "bill_recognize_v2",
}


class TextinImageProcessRequest(ImageProcessRequest):

    def __init__(self, /, **data: Any):
        super().__init__(**data)

        self.task = TEXTIN_TASKS.get(self.task.replace('_', '-'), self.task)


class ImageProcess(BaseModel):
    model: Literal[
        "remove-watermark",
        "remove-watermark-hunyuan",
        "remove-watermark-textin",

        "clarity",
        "clarity-hunyuan",
        "clarity-baidu",

        "expand",
        "rmbg-2.0"
    ]
    image: Union[str, bytes]
    mask: Optional[str] = None

    style: Optional[str] = None
    aspect_ratio: Union[str, Literal["1:1", "4:3", "3:4"]] = "1:1"  # 扩图

    response_format: Literal["url", "b64_json"] = "url"

    # class Config:
    #     extra = "allow"


if __name__ == '__main__':
    # print(ASPECT_RATIOS.items())

    # ImageRequest(quality=1)
    @lru_cache()
    def f(r):
        return r


    # f(FluxImageRequest(prompt="xx"))

    # from openai import OpenAI
    # from meutils.llm.openai_utils import to_openai_images_params
    #
    # data = to_openai_images_params(ImageRequest(prompt="a dog"))
    #
    # print(data)
    #
    # OpenAI().images.generate(**ImageRequest(prompt="a dog").model_dump())

    # print(KlingImageRequest())

    # print(ImagesResponse(data=[{'url': 1}]))

    # print(RecraftImageRequest(prompt="").model_dump_json())
    # print(RecraftImageRequest(prompt=""))

    prompt = "https://oss.ffire.cc/files/kling_watermark.png 带个眼镜"
    # prompt = "带个眼镜 https://oss.ffire.cc/files/kling_watermark.png"
    # prompt = "https://oss.ffire.cc/files/kling_watermark.png"
    # prompt = "画条狗"

    request = ImageRequest(
        prompt=prompt,

        # size="16x9",
        # size="1K",
        size="2K",

        # size="auto",

        # aspect_ratio="16:9"
    )

    # "sequential_image_generation": "auto",
    # "sequential_image_generation_options": {
    #     "max_images": 4
    # },

    #
    # print(request.prompt)
    #
    # print(request.image_urls)
    # print(request.image_and_prompt)
    # print(request.prompt)

    # data = {"image[]": "xxx"}
    # r = ImageRequest(**data)
    #
    # data = {
    #     "model": "flux-kontext-pro",
    #     "prompt": "a cat and a dog",
    #     "size": "512x1024",
    #     # "aspect_ratio": "16:9"
    # }
    #
    # dd = {
    #     "model": "flux-kontext-pro",
    #     "prompt": "a cat and a dog",
    #     "size": "5121x1024",
    #     # "aspect_ratio": "16:9"
    # }
    #
    # r = ImageRequest(**data)

    # print(ImagesResponse())

    # print(request)

    # print(dict(Image()))

    print(ImageRequest(aspect_ratio="2:1"))
    print(ImageRequest(size="8x2", aspect_ratio="2:1"))  # aspect_ratio优先级更高
    print(ImageRequest(size="8x2"))
    print(ImageRequest(size="8:2"))
