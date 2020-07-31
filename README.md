Модуль для работы с коммутаторами Eltex и D-Link.
Использует измененный netmiko, в котором дописан драйвер телнета и реализован save_config для Элтекса.

- `check device`: берет список коммутаторов из NetBox и записывает в формате JSON в файл:
[
    {
        "hardware": "C1",
        "id": 9113,
        "ip": "8.8.8.8",
        "lldp_forward_status": false,
        "lldp_status": true,
        "mac": "D8-FE-E3-EB-D7-E0",
        "model": "DES-3200-28",
        "netmiko_driver": "dlink_ds_telnet",
        "serial": "R3DZ1DA002818",
        "snmp_status": false,
        "software": "4.51.B007",
        "ssh_status": true,
        "vendor": "d-link"
    },
    {
        "hardware": "01.04",
        "id": 9112,
        "ip": "1.1.1.1",
        "lldp_forward_status": null,
        "lldp_status": true,
        "mac": "e8:28:c1:5f:14:80",
        "model": "MES1124M AC rev.B 28-port 100M/1G Managed Switch",
        "netmiko_driver": "eltex",
        "snmp_status": true,
        "software": "1.1.48.7[fc3f05fc]",
        "ssh_status": true,
        "vendor": "eltex"
    }
]

- `enable lldp`: включает LLDP на транковых портах в коммутаторах из этого файла.
