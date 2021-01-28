import json
from loguru import logger
import pynetbox
import logging
import asyncio
from commands_for_enable_syslog import do_connect


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

async def apply_device_config(device):
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
    }
    logger.info(f"do_connect() to {_ip}")
# Подключаемся по netmiko к коммутатору:
    _error, _success = await do_connect(_vendor, _ip, _params)
# Записываем результат применения команд:
    fail_to_connect.append(_error)
    finish_result.append(_success)


async def get_list_devices_in_region(region):
# Получаем коммутаторы в регионе в список
    logger.info(f"get_list_devices_in_region({region})")
    nb2 = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)
    list_devices = nb2.dcim.devices.filter(region=region, manufacturer='d-link', status='active')
    return list_devices


async def main(region):
    logger.info(f"main({region})")
    await asyncio.sleep(0)
# Получаем от функции список коммутаторов:
    for device in await get_list_devices_in_region(region):
# Отправляем коммутаторы на обработку командами:
        await apply_device_config(device)

    logger.info(f'Устройства в {region} обработаны')


if __name__ == '__main__':
    logger.info("nb.dcim.regions.filter()")

    nb1 = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

# Получаем регионы в список:
    all_regions = nb1.dcim.regions.filter(parent__n='null', slug__n='test-district')
    # all_regions = nb1.dcim.regions.filter(slug='kb')

    loop = asyncio.get_event_loop()
#Создаем таски по регионам и передаем регион в главную функцию:
    tasks = [loop.create_task(main(region.slug)) for region in all_regions]

    loop.run_until_complete(asyncio.wait(tasks))


with open('output/success_enable_syslog.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(finish_result, json_file, indent=4, sort_keys=True)

with open('output/errors_enable_syslog.json', 'w', encoding='utf-8-sig') as json2_file:
    json.dump(fail_to_connect, json2_file, indent=4, sort_keys=True)

logger.info(f"Completed!{len(finish_result)}")