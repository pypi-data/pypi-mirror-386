from typing import List, Optional, Dict, Any
from core.client import CtyunClient
from core.credential import Credential
from core.exception import CtyunRequestException

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class CtimageListImageSharesRequest:
    imageID: str  # 镜像 ID。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=23&api=4763&data=89&isNormal=1&vid=83" target="_blank">查询可以使用的镜像资源</a>接口来查询您可使用的镜像资源，可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=23&api=4764&data=89&isNormal=1&vid=83" target="_blank">查询镜像详细信息</a>接口来查询 1 份镜像的详细信息
    regionID: str  # 资源池 ID。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=5851&data=87&isNormal=1&vid=81" target="_blank">资源池列表查询</a>接口来查询您可见的资源池的列表
    pageNo: Optional[str] = None  # 页码。取值范围：最小 1（默认值）
    pageSize: Optional[str] = None  # 每页记录数目。取值范围：最小 1，最大 50，默认 10

    def to_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if v is not None}


@dataclass
class CtimageListImageSharesReturnObjImagesResponse:
    appVersion: Optional[str] = None  # 应用版本
    architecture: Optional[str] = None  # 系统架构。取值范围（值：描述）：<br />aarch64：AArch64 架构，<br />loongarch64：LoongArch64 架构，<br />sw_64：sw_64 架构，<br />x86_64：x86_64 架构
    azName: Optional[str] = None  # 在多可用区资源池下物理机镜像的可用区名称
    bootMode: Optional[str] = None  # x86_64 架构非数据盘镜像的启动方式。取值范围（值：描述）：<br />bios：BIOS 启动方式，<br />uefi：UEFI 启动方式
    chargeableImage: Optional[bool] = None  # 用于表示是否是收费镜像的标识
    containerFormat: Optional[str] = None  # 容器格式
    createdTime: Any = None  # 创建时间戳
    createdTimeStr: Optional[str] = None  # 创建时间
    cwaiType: Optional[str] = None  # 云骁智算云主机节点类型。取值范围（值：描述）：<br />control：控制面云主机节点，<br />node：GPU 云主机节点<br /><br />注意：镜像可适用于多节点类型，多个云骁智算云主机节点类型之间以英文逗号（,）分隔，如 control,node
    description: Optional[str] = None  # 描述信息
    destinationAccountID: Optional[str] = None  # 共享镜像接受者的账号 ID
    destinationUser: Optional[str] = None  # 共享镜像接受者
    diskFormat: Optional[str] = None  # 磁盘格式。取值范围（值：描述）：<br />qcow2：QCOW2 格式，<br />raw：RAW 格式，<br />vhd：VHD 格式，<br />vmdk：VMDK 格式
    diskID: Optional[str] = None  # 私有镜像来源的系统盘/数据盘 ID
    diskSize: Any = None  # 磁盘容量。单位为 GiB
    enableImageIntegrityCheck: Optional[bool] = None  # 用于表示是否启用镜像完整性校验的标识
    fullECSDiskSize: Any = None # 云主机整机磁盘容量。单位为 GiB
    gpuImageCategory: Optional[str] = None  # GPU 镜像种类。取值范围（值：描述）：<br />pass_through：GPU 直通镜像，<br />vgpu：vGPU 镜像
    hasAcceptedSharedImages: Optional[bool] = None  # 用于表示私有镜像的共享列表中是否有镜像状态为 accepted 的共享镜像的标识
    imageClass: Optional[str] = None  # 镜像类别。取值范围（值：描述）：<br />BMS：物理机，<br />ECS：云主机
    imageDisplayName: Optional[str] = None  # 镜像展示名称
    imageID: Optional[str] = None  # 镜像 ID
    imageIntegrityCheckStatus: Optional[str] = None  # 镜像完整性校验状态，详见枚举值表格
    imageName: Optional[str] = None  # 镜像名称
    imageScene: Optional[str] = None  # 镜像场景。取值范围（值：描述）：<br />dev：开发工具，<br />ecommerce：电商，<br />gaming：游戏，<br />website：网站<br /><br />注意：镜像可适用于多场景，多个镜像场景之间以英文逗号（,）分隔，如 ecommerce,website
    imageShareCount: Any = None  # 私有镜像的共享数量
    imageSize: Any = None  # 镜像大小。单位为 byte
    imageSource: Optional[str] = None  # 私有镜像来源。取值范围（值：描述）：<br />cloud_server：云主机，<br />full_ecs：云主机整机，<br />image_file：镜像文件，<br />metal_server：物理机，<br />snapshot：云主机快照
    imageStatus: Optional[str] = None  # 镜像状态，详见枚举值表格
    imageSubcategory: Optional[str] = None  # 镜像子种类。取值范围（值：描述）：<br />app：云主机应用镜像，<br />thin_app：轻量型云主机应用镜像<br /><br />注意：镜像可适用于多子种类，多个镜像子种类之间以英文逗号（,）分隔，如 app,thin_app
    imageType: Optional[str] = None  # 镜像类型。取值范围（值：描述）：<br />（空，即 null）：系统盘镜像，<br />data_disk_image：数据盘镜像，<br />full_ecs_image：整机镜像，<br />iso_image：ISO 镜像
    imageVisibility: Optional[str] = None  # 镜像可见类型，详见枚举值表格
    maximumRAM: Any = None  # 最大内存。单位为 GiB
    minimumRAM: Any = None  # 最小内存。单位为 GiB
    osDistro: Optional[str] = None  # 操作系统发行版
    osType: Optional[str] = None  # 操作系统类型。取值范围（值：描述）：<br />linux：Linux 系操作系统，<br />windows：Windows 系操作系统
    osVersion: Optional[str] = None  # 操作系统版本
    projectID: Optional[str] = None  # 企业项目 ID
    sourceAccountID: Optional[str] = None  # 共享镜像提供者的账号 ID
    sourceServerID: Optional[str] = None  # 私有镜像来源的云主机/云主机快照/物理机 ID
    sourceUser: Optional[str] = None  # 共享镜像提供者
    supportOneClickSFSMount: Optional[bool] = None  # 用于表示是否支持一键挂载文件系统的标识
    supportXSSD: Optional[bool] = None  # 用于表示是否支持 XSSD 类型盘的标识
    taskID: Optional[str] = None  # 任务 ID
    updatedTime: Any = None  # 更新时间戳
    updatedTimeStr: Optional[str] = None  # 更新时间

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImageSharesReturnObjImagesResponse']:
        if not json_data:
            return None
        obj = CtimageListImageSharesReturnObjImagesResponse(
            appVersion=json_data.get('appVersion'),
            architecture=json_data.get('architecture'),
            azName=json_data.get('azName'),
            bootMode=json_data.get('bootMode'),
            chargeableImage=json_data.get('chargeableImage'),
            containerFormat=json_data.get('containerFormat'),
            createdTime=json_data.get('createdTime'),
            createdTimeStr=json_data.get('createdTimeStr'),
            cwaiType=json_data.get('cwaiType'),
            description=json_data.get('description'),
            destinationAccountID=json_data.get('destinationAccountID'),
            destinationUser=json_data.get('destinationUser'),
            diskFormat=json_data.get('diskFormat'),
            diskID=json_data.get('diskID'),
            diskSize=json_data.get('diskSize'),
            enableImageIntegrityCheck=json_data.get('enableImageIntegrityCheck'),
            fullECSDiskSize=json_data.get('fullECSDiskSize'),
            gpuImageCategory=json_data.get('gpuImageCategory'),
            hasAcceptedSharedImages=json_data.get('hasAcceptedSharedImages'),
            imageClass=json_data.get('imageClass'),
            imageDisplayName=json_data.get('imageDisplayName'),
            imageID=json_data.get('imageID'),
            imageIntegrityCheckStatus=json_data.get('imageIntegrityCheckStatus'),
            imageName=json_data.get('imageName'),
            imageScene=json_data.get('imageScene'),
            imageShareCount=json_data.get('imageShareCount'),
            imageSize=json_data.get('imageSize'),
            imageSource=json_data.get('imageSource'),
            imageStatus=json_data.get('imageStatus'),
            imageSubcategory=json_data.get('imageSubcategory'),
            imageType=json_data.get('imageType'),
            imageVisibility=json_data.get('imageVisibility'),
            maximumRAM=json_data.get('maximumRAM'),
            minimumRAM=json_data.get('minimumRAM'),
            osDistro=json_data.get('osDistro'),
            osType=json_data.get('osType'),
            osVersion=json_data.get('osVersion'),
            projectID=json_data.get('projectID'),
            sourceAccountID=json_data.get('sourceAccountID'),
            sourceServerID=json_data.get('sourceServerID'),
            sourceUser=json_data.get('sourceUser'),
            supportOneClickSFSMount=json_data.get('supportOneClickSFSMount'),
            supportXSSD=json_data.get('supportXSSD'),
            taskID=json_data.get('taskID'),
            updatedTime=json_data.get('updatedTime'),
            updatedTimeStr=json_data.get('updatedTimeStr'),
        )
        return obj

@dataclass
class CtimageListImageSharesReturnObjResponse:
    """成功时返回的数据"""
    images: Optional[List[Optional[CtimageListImageSharesReturnObjImagesResponse]]] = None  # 镜像列表
    currentPage: Any = None  # 当前页码
    currentCount: Any = None  # 当前页记录数
    totalPage: Any = None  # 总页数
    totalCount: Any = None  # 总记录数

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImageSharesReturnObjResponse']:
        if not json_data:
            return None
        
        images = None
        if "images" in json_data:
            image_list = json_data.get("images")
            if image_list is not None and isinstance(image_list, list):
                images = [CtimageListImageSharesReturnObjImagesResponse.from_json(img) for img in image_list]
                
        obj = CtimageListImageSharesReturnObjResponse(
            images=images,
            currentPage=json_data.get('currentPage'),
            currentCount=json_data.get('currentCount'),
            totalPage=json_data.get('totalPage'),
            totalCount=json_data.get('totalCount'),
        )
        return obj


@dataclass
class CtimageListImageSharesResponse:
    statusCode: Any = None  # 返回状态码，取值范围（值：描述）：<br />800：成功，<br />900：失败
    error: Optional[str] = None  # 错误码（product.module.code 三段式码）
    errorCode: Optional[str] = None  # 同 error 参数
    message: Optional[str] = None  # 英文描述信息
    description: Optional[str] = None  # 中文描述信息
    returnObj: Optional[CtimageListImageSharesReturnObjResponse] = None  # 成功时返回的数据

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImageSharesResponse']:
        if not json_data:
            return None

        return_obj = None
        if "returnObj" in json_data:
            returnObj = json_data.get("returnObj")
            if returnObj is not None:
                return_obj = CtimageListImageSharesReturnObjResponse.from_json(returnObj)

        obj = CtimageListImageSharesResponse(
            statusCode=json_data.get('statusCode'),
            error=json_data.get('error'),
            errorCode=json_data.get('errorCode'),
            message=json_data.get('message'),
            description=json_data.get('description'),
            returnObj=return_obj,
        )
        return obj


# 在您将 1 份私有镜像共享给其他用户之后，此接口可用于查询该私有镜像的共享列表。准备：<br />1. 在调用前需了解如何构造请求，可参见：如何调用 API - 构造请求<br />2. OpenAPI 请求需进行加密调用，可参见：如何调用 API - 认证鉴权<br />注意：<br />1. 若需要查询您的共享镜像（其他用户共享给您），则可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=23&api=4763&data=89&isNormal=1&vid=83" target="_blank">查询可以使用的镜像资源</a>接口<br />2. 在调用前，请您认真阅读此文档，包括但不限于参数描述中的“注意”部分
class CtimageListImageSharesApi:
    def __init__(self, ak: str = None, sk: str = None):
        self.endpoint = None
        self.credential = Credential(ak, sk)
    
    def set_endpoint(self, endpoint: str) -> None:
        self.endpoint = endpoint
    
    @staticmethod
    def do(credential: Credential, client: CtyunClient, endpoint: str, request: CtimageListImageSharesRequest) -> CtimageListImageSharesResponse:
        url = endpoint + "/v4/image/show-shared-list"
        params = {'imageID':request.imageID, 'regionID':request.regionID, 'pageNo':request.pageNo, 'pageSize':request.pageSize}
        try:
            request_dict = request.to_dict() if hasattr(request, 'to_dict') else request
            request_dict = {key: value for key, value in request_dict.items() if value is not None}
            response = client.get(url=url, params=params, header_params=request_dict, credential=credential)
            return CtimageListImageSharesResponse.from_json(response.json())
        except Exception as e:
            raise CtyunRequestException(str(e))
