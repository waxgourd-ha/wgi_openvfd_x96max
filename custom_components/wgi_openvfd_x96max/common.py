import os
import logging
import json
import aiofiles
import yaml
import zipfile
import shutil
from typing import Optional, Callable, Awaitable

from packaging import version

from aiohttp import web
from aiohttp.client import ClientSession, ClientTimeout

from homeassistant.config import async_hass_config_yaml

from homeassistant.helpers import (
    entity,
    storage,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import  Platform
from homeassistant.const import __version__ as HA_VERSION 
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import Any, Mapping, StateType
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util.yaml import dump, load_yaml
from homeassistant.core import HomeAssistant, State
from .const import (
    CONF_BASE_KEY,
    DOMAIN,
    OPENVFD_TIME_ZONE_UTC_NAME,
    OPENVFD_SERVER_CONTROL,
    OPENVFD_SERVER_STATE_ACTION,
    YAML_FILE,
    VERSION_UPDATE_GITCODE_URL,
)

import packaging

_LOGGER = logging.getLogger(__name__)

def compare_version(version1, version2) -> int:
    v1 = version.parse(version1)
    v2 = version.parse(version2)
    if v1 < v2:
        return -1
    if v1 > v2:
        return 1
    return 0

def remove_file(path):
    if os.path.isfile(path):
        os.remove(path)

def remove_dir(path):
    try:
        shutil.rmtree(path)
    except Exception:
        _LOGGER.warning("remove dir fail.")

class ApiServer:

    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self._url = "curl -s -L -S http://127.0.0.1:5000/openvfd/service?mode="

    async def get_data(self,mode) -> dict:
        try:
            result = os.popen(f"{self._url}{mode}")
            _data = result.read()
            _json_data = json.loads(_data)
            return _json_data
        except:
            pass
        # API 错误时默认返回启用状态
        return {'enable': 1, 'status_code': 0}

    async def cmd(self, mode) -> None:
        try:
            os.system(f"{self._url}{mode}")
        except:
            pass

async def async_read_file(file_path):
    if not os.path.isfile(file_path):
        return None
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
        return content

async def read_json_async(file_path):
    if not os.path.isfile(file_path):
        return None
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
        return json.loads(content)


async def read_yaml_async(file_path):
    if not os.path.isfile(file_path):
        return None
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
        return yaml.safe_load(content)

def yaml_read(path):
    """Read YAML helper."""
    if not os.path.isfile(path):
        return None

    return load_yaml(path)


def yaml_write(path, data):
    """Write YAML helper."""
    # Do it before opening file. If dump causes error it will now not
    # truncate the file.
    contents = dump(data)
    write_utf8_file_atomic(path, contents)


async def get_device_entity_info(hass: HomeAssistant, device_id: str):
    _devices = hass.data[DOMAIN]['device']
    if len(_devices) >0:
        for device in _devices:
            if device_id == device.id:
                return device

def parse_version(hass: HomeAssistant, version: str):
    version_entity = hass.states.get("system.health")
    if version_entity:
        current_version = version_entity.attributes.get("version", "2025.5.3")
    else:
        # 方案2：从homeassistant.const获取（部分旧版本可用）
        current_version = HA_VERSION if "HA_VERSION" in globals() else "2025.5.3"
    _LOGGER.debug(f"Current Home Assistant version: {current_version}, Required version: {version}")
    is_supported = packaging.version.parse(current_version) >= packaging.version.parse(version)
    return is_supported

async def common_setup_entry(
        hass: HomeAssistant,
        devices: list,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        description: EntityDescription,
        mentity: Entity,
        platform_type: Platform | str,
        log: logging = None,
        entity_validator: Optional[Callable[[dict], bool]] = None,
        entity_processor: Optional[Callable[[dict], dict]] = None,
        post_create_hook: Optional[Callable[[Entity], Awaitable[None]]] = None
) -> None:
    """通用实体设置入口函数。
    
    Args:
        hass: Home Assistant 实例
        devices: 设备列表
        entry: 配置入口
        async_add_entities: 添加实体的回调函数
        description: 实体描述类
        mentity: 实体类
        platform_type: 平台类型
        log: 日志记录器
        entity_validator: 可选的实体验证函数
        entity_processor: 可选的实体处理函数
        post_create_hook: 可选的实体创建后处理函数
    """
    if log is None:
        log = logging.getLogger(__name__)
    
    is_supported = parse_version(hass, "2025.6.0")
    entities = []
    
    for device_info in devices:
        try:
            device_id = device_info.get('device_id')
            if not device_id:
                log.warning("Device ID not found in device info")
                continue

            device_entry = await get_device_entity_info(hass, device_id)
            if not device_entry:
                log.warning("Device entry not found for device %s", device_id)
                continue

            device_entities = device_info.get('entities', [])
            for entity_info in device_entities:
                if entity_info.get('platform') != platform_type:
                    continue

                if entity_validator and not entity_validator(entity_info):
                    log.warning(
                        "Entity validation failed for %s",
                        entity_info.get('id')
                    )
                    continue

                try:
                    entity = await _create_entity(
                        hass=hass,
                        entry=entry,
                        device_entry=device_entry,
                        entity_info=entity_info,
                        description_class=description,
                        entity_class=mentity,
                        is_supported=is_supported,
                        log=log
                    )

                    if entity_processor:
                        entity_info = entity_processor(entity_info)

                    if post_create_hook:
                        await post_create_hook(entity)

                    entities.append(entity)
                    log.debug(
                        "Created entity %s for device %s",
                        entity_info.get('id'),
                        device_id
                    )
                except Exception as e:
                    log.error(
                        "Error creating entity %s: %s",
                        entity_info.get('id'),
                        str(e),
                        exc_info=True
                    )
        except Exception as e:
            log.error(
                "Error processing device %s: %s",
                device_info.get('device_id'),
                str(e),
                exc_info=True
            )

    if entities:
        async_add_entities(entities, True)
        log.info(
            "Successfully created %d entities for platform %s",
            len(entities),
            platform_type
        )

async def _create_entity(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_entry: dr.DeviceEntry,
    entity_info: dict,
    description_class: EntityDescription,
    entity_class: Entity,
    is_supported: bool,
    log: logging.Logger
) -> Entity:
    """创建单个实体。
    
    Args:
        hass: Home Assistant 实例
        entry: 配置入口
        device_entry: 设备入口
        entity_info: 实体信息
        description_class: 实体描述类
        entity_class: 实体类
        is_supported: 是否支持新版本
        log: 日志记录器
    
    Returns:
        创建的实体实例
    """
    entity_id = entity_info.get('id')
    if not entity_id:
        raise ValueError("Entity ID not found in entity info")

    # 创建实体描述
    description = description_class(
        key=entity_id,
        force_update=True,
        icon=entity_info.get('icon'),
        has_entity_name=True,
        name=entity_info.get('name'),
        unit_of_measurement=entity_info.get('unit_of_measurement'),
    )

    # 创建设备信息
    device_info = dr.DeviceInfo(
        identifiers=device_entry.identifiers,
        name=device_entry.name,
        entry_type=device_entry.entry_type,
        manufacturer=device_entry.manufacturer,
        model=device_entry.model,
        sw_version=device_entry.sw_version,
        hw_version=device_entry.hw_version,
        via_device_id=device_entry.via_device_id,
        configuration_url=device_entry.configuration_url,
    )

    # 创建实体 - 只传递 WgiEntity 实际使用的参数
    return entity_class(
        entity_id=entity_id,
        device_info=device_info,
        entity_description=description,
        state=entity_info.get('state')
    )

class WgiEntity(Entity):
    """ Entity class."""

    def __init__(self, **values: Any) -> None:
        """Initialize an entity."""
        self._values = values

        if "entity_id" in values:
            self.entity_id = values["entity_id"]

        # 从 entity_description 提取常用属性到 _values
        if "entity_description" in values and values["entity_description"]:
            desc = values["entity_description"]
            if not hasattr(self, '_attr_translation_key') and hasattr(desc, 'translation_key'):
                self._attr_translation_key = desc.translation_key
            if not hasattr(self, '_attr_entity_category') and hasattr(desc, 'entity_category'):
                self._attr_entity_category = desc.entity_category

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._handle("available")

    @property
    def capability_attributes(self) -> Mapping[str, Any] | None:
        """Info about capabilities."""
        return self._handle("capability_attributes")

    @property
    def device_class(self) -> str | None:
        """Info how device should be classified."""
        return self._handle("device_class")

    @property
    def device_info(self) :
        """Info how it links to a device."""
        return self._handle("device_info")

    @property
    def entity_category(self) -> entity.EntityCategory | None:
        """Return the entity category."""
        return self._handle("entity_category")

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return self._handle("extra_state_attributes")

    @property
    def has_entity_name(self) -> bool:
        """Return the has_entity_name name flag."""
        return self._handle("has_entity_name")

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._handle("entity_registry_enabled_default")

    @property
    def entity_registry_visible_default(self) -> bool:
        """Return if the entity should be visible when first added to the entity registry."""
        return self._handle("entity_registry_visible_default")

    @property
    def icon(self) -> str | None:
        """Return the suggested icon."""
        return self._handle("icon")

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return self._handle("name")

    @property
    def original_icon(self) -> str | None:
        """Return the suggested icon."""
        return self._handle("original_icon")

    @property
    def original_name(self) -> str | None:
        """Return the name of the entity."""
        return self._handle("original_name")

    @property
    def should_poll(self) -> bool:
        """Return the ste of the polling."""
        return self._handle("should_poll")

    @property
    def state(self) -> StateType:
        """Return the state of the entity."""
        return self._handle("state")

    @property
    def supported_features(self) -> int | None:
        """Info about supported features."""
        return self._handle("supported_features")

    @property
    def translation_key(self) -> str | None:
        """Return the translation key."""
        return self._handle("translation_key")

    @property
    def unique_id(self) -> str | None:
        """Return the unique ID of the entity."""
        return self._handle("unique_id")

    @property
    def unit_of_measurement(self) -> str | None:
        """Info on the units the entity state is in."""
        return self._handle("unit_of_measurement")

    def _handle(self, attr: str) -> Any:
        """Return attribute value."""
        if attr in self._values:
            return self._values[attr]

        # 从 entity_description 中获取属性
        if "entity_description" in self._values and self._values["entity_description"]:
            desc = self._values["entity_description"]
            if hasattr(desc, attr):
                value = getattr(desc, attr)
                if value is not None:
                    return value

        return getattr(super(), attr, None)

async def get_version_info_last_from_gitcode() -> str | None:
    try:
        header={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(VERSION_UPDATE_GITCODE_URL,headers=header) as resp:
                if resp.status == 200:
                    return await resp.text()

    except TimeoutError:
        _LOGGER.error("Download failed.")
    return None


def file_write(filepath,data):
    with open(filepath, 'wb') as f:
        f.write(data)
    f.close()

def copytree(src, dst):
    shutil.copytree(src, dst,dirs_exist_ok=True)

async def down_zip_file(hass,url,filename) -> bool:
    header={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    async with ClientSession() as session:
        async with session.get(url,headers=header) as resp:
            if resp.status == 200:
                data = await resp.read()
                await hass.async_add_executor_job(file_write, filename,data)

def unzip_file(zip, extract):
    if not os.path.isfile(zip):
        raise OSError("No zip package.")
    with zipfile.ZipFile(zip, 'r') as zip_ref:
        zip_ref.extractall(extract)

async def get_version_last_from_gitcode() -> str | None:
    data = await get_version_info_last_from_gitcode()
    try:
        if data is not None:
            info = json.loads(data)
            if "version" in info:
                return info.get("version")
    except Exception:
        pass
    return None

class ConfigYaml:

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._yaml_config = {}

    @property
    def yaml_config(self):
        return self._yaml_config

    ## 读取配置
    async def get_integration_config(self):
        ### 读取配置
        self._yaml_config = await self.get_integration_config_last()
        return self._yaml_config

    async def get_integration_config_last(self):
        config = await async_hass_config_yaml(self._hass)
        return config.get(CONF_BASE_KEY,{})

async def async_common_setup_entry(
        hass: HomeAssistant,
        devices: list,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        description: EntityDescription,
        mentity: WgiEntity,
        platform_type: Platform | str,
        log: logging = None
) -> None:
    await common_setup_entry(hass, devices, entry, async_add_entities, description, mentity, platform_type, log)

def send_state(hass:HomeAssistant, entity_id,state="on"):
    new_state = State(entity_id,state)
    hass.states.async_set(entity_id, new_state.state, new_state.attributes)



class EntityManage:

    def __init__(self, hass: HomeAssistant) -> None:
        self._server_state = None
        self._api = None
        self._hass = hass
        self._hass_data = hass.data[DOMAIN]

    def get_entity(self, entity_id: str) -> dict:
        entity = {}
        _devices = self._hass_data['device_info']
        if len(_devices) > 0:
            for _device in _devices:
                _entities = _device.get('entities')
                if len(_entities) > 0:
                    for _entity in _entities:
                        _id = _entity.get('id')
                        if _id == entity_id:
                            entity = _entity
                            return entity

        return entity

    def action_state(self):
        is_enable = -1
        if self._server_state is not None:
            is_enable = self._server_state.get('status_code',-1)
        return is_enable

    def openvfd_server_state(self):
        is_enable = 0
        if self._server_state is not None:
            is_enable = self._server_state.get('enable',0)
        return is_enable


    async def update_server_init(self):
        await self.update_server()
        await self.update_server_action()

    async def async_get_entity(self, entity_id: str) -> dict:
        return self.get_entity(entity_id)


    def get_entity_attr(self,entity_id: str, attr: str="state", default=''):
        _entity = self.get_entity(entity_id)
        if attr in _entity:
            return _entity.get(attr,default)
        return default

    async def async_get_entity_attr(self,entity_id: str, attr: str="state", default=''):
        _entity = await self.async_get_entity(entity_id)
        if attr in _entity:
            return _entity.get(attr,default)
        return default

    async def update_entity_state(self,entity_id: str, attr: str="state", state='on'):
        _entity = await self.async_get_entity(entity_id)
        if _entity:
            _entity[attr] = state

    async def get_update_server_api(self):
        self._api = ApiServer(self._hass)
        self._server_state = await self._api.get_data('status')

    async def action(self,mode):
        if self._server_state is None:
            await self.get_update_server_api()
        return await self._api.get_data(mode)

    async def update_server(self):
        if self._server_state is None:
            await self.get_update_server_api()
        is_enable = self._server_state.get('enable',1)
        await self.update_server_state(is_enable)

    async def update_server_action(self):
        if self._server_state is None:
            await self.get_update_server_api()
        is_enable = self._server_state.get('status_code',-1)
        await self.update_server_action_state(is_enable)

    async def update_server_action_state(self, is_enable=-1):
        if str(is_enable) == '0':

            await self.update_entity_state(f"switch.{OPENVFD_SERVER_STATE_ACTION}",'state','on')
        else:
            await self.update_entity_state(f"switch.{OPENVFD_SERVER_STATE_ACTION}",'state','off')

    async def update_server_action_cmd(self, is_enable=-1):
        if str(is_enable) == '0':
            return await self.action('start')
        else:
            return await self.action('stop')

    async def update_server_restart(self):
        data = await self.action('restart')
        is_enable = data.get('status_code',-1)
        await self.update_server_action_state(is_enable)
        if str(is_enable) != '-1':
            send_state(self._hass, f"switch.{OPENVFD_SERVER_STATE_ACTION}", 'on')
        else:
            send_state(self._hass, f"switch.{OPENVFD_SERVER_STATE_ACTION}", 'off')


    async def update_server_state(self,is_enable=1):
        if str(is_enable) == '1':
            await self.update_entity_state(f"switch.{OPENVFD_SERVER_CONTROL}")
            self.write_server('enable')
        else:
            await self.update_entity_state(f"switch.{OPENVFD_SERVER_CONTROL}",'state','off')
            self.write_server('disable')



    def write_server(self,state):
        update_data = {
            "openvfd_server": state
        }
        yaml_data = self._hass.data[DOMAIN]['yaml_config']
        yaml_data.update(update_data)
        yaml_write(YAML_FILE,yaml_data)

    def write(self,time_zone):
        update_data = {
            "time_zone_name": time_zone,
        }
        yaml_data = self._hass.data[DOMAIN]['yaml_config']
        yaml_data.update(update_data)
        yaml_write(YAML_FILE,yaml_data)

    async def update_default_utc_yaml(self, time_zone: str) -> None:
        self.write(time_zone)

    async def update_default_utc(self,time_zone: str) -> None:
        _utc_val = await self.async_get_entity_attr(OPENVFD_TIME_ZONE_UTC_NAME)

        if time_zone != _utc_val:
            await self.update_entity_state(OPENVFD_TIME_ZONE_UTC_NAME,'state',time_zone)
            self.write(time_zone)
