from typing import Optional
from core.client import CtyunClient
from core.credential import Credential

from .ctimage_create_ecs_system_disk_image_api import CtimageCreateEcsSystemDiskImageApi
from .ctimage_delete_image_api import CtimageDeleteImageApi
from .ctimage_list_image_shares_api import CtimageListImageSharesApi
from .ctimage_list_images_api import CtimageListImagesApi
from .ctimage_unshare_image_api import CtimageUnshareImageApi
from .ctimage_share_image_api import CtimageShareImageApi


ENDPOINT_NAME = "ctimage"

class Apis:
    _ctimagecreateecssystemdiskimageapi: CtimageCreateEcsSystemDiskImageApi
    _ctimagedeleteimageapi: CtimageDeleteImageApi
    _ctimagelistimagesharesapi: CtimageListImageSharesApi
    _ctimagelistimagesapi: CtimageListImagesApi
    _ctimageunshareimageapi: CtimageUnshareImageApi
    _ctimageshareimageapi: CtimageShareImageApi

    
    def __init__(self, endpoint_url: str, client: Optional[CtyunClient] = None):
        self.client = client or CtyunClient()
        self.endpoint = endpoint_url
    
        self._ctimagelistimagesapi = CtimageListImagesApi(self.client)
        self._ctimagelistimagesapi.set_endpoint(self.endpoint)
        self._ctimagecreateecssystemdiskimageapi = CtimageCreateEcsSystemDiskImageApi(self.client)
        self._ctimagecreateecssystemdiskimageapi.set_endpoint(self.endpoint)
        self._ctimagedeleteimageapi = CtimageDeleteImageApi(self.client)
        self._ctimagedeleteimageapi.set_endpoint(self.endpoint)
        self._ctimagelistimagesharesapi = CtimageListImageSharesApi(self.client)
        self._ctimagelistimagesharesapi.set_endpoint(self.endpoint)
        self._ctimageunshareimageapi = CtimageUnshareImageApi(self.client)
        self._ctimageunshareimageapi.set_endpoint(self.endpoint)
        self._ctimageshareimageapi = CtimageShareImageApi(self.client)
        self._ctimageshareimageapi.set_endpoint(self.endpoint)

    @property  # noqa
    def ctimagelistimagesapi(self) -> CtimageListImagesApi:  # noqa
        return self._ctimagelistimagesapi

    @property  # noqa
    def ctimagecreateecssystemdiskimageapi(self) -> CtimageCreateEcsSystemDiskImageApi:  # noqa
        return self._ctimagecreateecssystemdiskimageapi
        
    @property  # noqa
    def ctimagedeleteimageapi(self) -> CtimageDeleteImageApi:  # noqa
        return self._ctimagedeleteimageapi
        
    @property  # noqa
    def ctimagelistimagesharesapi(self) -> CtimageListImageSharesApi:  # noqa
        return self._ctimagelistimagesharesapi

    @property  # noqa
    def ctimageunshareimageapi(self) -> CtimageUnshareImageApi:  # noqa
        return self._ctimageunshareimageapi

    @property  # noqa
    def ctimageshareimageapi(self) -> CtimageShareImageApi:  # noqa
        return self._ctimageshareimageapi

