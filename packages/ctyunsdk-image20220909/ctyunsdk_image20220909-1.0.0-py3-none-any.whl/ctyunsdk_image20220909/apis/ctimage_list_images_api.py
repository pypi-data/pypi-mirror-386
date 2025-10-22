from typing import List, Optional, Dict, Any
from core.client import CtyunClient
from core.credential import Credential
from core.exception import CtyunRequestException

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class CtimageListImagesRequest:
    regionID: str  # 资源池 ID。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=5851&data=87&isNormal=1&vid=81" target="_blank">资源池列表查询</a>接口来查询您可见的资源池的列表
    azName: Optional[str] = None  # 可用区名称。注意：<br />1. 仅在多可用区资源池下对物理机镜像生效。请不要在其它场景使用此参数<br />2. 可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=5855&data=87&isNormal=1&vid=81" target="_blank">资源池可用区查询</a>接口查询多可用区资源池的可用区信息。若响应的 returnObj 中的 zoneList 是空的可用区列表，则所指定的资源池是单可用区资源池
    cwaiType: Optional[str] = None  # 云骁智算云主机节点类型。取值范围（值：描述）：<br />control：控制面云主机节点，<br />node：GPU 云主机节点<br /><br />注意：仅在 imageVisibilityCode 参数值为 1（公共镜像）时用于限制仅显示适用于指定云骁智算云主机节点类型的公共镜像，未指定节点类型时不启用此限制。请不要在其它场景使用此参数
    flavorName: Optional[str] = None  # 规格名称。注意：<br />1. 可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=8327&data=87&isNormal=1&vid=81" target="_blank">查询一个或多个云主机规格资源</a>接口来查询您可以使用的云主机规格（如 s7.small.1）<br />2. 可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=11998&data=87&isNormal=1&vid=81" target="_blank">查询轻量型云主机的规格套餐资源</a>接口来查询您可以使用的轻量型云主机规格（如 lite1.fix.small.1）
    imageName: Optional[str] = None  # 镜像名称。注意：仅在 imageVisibilityCode 参数值为 0（私有镜像）时生效。
    imageScene: Optional[str] = None  # 镜像场景。取值范围（值：描述）：<br />dev：开发工具，<br />ecommerce：电商，<br />gaming：游戏，<br />website：网站<br /><br />注意：仅在 imageVisibilityCode 参数值为 5（应用镜像）时用于筛选应用镜像，未指定镜像场景时不启用此筛选。请不要在其它场景使用此参数
    imageStatus: Optional[str] = None  # 镜像状态。取值范围（值：描述）：<br />accepted：已接受共享镜像，<br />rejected：已拒绝共享镜像，<br />waiting：等待接受/拒绝共享镜像<br /><br />注意：仅在 imageVisibilityCode 参数值为 2（共享镜像）时生效，未指定镜像状态时默认显示镜像状态为 accepted 或 waiting 的共享镜像。请不要在其它场景使用此参数
    imageSubcategory: Optional[str] = None  # 镜像子种类。取值范围（值：描述）：<br />app：云主机应用镜像，<br />thin_app：轻量型云主机应用镜像<br /><br />注意：仅在 imageVisibilityCode 参数值为 5（应用镜像）时用于筛选应用镜像，未指定镜像子种类时不启用此筛选。请不要在其它场景使用此参数
    imageType: Optional[str] = None  # 镜像类型。取值范围（值：描述）：<br />data_disk_image：数据盘镜像。<br />others：其它类型镜像。<br />注意：仅在 imageVisibilityCode 参数值为 0（私有镜像）时生效，未指定镜像类型时不启用此筛选。请不要在其它场景使用此参数。
    imageVisibilityCode: Any = None  # 镜像可见类型代码，详见枚举值表格
    osTypeCode: Any = None # 操作系统类型代码。取值范围（值：描述）：<br />1：Linux 系操作系统。<br />2：Windows 系操作系统。<br />注意：在 imageVisibilityCode 参数值为 2（共享镜像）时不生效，未指定操作系统类型代码时不启用此筛选。
    pageNo: Any = None# 页码。取值范围：最小 1（默认值）
    pageSize: Any = None # 每页记录数目。取值范围：最小 1，最大 200，默认 10
    projectID: Optional[str] = None  # 企业项目 ID。可使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=77&api=7246&data=114&isNormal=1&vid=107" target="_blank">查询企业项目列表</a>接口来查询您可以使用的企业项目 ID。注意：仅在 imageVisibilityCode 参数值为 0（私有镜像）时生效。请不要在其它场景使用此参数
    queryContent: Optional[str] = None  # 查询内容

    def to_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if v is not None}


@dataclass
class CtimageListImagesReturnObjImagesSourceDisksResponse:
    cmkID: Optional[str]  # 磁盘加密密钥ID
    diskID: Optional[str]  # 磁盘ID
    diskName: Optional[str]  # 磁盘名称
    diskSize: Optional[str]  # 磁盘大小
    diskType: Optional[str]  # 磁盘类型
    isEncrypt: Optional[str]  # 磁盘是否加密的标识
    isSystemVolume: Optional[str]  # 是否为系统盘

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImagesReturnObjImagesSourceDisksResponse']:
        if not json_data:
            return None

        return CtimageListImagesReturnObjImagesSourceDisksResponse(
            cmkID=json_data.get('cmkID'),
            diskID=json_data.get('diskID'),
            diskName=json_data.get('diskName'),
            diskSize=json_data.get('diskSize'),
            diskType=json_data.get('diskType'),
            isEncrypt=json_data.get('isEncrypt'),
            isSystemVolume=json_data.get('isSystemVolume')
        )


@dataclass
class CtimageListImagesReturnObjImagesResponse:
    appVersion: Optional[str]  # 应用版本
    appCategory: Optional[str]  # 应用种类。取值范围（值：描述）：<br />Docker：Docker 应用种类。<br />Palworld：幻兽帕鲁应用种类。<br />WordPress：WordPress 应用种类。
    architecture: Optional[str]  # 系统架构。取值范围（值：描述）：<br />aarch64：AArch64 架构，<br />loongarch64：LoongArch64 架构，<br />sw_64：sw_64 架构，<br />x86_64：x86_64 架构
    azName: Optional[str]  # 在多可用区资源池下物理机镜像的可用区名称
    bootMode: Optional[str]  # x86_64 架构非数据盘镜像的启动方式。取值范围（值：描述）：<br />bios：BIOS 启动方式，<br />uefi：UEFI 启动方式
    chargeableImage: Optional[bool]  # 用于表示是否是收费镜像的标识
    cmkID: Optional[str]  # 密钥 ID。
    containerFormat: Optional[str]  # 容器格式
    cpuType: Optional[str]  # CPU 类型。详见枚举值表格。
    createdTime: Any  # 创建时间戳
    createdTimeStr: Optional[str]  # 创建时间
    cwaiType: Optional[str]  # 云骁智算云主机节点类型。取值范围（值：描述）：<br />control：控制面云主机节点，<br />node：GPU 云主机节点<br /><br />注意：镜像可适用于多节点类型，多个云骁智算云主机节点类型之间以英文逗号（,）分隔，如 control,node
    description: Optional[str]  # 描述信息
    destinationAccountID: Optional[str]  # 共享镜像接受者的账号 ID
    diskFormat: Optional[str]  # 磁盘格式。取值范围（值：描述）：<br />qcow2：QCOW2 格式，<br />raw：RAW 格式，<br />vhd：VHD 格式，<br />vmdk：VMDK 格式
    diskID: Optional[str]  # 私有镜像来源的系统盘/数据盘 ID
    diskSize: Any  # 磁盘容量。单位为 GiB
    enableImageIntegrityCheck: Optional[bool]  # 用于表示是否启用镜像完整性校验的标识
    fullECSDiskSize: Any  # 云主机整机磁盘容量。单位为 GiB
    gpuImageCategory: Optional[str]  # GPU 镜像种类。取值范围（值：描述）：<br />pass_through：GPU 直通镜像，<br />vgpu：vGPU 镜像
    gpuType: Any  # GPU 类型。取值范围（值：描述）：<br />1：寒武纪 GPU 直通。<br />2：昇腾 GPU 直通。<br />3：英伟达 T4/V100 vGPU。<br />4：英伟达 A10/V100S vGPU。
    hasAcceptedSharedImages: Optional[bool]  # 用于表示私有镜像的共享列表中是否有镜像状态为 accepted 的共享镜像的标识
    imageCategory: Optional[str]  # 镜像种类。取值范围（值：描述）：<br />bare：裸金属镜像。<br />basic：基础镜像。<br />exclusive：独占镜像。<br />paas：PaaS 镜像。<br />security：安全镜像。
    imageClass: Optional[str]  # 镜像类别。取值范围（值：描述）：<br />BMS：物理机，<br />ECS：云主机
    imageDisplayName: Optional[str]  # 镜像展示名称
    imageID: Optional[str]  # 镜像 ID
    imageIntegrityCheckStatus: Optional[str]  # 镜像完整性校验状态，详见枚举值表格
    imageName: Optional[str]  # 镜像名称
    imageProvider: Optional[str]  # 市场镜像提供方。CN_CTCLOUD_001 代表天翼云科技有限公司。
    imageScene: Optional[str]  # 镜像场景。取值范围（值：描述）：<br />dev：开发工具，<br />ecommerce：电商，<br />gaming：游戏，<br />website：网站<br /><br />注意：镜像可适用于多场景，多个镜像场景之间以英文逗号（,）分隔，如 ecommerce,website
    imageShareCount: Any  # 私有镜像的共享数量
    imageSize: Any  # 镜像大小。单位为 byte
    imageSource: Optional[str]  # 私有镜像来源。取值范围（值：描述）：<br />cloud_server：云主机，<br />full_ecs：云主机整机，<br />image_file：镜像文件，<br />metal_server：物理机，<br />snapshot：云主机快照
    imageStatus: Optional[str]  # 镜像状态，详见枚举值表格
    imageSubcategory: Optional[str]  # 镜像子种类。取值范围（值：描述）：<br />app：云主机应用镜像，<br />thin_app：轻量型云主机应用镜像<br /><br />注意：镜像可适用于多子种类，多个镜像子种类之间以英文逗号（,）分隔，如 app,thin_app
    imageType: Optional[str]  # 镜像类型。取值范围（值：描述）：<br />（空，即 null）：系统盘镜像，<br />data_disk_image：数据盘镜像，<br />full_ecs_image：整机镜像，<br />iso_image：ISO 镜像
    imageVisibility: Optional[str]  # 镜像可见类型，详见枚举值表格
    isEncrypt: Optional[bool]  # 用于表示私有镜像是否加密的标识。
    marketClassI: Optional[str]  # 云镜像市场一级分类。详见枚举值表格。
    marketClassII: Optional[str]  # 云镜像市场二级分类。详见枚举值表格。
    maximumCPUCoreCount: Any  # 最大 CPU 核数。
    maximumRAM: Any  # 最大内存。单位为 GiB
    minimumCPUCoreCount: Any  # 最小 CPU 核数。
    minimumRAM: Any  # 最小内存。单位为 GiB
    osDistro: Optional[str]  # 操作系统发行版
    osType: Optional[str]  # 操作系统类型。取值范围（值：描述）：<br />linux：Linux 系操作系统，<br />windows：Windows 系操作系统
    osVersion: Optional[str]  # 操作系统版本
    projectID: Optional[str]  # 企业项目 ID
    sourceAccountID: Optional[str]  # 共享镜像提供者的账号 ID
    sourceDisks: Optional[List[Optional[CtimageListImagesReturnObjImagesSourceDisksResponse]]]  # 关联云盘信息。
    sourceServerID: Optional[str]  # 私有镜像来源的云主机/云主机快照/物理机 ID
    supportOneClickSFSMount: Optional[bool]  # 用于表示是否支持一键挂载文件系统的标识
    supportXSSD: Optional[bool]  # 用于表示是否支持 XSSD 类型盘的标识
    taskID: Optional[str]  # 任务 ID
    trustedImage: Optional[bool]  # 用于表示是否属于可信镜像的标识。
    updatedTime: Any  # 更新时间戳
    updatedTimeStr: Optional[str]  # 更新时间
    visibleImage: Optional[bool]  # 用于表示是否是可见镜像的标识。


    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImagesReturnObjImagesResponse']:
        if not json_data:
            return None

        # 处理sourceDisks字段
        source_disks = None
        if "sourceDisks" in json_data:
            disks_data = json_data.get("sourceDisks")
            if disks_data is not None and isinstance(disks_data, list):
                source_disks = [CtimageListImagesReturnObjImagesSourceDisksResponse.from_json(disk)
                                for disk in disks_data if disk is not None]
        obj = CtimageListImagesReturnObjImagesResponse(
            appVersion=json_data.get('appVersion'),
            appCategory=json_data.get('appCategory'),
            architecture=json_data.get('architecture'),
            azName=json_data.get('azName'),
            bootMode=json_data.get('bootMode'),
            chargeableImage=json_data.get('chargeableImage'),
            cmkID=json_data.get('cmkID'),
            containerFormat=json_data.get('containerFormat'),
            cpuType=json_data.get('cpuType'),
            createdTime=json_data.get('createdTime'),
            createdTimeStr=json_data.get('createdTimeStr'),
            cwaiType=json_data.get('cwaiType'),
            description=json_data.get('description'),
            destinationAccountID=json_data.get('destinationAccountID'),
            diskFormat=json_data.get('diskFormat'),
            diskID=json_data.get('diskID'),
            diskSize=json_data.get('diskSize'),
            enableImageIntegrityCheck=json_data.get('enableImageIntegrityCheck'),
            fullECSDiskSize=json_data.get('fullECSDiskSize'),
            gpuImageCategory=json_data.get('gpuImageCategory'),
            gpuType=json_data.get('gpuType'),
            hasAcceptedSharedImages=json_data.get('hasAcceptedSharedImages'),
            imageCategory=json_data.get('imageCategory'),
            imageClass=json_data.get('imageClass'),
            imageDisplayName=json_data.get('imageDisplayName'),
            imageID=json_data.get('imageID'),
            imageIntegrityCheckStatus=json_data.get('imageIntegrityCheckStatus'),
            imageName=json_data.get('imageName'),
            imageProvider=json_data.get('imageProvider'),
            imageScene=json_data.get('imageScene'),
            imageShareCount=json_data.get('imageShareCount'),
            imageSize=json_data.get('imageSize'),
            imageSource=json_data.get('imageSource'),
            imageStatus=json_data.get('imageStatus'),
            imageSubcategory=json_data.get('imageSubcategory'),
            imageType=json_data.get('imageType'),
            imageVisibility=json_data.get('imageVisibility'),
            isEncrypt=json_data.get('isEncrypt'),
            marketClassI=json_data.get('marketClassI'),
            marketClassII=json_data.get('marketClassII'),
            maximumCPUCoreCount=json_data.get('maximumCPUCoreCount'),
            maximumRAM=json_data.get('maximumRAM'),
            minimumCPUCoreCount=json_data.get('minimumCPUCoreCount'),
            minimumRAM=json_data.get('minimumRAM'),
            osDistro=json_data.get('osDistro'),
            osType=json_data.get('osType'),
            osVersion=json_data.get('osVersion'),
            projectID=json_data.get('projectID'),
            sourceAccountID=json_data.get('sourceAccountID'),
            sourceDisks=source_disks,
            sourceServerID=json_data.get('sourceServerID'),
            supportOneClickSFSMount=json_data.get('supportOneClickSFSMount'),
            supportXSSD=json_data.get('supportXSSD'),
            taskID=json_data.get('taskID'),
            trustedImage=json_data.get('trustedImage'),
            updatedTime=json_data.get('updatedTime'),
            updatedTimeStr=json_data.get('updatedTimeStr'),
            visibleImage=json_data.get('visibleImage')
        )
        return obj

@dataclass
class CtimageListImagesReturnObjResponse:
    """成功时返回的数据"""
    images: Optional[List[Optional[CtimageListImagesReturnObjImagesResponse]]] = None  # 镜像列表
    currentPage: Any = None  # 当前页码
    currentCount: Any = None  # 当前页记录数
    totalPage: Any = None  # 总页数
    totalCount: Any = None  # 总记录数

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImagesReturnObjResponse']:
        if not json_data:
            return None

        images = None
        if "images" in json_data:
            image_list = json_data.get("images")
            if image_list is not None and isinstance(image_list, list):
                images = [CtimageListImagesReturnObjImagesResponse.from_json(img) for img in image_list]

        obj = CtimageListImagesReturnObjResponse(
            images=images,
            currentPage=json_data.get('currentPage'),
            currentCount=json_data.get('currentCount'),
            totalPage=json_data.get('totalPage'),
            totalCount=json_data.get('totalCount'),
        )
        return obj

@dataclass
class CtimageListImagesResponse:
    statusCode: Any = None  # 返回状态码，取值范围（值：描述）：<br />800：成功，<br />900：失败
    error: Optional[str] = None  # 错误码（product.module.code 三段式码）
    errorCode: Optional[str] = None  # 同 error 参数
    message: Optional[str] = None  # 英文描述信息
    description: Optional[str] = None  # 中文描述信息
    returnObj: Optional[CtimageListImagesReturnObjResponse] = None # 成功时返回的数据

    @staticmethod
    def from_json(json_data: dict) -> Optional['CtimageListImagesResponse']:
        if not json_data:
            return None

        return_obj = None
        if "returnObj" in json_data:
            returnObj = json_data.get("returnObj")
            if returnObj is not None:
                return_obj = CtimageListImagesReturnObjResponse.from_json(returnObj)

        obj = CtimageListImagesResponse(
            statusCode=json_data.get('statusCode'),
            error=json_data.get('error'),
            errorCode=json_data.get('errorCode'),
            message=json_data.get('message'),
            description=json_data.get('description'),
            returnObj=return_obj,
        )
        return obj


# 根据规格名称、镜像可见类型等，查询可以使用的镜像资源<br />准备：<br />1. 在调用前需了解如何构造请求，可参见：如何调用 API - 构造请求<br />2. OpenAPI 请求需进行加密调用，可参见：如何调用 API - 认证鉴权<br />注意：<br />1. 推荐使用<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=16&api=4577&data=97&isNormal=1&vid=91" target="_blank">查询物理机镜像</a>接口来查询物理机镜像<br />2. 在调用前，请您认真阅读此文档，包括但不限于参数描述中的“注意”部分
class CtimageListImagesApi:
    def __init__(self, ak: str = None, sk: str = None):
        self.endpoint = None
        self.credential = Credential(ak, sk)
    
    def set_endpoint(self, endpoint: str) -> None:
        self.endpoint = endpoint
    
    @staticmethod
    def do(credential: Credential, client: CtyunClient, endpoint: str, request: CtimageListImagesRequest) -> CtimageListImagesResponse:
        url = endpoint + "/v4/image/list"
        params = {'regionID':request.regionID, 'azName':request.azName, 'cwaiType':request.cwaiType, 'flavorName':request.flavorName, 'imageName':request.imageName, 'imageScene':request.imageScene, 'imageStatus':request.imageStatus, 'imageSubcategory':request.imageSubcategory, 'imageType':request.imageType, 'imageVisibilityCode':request.imageVisibilityCode, 'osTypeCode':request.osTypeCode, 'pageNo':request.pageNo, 'pageSize':request.pageSize, 'projectID':request.projectID, 'queryContent':request.queryContent}
        try:
            request_dict = request.to_dict() if hasattr(request, 'to_dict') else request
            request_dict = {key: value for key, value in request_dict.items() if value is not None}
            response = client.get(url=url, params=params, header_params=request_dict, credential=credential)
            return CtimageListImagesResponse.from_json(response.json())
        except Exception as e:
            raise CtyunRequestException(str(e))
