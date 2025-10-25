from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from aiexec.services.factory import ServiceFactory
from aiexec.services.store.service import StoreService

if TYPE_CHECKING:
    from wfx.services.settings.service import SettingsService


class StoreServiceFactory(ServiceFactory):
    def __init__(self) -> None:
        super().__init__(StoreService)

    @override
    def create(self, settings_service: SettingsService):
        return StoreService(settings_service)
