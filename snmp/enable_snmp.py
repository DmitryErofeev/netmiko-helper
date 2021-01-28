import json
from loguru import logger
import pynetbox
import logging
from commands_for_enable_snmp import do_connect


with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)
dev_conf = conf.get('device')

if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')

if not nb_conf:
    raise ValueError

logging.basicConfig(filename='test.log', level=logging.DEBUG)

fail_to_connect = []
finish_result = []

def apply_device_config(device):
    logger.info(f"apply_device_config({device})")
# Собираем информацию по коммутатору для netmiko
    _driver = device.device_type.custom_fields['netmiko_driver']
    _vendor = device.device_type.manufacturer.slug
    _ip = device.primary_ip.address.split('/')[0]  # отрезаем префикс от ip
    _params = {
        'device_type': _driver,  # имя драйвера для netmiko
        'username': dev_conf['username'],
        'password': dev_conf['password'],
        'ip': _ip,
        'timeout': 100,
    }
    logger.info(f"do_connect() to {_ip}")
# Подключаемся по netmiko к коммутатору:
    _error, _success = do_connect(_vendor, _ip, _params)
# Записываем результат применения команд:
    fail_to_connect.append(_error)
    finish_result.append(_success)


def get_list_devices_in_region(region):
# Получаем коммутаторы в регионе в список
    logger.info(f"get_list_devices_in_region({region})")
    nb2 = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)
    list_devices = nb2.dcim.devices.filter(region=region, role='distribution-switch', status='active')
    return list_devices


def main(region):
    logger.info(f"main({region})")

# Получаем от функции список коммутаторов:
    for device in get_list_devices_in_region(region):
# Отправляем коммутаторы на обработку командами:
        apply_device_config(device)

    logger.info(f'Устройства в {region} обработаны')


if __name__ == '__main__':
    # logger.info("main()")

    # nb1 = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

# Получаем регионы в список:
    # all_regions = nb1.dcim.regions.filter(parent__n='null', slug__n='test-district')
    # all_regions = nb1.dcim.regions.filter(slug='kb')

#Вызываем главную функцию и передаем регион :
    # [(main(region.slug)) for region in all_regions]

    main('oz')

with open('output/success_enable_snmp_oz.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(finish_result, json_file, indent=4, sort_keys=True)

with open('output/errors_enable_snmp_oz.json', 'w', encoding='utf-8-sig') as json2_file:
    json.dump(fail_to_connect, json2_file, indent=4, sort_keys=True)

logger.info(f"Completed!{len(finish_result)}")