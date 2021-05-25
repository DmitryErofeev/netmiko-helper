import json
import netmiko
import pynetbox
from loguru import logger
from retry import retry
import requests
from icecream import ic

# Запрашивает версию прошивки у Длинков через API
with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError


fail_to_connect = []
finish_result = []


def get_devices_by_model(model):
    nb = pynetbox.api(url=nb_conf['url'],
                      token=nb_conf['token'], threading=True)
    devices_list = nb.dcim.devices.filter(model=model, status='active')
    return devices_list


@retry(exceptions=Exception, tries=5, delay=2, backoff=2, logger=logger)
def api_get_data(ip):
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/get_firmware'
    responce = requests.get(url)
    firmware = responce.json()
    return firmware


def main(model):
    logger.info(f'main(){model}')

    # получаем устройства из региона
    for device in get_devices_by_model(model):
        result = {}
        ip = device.primary_ip.address.split('/')[0]
        responce = api_get_data(ip)
        if data := responce['response'].get('data'):
            fw_info = data.get('firmware_info')['0']
            result['ip'] = ip
            result['model'] = responce['response']['model']
            result['firmware_info'] = fw_info
            result['uptime'] = responce['response']['sys_uptime']
            result['uptime'] = int(int(result['uptime']) / 100 / 3600)

            finish_result.append(result)

    logger.info(f'Устройства {model} обработаны')


if __name__ == '__main__':
    nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)
    # region = 'oz'
    models = [
        'des-3200-18',
        # 'des-1210-10me',
        # 'des-1210-28me',
    ]

    for model in models:
        main(model)

    with open('output/get_firmware.json', 'w', encoding='utf-8-sig') as json_file:
        json.dump(finish_result, json_file, indent=4, sort_keys=True)

    logger.info('Готово')
