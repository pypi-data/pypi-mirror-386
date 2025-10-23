#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : video_types
# @Time         : 2024/9/13 10:15
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import uuid

from meutils.pipe import *

from openai.types.video import Video as _Video


class Video(_Video):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Unique identifier for the video job."""

    created_at: int = Field(default_factory=lambda: int(time.time()))
    """Unix timestamp (seconds) for when the job was created."""

    model: Optional[Union[str, Literal["sora-2", "sora-2-pro"]]] = None
    """The video generation model that produced the job."""

    object: Literal["video"] = "video"
    """The object type, which is always `video`."""

    progress: int = 0
    """Approximate completion percentage for the generation task."""

    seconds: Optional[Union[str, Literal["4", "8", "12"]]] = None
    """Duration of the generated clip in seconds."""

    size: Optional[Union[str, Literal["720x1280", "1280x720", "1024x1792", "1792x1024"]]] = None
    """The resolution of the generated video."""

    status: Literal["queued", "in_progress", "completed", "failed"] = "queued"
    """Current lifecycle status of the video job."""

    video_url: Optional[str] = None

    # class Config:
    #     extra = "allow"


class VideoRequest(BaseModel):
    model: Union[str, Literal["cogvideox-flash", "cogvideox"]] = "cogvideox-flash"

    prompt: str = "比得兔开小汽车，游走在马路上，脸上的表情充满开心喜悦。"
    negative_prompt: Optional[str] = None

    """
    提供基于其生成内容的图像。如果传入此参数，系统将以该图像为基础进行操作。支持通过URL或Base64编码传入图片。
    图片要求如下：图片支持.png、jpeg、.jpg 格式、图片大小：不超过5M。image_url和prompt二选一或者同时传入。
    """
    image_url: Optional[str] = None
    tail_image_url: Optional[str] = None

    """
    输出模式，默认为 "quality"。 "quality"：质量优先，生成质量高。 "speed"：速度优先，生成时间更快，质量相对降低。 
    cogvideox-flash模型不支持选择输出模式。
    """
    quality: Literal["quality", "speed"] = "speed"

    """是否生成 AI 音效。默认值: False（不生成音效）。"""
    with_audio: bool = True

    cfg_scale: Optional[float] = None

    """
    默认值: 若不指定，默认生成视频的短边为 1080，长边根据原图片比例缩放。最高支持 4K 分辨率。
    分辨率选项：720x480、1024x1024、1280x960、960x1280、1920x1080、1080x1920、2048x1080、3840x2160
    """
    aspect_ratio: Union[str, Literal["1:1", "21:9", "16:9", "9:16", "4:3", "3:4"]] = "16:9"

    size: Literal[
        '720x480',
        '1024x1024',
        '1280x960',
        '960x1280',
        '1920x1080',
        '1080x1920',
        '2048x1080',
        '3840x2160'] = "1024x1024"

    duration: Literal[5, 10] = 5

    fps: Literal[30, 60] = 30


class SoraVideoRequest(BaseModel):
    model: Union[str, Literal["sora-2", "sora-2-pro"]] = "sora-2"
    prompt: str = "比得兔开小汽车，游走在马路上，脸上的表情充满开心喜悦。"
    seconds: Union[str, Literal["4", "8", "12"]] = "4"
    size: Optional[Union[str, Literal["720x1280", "1280x720", "1024x1792", "1792x1024"]]] = "720x1280"
    input_reference: Optional[Union[str, bytes, list]] = None  # image url/base64/bytes
    webhook_url: Optional[str] = None


class FalVideoRequest(BaseModel):
    model: Union[str, Literal["latentsync", "sync-lipsync",]] = 'latentsync'
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None

    sync_mode: Union[str, Literal["cut_off", "loop", "bounce"]] = "cut_off"


class FalKlingVideoRequest(BaseModel):
    model: Union[
        str, Literal["fal-ai/kling-video/v1/standard/text-to-video",]] = 'fal-ai/kling-video/v1/standard/text-to-video'

    prompt: Optional[str] = None
    duration: Optional[float] = 5.0
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None

    sync_mode: Union[str, Literal["cut_off", "loop", "bounce"]] = "cut_off"


class LipsyncVideoRequest(BaseModel):
    model: Union[str, Literal[
        "latentsync", "sync-lipsync",
        "lip_sync_avatar_std", "lip_sync_avatar_lively"
    ]
    ] = 'latentsync'

    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None

    sync_mode: Union[str, Literal["cut_off", "loop", "bounce"]] = "cut_off"


if __name__ == '__main__':
    # print(LipsyncVideoRequest())

    print(Video(x=1))
