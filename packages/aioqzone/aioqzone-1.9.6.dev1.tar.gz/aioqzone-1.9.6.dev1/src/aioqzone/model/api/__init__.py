import typing as t

from pydantic import BaseModel, Field
from yarl import URL

from .request import *
from .response import *

TyRequest = t.TypeVar("TyRequest", bound=QzoneRequestParams)
TyResponse = t.TypeVar("TyResponse", bound=QzoneResponse)
TyHttpMethod = t.Union[t.Literal["GET"], t.Literal["POST"]]


class QzoneApi(BaseModel, t.Generic[TyRequest, TyResponse]):
    """The base class for all Qzone APIs below."""

    host: t.ClassVar[str] = "https://h5.qzone.qq.com"
    http_method: t.ClassVar[TyHttpMethod]
    path: t.ClassVar[str]

    keep_alive: t.ClassVar[bool] = True
    is_json: t.ClassVar[bool] = False
    referer: str = "https://h5.qzone.qq.com/"

    attach_token: t.ClassVar[bool] = True
    login_required: t.ClassVar[bool] = True
    params: TyRequest = Field(default_factory=QzoneRequestParams)  # type: ignore
    response: t.ClassVar[t.Type[TyResponse]]  # type: ignore

    @property
    def url(self) -> URL:
        return URL(str(self.host)).with_path(self.path.format(**self.params.model_dump()))


class IndexPageApi(QzoneApi[QzoneRequestParams, IndexPageResp]):
    response: t.ClassVar = IndexPageResp
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    path: t.ClassVar[str] = "/mqzone/index"
    keep_alive: t.ClassVar[bool] = False
    attach_token: t.ClassVar[bool] = False


class UserProfileApi(QzoneApi[ProfileParams, ProfilePagePesp]):
    response: t.ClassVar = ProfilePagePesp
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    path: t.ClassVar[str] = "/mqzone/profile"
    keep_alive: t.ClassVar[bool] = False
    attach_token: t.ClassVar[bool] = False


class FeedPageApi(QzoneApi[ActiveFeedsParams, FeedPageResp]):
    response: t.ClassVar = FeedPageResp
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    path: t.ClassVar[str] = "/webapp/json/mqzone_feeds/getActiveFeeds"


class ShuoshuoApi(QzoneApi[ShuoshuoParams, DetailResp]):
    response: t.ClassVar = DetailResp
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    path: t.ClassVar[str] = "/webapp/json/mqzone_detail/shuoshuo"


class GetFeedsApi(QzoneApi[GetFeedsParams, ProfileResp]):
    response: t.ClassVar = ProfileResp
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/get_feeds"


class GetCountApi(QzoneApi[GetCountParams, FeedCount]):
    response: t.ClassVar = FeedCount
    params: GetCountParams = Field(default_factory=GetCountParams)

    http_method: t.ClassVar[TyHttpMethod] = "GET"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/feeds/mfeeds_get_count"
    is_json: t.ClassVar[bool] = True


class LikeApi(QzoneApi[DolikeParam, SingleReturnResp]):
    response: t.ClassVar = SingleReturnResp
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    path: t.ClassVar[str] = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app"


class UnlikeApi(LikeApi):
    path: t.ClassVar[str] = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_unlike_app"


class AddCommentApi(QzoneApi[AddCommentParams, AddCommentResp]):
    response: t.ClassVar = AddCommentResp
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    path: t.ClassVar[str] = "/webapp/json/qzoneOperation/addComment"
    is_json: t.ClassVar[bool] = True


class AddCommentApiLegacy(QzoneApi[AddCommentParamsLegacy, AddCommentLegacyResp]):
    response: t.ClassVar = AddCommentLegacyResp
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    path: t.ClassVar[str] = "/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_re_feeds"


class DeleteCommentApi(QzoneApi[DeleteCommentParams, DeleteCommentResp]):
    response: t.ClassVar = DeleteCommentResp
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    path: t.ClassVar[str] = "/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_delcomment_ugc"


class ListFriendApi(QzoneApi):
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/friend/mfriend_list"


class PublishMoodApi(QzoneApi[PublishMoodParams, PublishMoodResp]):
    response: t.ClassVar = PublishMoodResp
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/mood/publish_mood"


class AddOperationApi(QzoneApi):
    response: t.Type[QzoneResponse]
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "operation/operation_add"


class UploadPicApi(QzoneApi[UploadPicParams, UploadPicResponse]):
    response: t.ClassVar = UploadPicResponse
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/up/cgi-bin/upload/cgi_upload_pic_v2"


class PhotosPreuploadApi(QzoneApi[PhotosPreuploadParams, PhotosPreuploadResponse]):
    response: t.ClassVar = PhotosPreuploadResponse
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/up/cgi-bin/upload/cgi_upload_pic_v2"


class AvatarApi(QzoneApi[AvatarParams, AvatarResponse]):
    response: t.ClassVar = AvatarResponse
    login_required: t.ClassVar[bool] = False
    http_method: t.ClassVar[TyHttpMethod] = "GET"
    host: t.ClassVar[str] = "https://qlogo2.store.qq.com"
    path: t.ClassVar[str] = "/qzone/{hostuin}/{hostuin}/{size}"


class SetTopApi(QzoneApi[SetTopParams, SingleReturnResp]):
    response: t.ClassVar = SingleReturnResp
    http_method: t.ClassVar[TyHttpMethod] = "POST"
    host: t.ClassVar[str] = "user.qzone.qq.com"
    path: t.ClassVar[str] = "proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/cgi_settopfeed"
