from typing import List, Optional, Dict, Any
from core.client import CtyunClient
from core.credential import Credential
from core.exception import CtyunRequestException

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class CtimageDeleteImageRequest:
    imageID: str  # 镜像 ID。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=23&api=4763&data=89&isNormal=1&vid=83" target="_blank">查询可以使用的镜像资源</a>接口来查询您可使用的镜像资源，可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=23&api=4764&data=89&isNormal=1&vid=83" target="_blank">查询镜像详细信息</a>接口来查询 1 份镜像的详细信息。注意：<br />1. 所指定的镜像应是镜像状态为 active、deactivated、deactivating、deleting、error 或 reactivating 的私有镜像<br />2. 所指定的私有镜像的共享列表中没有镜像状态为 accepted 的共享镜像。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=23&api=6764&data=89&isNormal=1&vid=83" target="_blank">查询私有镜像的共享列表</a>接口来查询 1 份私有镜像的共享列表
    regionID: str  # 资源池 ID。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=5851&data=87&isNormal=1&vid=81" target="_blank">资源池列表查询</a>接口来查询您可见的资源池的列表

    def to_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if v is not None}


@dataclass
class CtimageDeleteImageReturnObjResponse:
    """成功时返回的数据"""
    pass  # 空类占位符

    @staticmethod
    def from_json(json_data: dict) -> Optional[dict]:
        if not json_data:
            return None
        return {}

@dataclass
class CtimageDeleteImageResponse:
    statusCode: Any = None  # 状态码。取值范围（值：描述）：<br />800：成功，<br />900：失败
    error: Optional[str] = None  # 错误码（product.module.code 三段式码）
    errorCode: Optional[str] = None  # 同 error 参数
    message: Optional[str] = None  # 英文描述信息
    description: Optional[str] = None  # 中文描述信息
    returnObj: Optional[CtimageDeleteImageReturnObjResponse] = None  # 成功时返回的数据

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageDeleteImageResponse']:
        if not json_data:
            return None

        return_obj = None
        if "returnObj" in json_data:
            returnObj = json_data.get("returnObj")
            if returnObj is not None:
                return_obj = CtimageDeleteImageReturnObjResponse.from_json(returnObj)

        obj = CtimageDeleteImageResponse(
            statusCode=json_data.get('statusCode'),
            error=json_data.get('error'),
            errorCode=json_data.get('errorCode'),
            message=json_data.get('message'),
            description=json_data.get('description'),
            returnObj=return_obj,
        )
        return obj


# 删除 1 份私有镜像<br />准备：<br />1. 在调用前需了解如何构造请求，可参见：如何调用 API - 构造请求<br />2. OpenAPI 请求需进行加密调用，可参见：如何调用 API - 认证鉴权<br />注意：在调用前，请您认真阅读此文档，包括但不限于参数描述中的“注意”部分
class CtimageDeleteImageApi:
    def __init__(self, ak: str = None, sk: str = None):
        self.endpoint = None
        self.credential = Credential(ak, sk)
    
    def set_endpoint(self, endpoint: str) -> None:
        self.endpoint = endpoint
    
    @staticmethod
    def do(credential: Credential, client: CtyunClient, endpoint: str, request: CtimageDeleteImageRequest) -> CtimageDeleteImageResponse:
        url = endpoint + "/v4/image/delete"
        params = {}
        try:
            header_params = {}
            request_dict = request.to_dict() if hasattr(request, 'to_dict') else request
            request_dict = {key: value for key, value in request_dict.items() if value is not None}
            response = client.post(url=url, params=params, header_params=header_params, data=request_dict, credential=credential)
            return CtimageDeleteImageResponse.from_json(response.json())
        except Exception as e:
            raise CtyunRequestException(str(e))
