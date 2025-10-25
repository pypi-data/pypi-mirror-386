import re
import typing as t
from contextlib import suppress

from aiohttp import ClientResponse
from lxml.html import HtmlElement, document_fromstring
from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    Field,
    HttpUrl,
    TypeAdapter,
    create_model,
    model_validator,
)
from tenacity import TryAgain
from typing_extensions import Self

from aioqzone.exception import QzoneError
from aioqzone.utils.regex import entire_closing, response_callback
from qqqr.utils.iter import firstn
from qqqr.utils.jsjson import json_loads

from .feed import FeedData
from .profile import ProfileFeedData, QzoneProfile

StrDict = t.Dict[str, t.Any]


__all__ = [
    "QzoneResponse",
    "FeedPageResp",
    "ProfileResp",
    "IndexPageResp",
    "ProfilePagePesp",
    "DetailResp",
    "FeedCount",
    "SingleReturnResp",
    "AddCommentResp",
    "AddCommentLegacyResp",
    "DeleteCommentResp",
    "PublishMoodResp",
    "DeleteUgcResp",
    "UploadPicResponse",
    "PhotosPreuploadResponse",
    "FeedData",
    "PicInfo",
    "ProfileFeedData",
    "AvatarResponse",
]

validate_strdict = TypeAdapter(StrDict).validate_python
validate_str = TypeAdapter(str).validate_python


class QzoneResponse(BaseModel):
    _errno_key: t.ClassVar[t.Union[str, AliasPath, AliasChoices, None]] = AliasChoices(
        "code", "ret", "err", "error"
    )
    _msg_key: t.ClassVar[t.Union[str, AliasPath, AliasChoices, None]] = AliasChoices(
        "message", "msg"
    )
    _data_key: t.ClassVar[t.Union[str, AliasPath, AliasChoices, None]] = AliasPath("data")

    @classmethod
    def from_response_object(cls, obj: "StrDict") -> Self:
        """Parses the response text or object recieved from Qzone API.

        :param obj: the parsed response object. see `.response_to_object`
        :raise `aioqzone.exception.QzoneError`: if returned result code != 0

        :return: Self
        """

        class response_header(BaseModel):
            status: int = Field(default=0, validation_alias=cls._errno_key)
            message: str = Field(default="", validation_alias=cls._msg_key)

        header = response_header.model_validate(obj)
        if header.status != 0:
            if header.message:
                raise QzoneError(header.status, header.message, robj=obj)
            else:
                raise QzoneError(header.status, robj=obj)

        if cls._data_key is None:
            return cls.model_validate(obj)

        data_wrapper = create_model(
            "data_wrapper", data=(cls, Field(validation_alias=cls._data_key))
        )
        return getattr(data_wrapper.model_validate(obj), "data")

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> "StrDict":
        return await response.json(content_type=None)


class FeedCount(QzoneResponse):
    active_cnt: int = 0
    passive_cnt: int = 0
    gamebar_cnt: int = 0
    gift_cnt: int = 0
    visitor_cnt: int = 0


class DetailResp(FeedData, QzoneResponse):
    hasmore: bool = False
    attach_info: str = ""

    @model_validator(mode="before")
    def remove_prefix(cls, v: dict):
        return {k[5:] if str.startswith(k, "cell_") else k: i for k, i in v.items()}


class FeedPageResp(QzoneResponse):
    """Represents RESPonse from get feed page operation.
    Used to validate response data in :meth:`aioqzone.api.h5.QzoneH5API.index`
    and :meth:`aioqzone.api.h5.QzoneH5API.getActivateFeeds`
    """

    hasmore: bool = False
    attachinfo: str = ""
    newcnt: int

    undeal_info: FeedCount
    vFeeds: t.List[FeedData]


class ProfileResp(FeedPageResp):
    vFeeds: t.List[ProfileFeedData]


class IndexPageResp(FeedPageResp):
    qzonetoken: str = ""

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> StrDict:
        html = await response.text()
        scripts: t.List[HtmlElement] = document_fromstring(html).xpath(
            'body/script[@type="application/javascript"]'
        )
        if not scripts:
            raise TryAgain("script tag not found")

        texts: t.List[str] = [s.text for s in scripts if s.text]
        script = firstn(texts, lambda s: "shine0callback" in s)
        if not script:
            raise TryAgain("data script not found")

        m = re.search(r'window\.shine0callback.*return "([0-9a-f]+?)";', script)
        if m is None:
            raise TryAgain("data script not found")
        qzonetoken = m.group(1)

        m = re.search(r"var FrontPage =.*?data\s*:\s*\{", script)
        if m is None:
            raise TryAgain("page data not found")
        data = script[m.end() - 1 : m.end() + entire_closing(script[m.end() - 1 :])]
        data = validate_strdict(json_loads(data))

        with suppress(TypeError):
            data["data"]["qzonetoken"] = qzonetoken

        return data


class QzoneStatistic(BaseModel):
    blog: int = 0
    message: int = 0
    pic: int = 0
    shuoshuo: int = 0


class QzoneInfo(QzoneResponse):
    count: QzoneStatistic = Field(default_factory=QzoneStatistic)
    cover: HttpUrl = Field(validation_alias=AliasPath("coverinfo", 0, "cover"))
    is_friend: bool = False
    is_hide: int = 0
    limit: int = 0
    profile: QzoneProfile


class ProfilePagePesp(QzoneResponse):
    info: QzoneInfo
    feedpage: ProfileResp
    qzonetoken: str

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> StrDict:
        html = await response.text()
        scripts: t.List[HtmlElement] = document_fromstring(html).xpath(
            'body/script[@type="application/javascript"]'
        )
        if not scripts:
            raise TryAgain("ProfilePageResponse: script tag not found")

        texts: t.List[str] = [s.text for s in scripts if s.text]
        script = firstn(texts, lambda s: "shine0callback" in s)
        if not script:
            raise TryAgain("ProfilePageResponse: script tag not found")

        m = re.search(r'window\.shine0callback.*return "([0-9a-f]+?)";', script)
        if m is None:
            raise TryAgain("ProfilePageResponse: qzonetoken not found")
        qzonetoken = m.group(1)

        m = re.search(r"var FrontPage =.*?data\s*:\s*\[", script)
        if m is None:
            raise TryAgain("page data not found")
        data = script[m.end() - 1 : m.end() + entire_closing(script[m.end() - 1 :], "[")]
        data = re.sub(r",,\]$", "]", data)
        data = json_loads(data)
        assert isinstance(data, list)
        if len(data) < 2:
            raise TryAgain("ProfilePageResponse: profile not returned")

        data = dict(zip(["info", "feedpage"], data))
        data["qzonetoken"] = qzonetoken
        return data

    @classmethod
    def from_response_object(cls, obj: "StrDict") -> Self:
        return cls(
            info=QzoneInfo.from_response_object(validate_strdict(obj["info"])),
            feedpage=ProfileResp.from_response_object(validate_strdict(obj["feedpage"])),
            qzonetoken=validate_str(obj.get("qzonetoken", "")),
        )


class SingleReturnResp(QzoneResponse):
    _data_key = None
    pass


class AddCommentResp(QzoneResponse):
    ret: int = 0
    msg: str = ""
    verifyurl: str = ""
    commentid: int = 0
    commentLikekey: HttpUrl


class AddCommentLegacyResp(QzoneResponse):
    _data_key = None
    smooth_policy: dict = Field(
        default_factory=dict, validation_alias=AliasPath("result", "smoothpolicy")
    )
    feeds: str = ""

    @classmethod
    async def response_to_object(cls, response: ClientResponse):
        html = await response.text()
        scripts: t.List[HtmlElement] = document_fromstring(html).xpath(
            'body/script[@type="text/javascript"]'
        )
        texts: t.List[str] = [s.text for s in scripts if s.text]
        script = firstn(texts, lambda s: "frameElement.callback" in s)
        if not script:
            raise TryAgain("AddCommentLegacyResponse: script tag not found")

        m = response_callback.search(script)
        assert m
        return validate_strdict(json_loads(m.group(1)))


class DeleteCommentResp(QzoneResponse):
    feeds: str = ""

    @classmethod
    async def response_to_object(cls, response: ClientResponse):
        html = await response.text()
        scripts: t.List[HtmlElement] = document_fromstring(html).xpath(
            'body/script[@type="text/javascript"]'
        )
        texts: t.List[str] = [s.text for s in scripts if s.text]
        script = firstn(texts, lambda s: "frameElement.callback" in s)
        if not script:
            raise TryAgain("DeleteCommentResponse: script tag not found")

        m = response_callback.search(script)
        assert m
        return validate_strdict(json_loads(m.group(1)))


class PublishMoodResp(QzoneResponse):
    ret: int = 0
    msg: str = ""
    fid: str = Field(validation_alias="tid")
    undeal_info: FeedCount = Field(default_factory=FeedCount)


class DeleteUgcResp(QzoneResponse):
    ret: int = 0
    msg: str = ""
    undeal_info: FeedCount = Field(default_factory=FeedCount)


class UploadPicResponse(QzoneResponse):
    _data_key = None

    filelen: int
    filemd5: str

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> StrDict:
        m = response_callback.search(await response.text())
        assert m
        return validate_strdict(json_loads(m.group(1)))


class PicInfo(QzoneResponse):
    _data_key = None

    pre: HttpUrl
    url: HttpUrl
    sloc: str
    """id of small picture"""
    lloc: str
    """id of large picture"""
    width: int
    height: int
    albumid: str


class PhotosPreuploadResponse(QzoneResponse):
    _data_key = None
    photos: t.List[PicInfo] = Field(default_factory=list)

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> StrDict:
        m = response_callback.search(await response.text())
        assert m

        picinfos = json_loads(m.group(1))
        assert isinstance(picinfos, list)
        return dict(photos=[PicInfo.from_response_object(info["picinfo"]) for info in picinfos])  # type: ignore


class AvatarResponse(QzoneResponse):
    _errno_key = None
    _msg_key = None
    _data_key = None

    avatar: bytes

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> "StrDict":
        return {"avatar": await response.content.read()}
