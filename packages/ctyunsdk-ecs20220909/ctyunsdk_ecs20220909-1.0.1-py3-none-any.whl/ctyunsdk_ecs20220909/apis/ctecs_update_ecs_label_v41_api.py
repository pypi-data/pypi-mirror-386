from ctyunsdk_ecs20220909.core.client import CtyunClient
from ctyunsdk_ecs20220909.core.credential import Credential
from ctyunsdk_ecs20220909.core.exception import CtyunRequestException

from dataclasses import dataclass
from typing import Optional, List, Any


@dataclass
class CtecsUpdateEcsLabelV41LabelListRequest:
    labelKey: str  # 标签键
    labelValue: str  # 标签值

    def to_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if v is not None}


@dataclass
class CtecsUpdateEcsLabelV41Request:
    regionID: str  # 资源池ID，您可以查看<a href="https://www.ctyun.cn/document/10026730/10028695">地域和可用区</a>来了解资源池 <br />获取：<br /><span style="background-color: rgb(73, 204, 144);color: rgb(255,255,255);padding: 2px; margin:2px">查</span> <a  href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=5851&data=87">资源池列表查询</a>
    instanceID: str  # 云主机ID，您可以查看<a href="https://www.ctyun.cn/products/ecs">弹性云主机</a>了解云主机的相关信息<br />获取：<br /><span style="background-color: rgb(73, 204, 144);color: rgb(255,255,255);padding: 2px; margin:2px">查</span> <a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=8309&data=87">查询云主机列表</a><br /><span style="background-color: rgb(97, 175, 254);color: rgb(255,255,255);padding: 2px; margin:2px">创</span> <a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=8281&data=87">创建一台按量付费或包年包月的云主机</a><br /><span style="background-color: rgb(97, 175, 254);color: rgb(255,255,255);padding: 2px; margin:2px">创</span> <a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=8282&data=87">批量创建按量付费或包年包月云主机</a>
    action: str  # 操作类型，可选值：ADD（增加）、UPDATE（修改）、DELETE（删除）
    labelList: List[CtecsUpdateEcsLabelV41LabelListRequest]  # 标签列表

    def to_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if v is not None}

@dataclass
class CtecsUpdateEcsLabelV41Response:
    statusCode: Any  # 返回状态码（800为成功，900为失败）
    errorCode: Optional[str]  # 错误码，为product.module.code三段式码
    error: Optional[str]  # 错误码，为product.module.code三段式码
    message: Optional[str]  # 英文描述信息
    description: Optional[str]  # 中文描述信息
    returnObj: Optional[Any]

    @staticmethod
    def from_json(json_data: dict) -> 'CtecsUpdateEcsLabelV41Response':
        if not json_data:
            return None
        obj = CtecsUpdateEcsLabelV41Response(
            statusCode=json_data.get('statusCode'),
            errorCode=json_data.get('errorCode'),
            error=json_data.get('error'),
            message=json_data.get('message'),
            description=json_data.get('description'),
            returnObj=json_data.get('returnObj')
        )
        return obj


# &emsp;&emsp;构造请求：在调用前需要了解如何构造请求，详情查看<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=%u6784%u9020%u8BF7%u6C42&data=87&vid=81">构造请求</a><br />&emsp;&emsp;认证鉴权：openapi请求需要进行加密调用，详细查看<a href="https://eop.ctyun.cn/ebp/ctapiDocument/search?sid=25&api=%u8BA4%u8BC1%u9274%u6743&data=87&vid=81">认证鉴权</a><br />
class CtecsUpdateEcsLabelV41Api:
    def __init__(self, ak: str = None, sk: str = None):
        self.endpoint = None
        self.credential = Credential(ak, sk)
    
    def set_endpoint(self, endpoint: str) -> None:
        self.endpoint = endpoint
    
    @staticmethod
    def do(credential: Credential, client: CtyunClient, endpoint: str, request: CtecsUpdateEcsLabelV41Request) -> CtecsUpdateEcsLabelV41Response:
        url = endpoint + "/v4/ecs/label/update"
        try:
            request_dict = request.to_dict()
            response = client.post(url=url, data=request_dict, credential=credential)
            return CtecsUpdateEcsLabelV41Response.from_json(response.json())
        except Exception as e:
            raise CtyunRequestException(str(e))
