import json
import netmiko
import pynetbox
import requests
from retry import retry
from loguru import logger
from commands_for_disable_gvrp_Icheking import do_connect

# Отключает gvrp Ingress cheking на длинках

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
    # _device_result = {}
    logger.info(f'apply_commands() на устройстве{device}')
    #Собираем информацию по устройству для netmiko
    _driver = device.device_type.custom_fields['netmiko_driver']
    _ip = device.primary_ip.address.split('/')[0] # отрезаем префикс от ip
    _vendor = device.device_type.manufacturer.slug
    _params = {
        'device_type': _driver,  # имя драйвера для netmiko
        'username': dev_conf['username'],
        'password': dev_conf['password'],
        'ip': _ip,
        # 'timeout': 100,
        # 'global_delay_factor': 3,
    }
    logger.info(f'Соединяюсь с {_ip}')

    try:

        _success = do_connect(_vendor, _ip, _params) # тут надо _ports

        finish_result.append(_success)

    except(TimeoutError, OSError, netmiko.ssh_exception.NetmikoTimeoutException, paramiko.ssh_exception.SSHException,
    ConnectionResetError, netmiko.ssh_exception.NetmikoAuthenticationException) as ex:
        _error = {}
        _error['ip'] = _ip
        _error['vendor'] = _vendor
        _error['error'] = f'{ex.args} - {ex.__class__.__name__}'
        fail_to_connect.append(_error)


@retry(exceptions=ConnectionError, tries=5, delay=3, backoff=2, logger=logger)
def get_probeConfig(ip):
    logger.info(f'Запрашиваем API по {ip}')
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/get_probeConfig'
    r = requests.get(url)
    data = r.json()
    hw_rev = data['response']['data'].get('HardwareRev')
    if hw_rev and list(hw_rev.keys())[0].startswith('.'): # отлавливаем, если ответ возвращается с точкой впереди
        fail_to_connect.append({ip:'Item value start with DOT!!!'})
        # raise ValueError(lldp_rem_table, "Item keys start with DOT!!!")
    return hw_rev


def get_list_devices_in_region(model, region):
    logger.info(f'get_list_devices_in_region(){region}')
    list_devices = nb.dcim.devices.filter(role='access-switch', region=region, status='active', model=model)
    return list_devices


def main(model, region):
    logger.info(f'main(){region}')
    for device in get_list_devices_in_region(model, region): # получаем устройства из региона
        ip = device.primary_ip.address.split('/')[0]

        try:
            hw_rev = get_probeConfig(ip).get('0') #Сортируем устройство по версии прошивки
            logger.info(f'Модель: {model}, Ревизия: {hw_rev}')
        except:
            fail_to_connect.append({ip:'АПИ не ответило по этому свитчу'})

        if device.device_type.slug == 'des-3200-28' or device.device_type.slug == 'des-3200-10':
            if hw_rev == 'B1' or hw_rev == 'A1':
                logger.info(f'DES-3200, ревизия: {hw_rev}, применяю команду')
                try:
                    apply_commands(device) # применяем команды на устройство
                except:
                    fail_to_connect.append({ip:'Команда не применилась'})

            else:
                logger.info(f'ревизия норм: {hw_rev}')

        else:
            try:
                apply_commands(device)
                logger.info(f'DES-3028, применяю команду')
            except:
                fail_to_connect.append({ip:'Команда не применилась'})


    logger.info(f'Устройства в {region} обработаны')


if __name__ == '__main__':
    models = ['des-3200-28', 'des-3028', 'des-3200-10']
    nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)
    region = 'oz'
    for model in models:
        main(model, region)
# 3200-28, 3028, 3200-10

    with open(f'output/success_disable_gvrp_{region}.json', 'w', encoding='utf-8-sig') as json_file:
        json.dump(finish_result, json_file, indent=4, sort_keys=True)

    with open(f'output/errors_disable_gvrp_{region}.json', 'w', encoding='utf-8-sig') as json_file2:
        json.dump(fail_to_connect, json_file2, indent=4, sort_keys=True)

    logger.info(f'GVRP выключен на {len(finish_result)} коммутаторах' )
