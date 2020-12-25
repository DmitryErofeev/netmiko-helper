import json
import netmiko
import pynetbox
from loguru import logger
from make_ports_for_lldp import make_ports
from commands_for_enable_lldp import do_connect


# TODO: Check file exists
with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError


fail_to_connect = []
finish_result = []


def apply_commands(device):
    logger.info(f'apply_commands()на устройстве{device}')
    #Собираем информацию по устройству для netmiko
    _driver = device.device_type.custom_fields['netmiko_driver']
    _ip = device.primary_ip.address.split('/')[0] # отрезаем префикс от ip
    _vendor = device.device_type.manufacturer.slug
    _params = {
        'device_type': _driver,  # имя драйвера для netmiko
        'username': dev_conf['username'],
        'password': dev_conf['password'],
        'ip': _ip,
        'timeout': 100,
    }
    logger.info(f'Соединяюсь с {_ip}')
    _ports = make_ports(_ip)
    _errors, _success = do_connect(_vendor, _ip, _params, _ports)

    fail_to_connect.append(_errors)
    finish_result.append(_success)


def get_list_devices_in_region(region):
    logger.info(f'get_list_devices_in_region(){region}')
    list_devices = nb.dcim.devices.filter(role='access-switch', region=region, status='active', manufacturer='d-link')
    return list_devices


def main(region):
    logger.info(f'main(){region}')
    for device in get_list_devices_in_region(region): # получаем устройства из региона
        apply_commands(device) # применяем команды на устройство
    logger.info(f'Устройства в {region}обработаны')


if __name__ == '__main__':
    nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)
    main('kb')


with open('output/success_enable_lldp.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(finish_result, json_file, indent=4, sort_keys=True)

with open('output/errors_enable_lldp.json', 'w', encoding='utf-8-sig') as json_file2:
    json.dump(fail_to_connect, json_file2, indent=4, sort_keys=True)

logger.info(f'LLDP включен на {len(finish_result)} коммутаторах' )
