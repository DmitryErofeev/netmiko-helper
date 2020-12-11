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

def apply_device_config(ip):
    logger.info(f"apply_device_config({ip})")
# Собираем информацию по коммутатору для netmiko
    _driver = 'dlink_ds'
    _vendor = 'd-link'
    _ip = ip
    _params = {
        'device_type': _driver,  # имя драйвера для netmiko
        'username': dev_conf['username'],
        'password': dev_conf['password'],
        'ip': _ip,
        # 'secret': dev_conf['secret'],
        # 'global_delay_factor': 4,
    }
    logger.info(f"do_connect() to {_ip}")
# Подключаемся по netmiko к коммутатору:
    _error, _success = do_connect(_vendor, _ip, _params)
# Записываем результат применения команд:
    fail_to_connect.append(_error)
    finish_result.append(_success)


def main(ip):
    logger.info(f"main({ip})")
    # await asyncio.sleep(0)
# Отправляем коммутаторы в функцию на обработку командами:
    apply_device_config(ip)
    logger.info(f'main(), Устройства с {ip} обработаны')


if __name__ == '__main__':
    # logger.info("nb.dcim.regions.filter()")

    nb1 = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

    with open('output/~errors_enable_syslog.json', 'r', encoding='utf-8-sig') as source_data:
        all_unsorted_IP = json.load(source_data)

        # loop = asyncio.get_event_loop()
#Создаем таски по IP и передаем IP в главную функцию:
        # for ip in all_IP:
        all_sorted_IP = [ip for ip in all_unsorted_IP if ip]
        for ip in all_sorted_IP:
            main(ip['ip'])

        # loop.run_until_complete(asyncio.wait(tasks))


with open('output/success_enable_syslog.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(finish_result, json_file, indent=4, sort_keys=True)

with open('output/errors_enable_syslog.json', 'w', encoding='utf-8-sig') as json2_file:
    json.dump(fail_to_connect, json2_file, indent=4, sort_keys=True)

logger.info(f"Completed!{len(finish_result)}")






