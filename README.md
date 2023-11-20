# Wgi Openvfd X96max


## 安装

搜索 `Wgi openvfd x96max`安装

## 实体配置


```

BASE_DEVICE_CONFIG = {
    "device": [
        {
            "manufacturer": "冬瓜电子",
            # "configuration_url": "https://www.minforcode.com",
            "sw_version": "0.1.0",
            "hw_version": "0.1.0",
            "model": "wg_x96max_openvfd",
            "id": "vfd-mf-100",
            "name": "Openvfd设备",
            "entities": [
                {
                    "platform": "sensor",
                    "id": OPENVFD_TIME_ZONE_UTC_NAME,
                    "field_type": "zone_name",
                    "name": "时区",
                    "state": "Asia/Shanghai",
                    "allow_config":"off",
                    "icon": "mdi:timeline-clock",
                    "unit_of_measurement": ""
                },

                {
                    "platform": "switch",
                    "id": f"switch.{OPENVFD_SERVER_CONTROL}",
                    "field_type": f"{OPENVFD_SERVER_CONTROL}",
                    "value_type": "",
                    "name": "开机OpenVFD启动",
                    "icon": "mdi:server",
                    "state": "on",
                    "allow_config":"off",
                    "unit_of_measurement": ""
                },
                {
                    "platform": "switch",
                    "id": f"switch.{OPENVFD_SERVER_STATE_ACTION}",
                    "field_type": f"{OPENVFD_SERVER_STATE_ACTION}",
                    "value_type": "",
                    "name": "服务状态切换",
                    "icon": "mdi:server",
                    "state": "on",
                    "allow_config":"off",
                    "unit_of_measurement": ""
                },
                {
                    "platform": "button",
                    "id": f"button.{OPENVFD_SERVER_RESTART}",
                    "field_type": f"{OPENVFD_SERVER_RESTART}",
                    "value_type": "",
                    "name": "服务重启",
                    "icon": "",
                    "state": "on",
                    "allow_config":"off",
                    "unit_of_measurement": ""
                },
            ]
        }
    ]
}
```

