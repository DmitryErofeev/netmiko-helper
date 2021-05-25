import pynetbox
import netmiko
import json
from loguru import logger
import logging
from icecream import ic
import datetime


try:
    with open('config.json') as config_file:
        conf = json.load(config_file)

except(KeyError):
    logger.error('Нет файла с переменными!')

logging.basicConfig(filename='test.log', level=logging.DEBUG)


nb_url = conf['netbox']['url']
nb_token = conf['netbox']['token']

device_username = conf['device']['username']
device_password = conf['device']['password']

nb = pynetbox.api(nb_url, nb_token)

eltex_command = 'copy running-config tftp://10.100.3.104/{device_name}_{now}.txt'
finish_result = []


def get_devices_from_netbox(params):

    devices = nb.dcim.devices.filter(**params)
    return devices


def do_connect(device):

    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    device_result = {
        'ip': device.primary_ip.address.split('/')[0],
    }

    netmiko_params = {
        'device_type': device.device_type.custom_fields['netmiko_driver'],
        'username': device_username,
        'password': device_password,
        'ip': device.primary_ip.address.split('/')[0],
        # 'timeout': 100,
        # 'global_delay_factor': 3,
    }
    try:
        with netmiko.ConnectHandler(**netmiko_params) as ssh:

            logger.info(
                f'Применяю команду {eltex_command.format(device_name=device.name, now=now)} на {device.primary_ip.address}'
            )
            out = ssh.send_command_timing(
                eltex_command.format(device_name=device.name, now=now))

            logger.info(f'Результат: {out}')
            device_result['result'] = 'Ok'

    except(
        TimeoutError,
        OSError,
        netmiko.ssh_exception.NetmikoTimeoutException,
        ConnectionResetError,
        netmiko.ssh_exception.NetmikoAuthenticationException,
    ) as ex:
        _error = {}
        _error['error'] = f'{ex.args} - {ex.__class__.__name__}'
        device_result['result'] = _error

    return device_result


def main(params):
    logger.info('Получаем список устройств из Нетбокса: ')
    devices = get_devices_from_netbox(params)
    logger.info(f'В списке: {len(devices)} коммутаторов')

    for device in devices:
        logger.info(f'Соединяемся с коммутатором {device.primary_ip.address}')
        result = do_connect(device)
        finish_result.append(result)


if __name__ == '__main__':

    params = {
        'region': 'ld',
        # 'role': 'access-switch',
        'status': 'active',
        'model': 'mes1124m',
        # 'name': '',
    }
    main(params)

    with open('output/result_save_config.txt', 'w') as errors_file:
        json.dump(finish_result, errors_file, sort_keys=True)

    ic('Готово')
    ic(f'Результат: {finish_result}')
