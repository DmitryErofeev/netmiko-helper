import json
import netmiko
import pynetbox
# from .make_ports_for_lldp import make_ports
# from .make_ports_for_lldp import make_ports_eltex
from .commands_for_enable_lldp import do_connect



# from lldp import do_connect, do_connect_3010, VlanListNotFound

# from .commands_for_enable_lldp_3010 import do_connect_3010
import paramiko
# from .make_ports_for_lldp import VlanListNotFound
from netmiko.ssh_exception import NetmikoTimeoutException


# TODO: Check file exists
with open("../config.json") as json_conf_file:
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

    # if _vendor == 'dlink':
    #     _ports = make_ports(_ip)
    # else:
    #     _ports = make_ports_eltex(_ip)

    try:
        if device.device_type.slug == 'des-3010g':
            _success = do_connect_3010(_vendor, _ip, _params, _ports)
        else:
            _success = do_connect(_vendor, _ip, _params, _ports)

        finish_result.append(_success)

    except(TimeoutError,NetmikoTimeoutException, VlanListNotFound, OSError, netmiko.ssh_exception.NetmikoTimeoutException, paramiko.ssh_exception.SSHException,
    ConnectionResetError, netmiko.ssh_exception.NetmikoAuthenticationException) as ex:
        _error = {}
        _error['ip'] = _ip
        _error['vendor'] = _vendor
        _error['error'] = f'{ex.args} - {ex.__class__.__name__}'
        fail_to_connect.append(_error)

def get_list_devices_in_region(region):
    logger.info(f'get_list_devices_in_region(){region}')
    list_devices = nb.dcim.devices.filter(role='access-switch', region=region, status='active', model='des-1210-28me')
    return list_devices


def main(region):
    logger.info(f'main(){region}')
    for device in get_list_devices_in_region(region): # получаем устройства из региона
        apply_commands(device) # применяем команды на устройство
    logger.info(f'Устройства в {region} обработаны')


if __name__ == '__main__':
    nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)
    region = 'dm'
    main(region)


    with open(f'output/success_enable_lldp_{region}.json', 'w', encoding='utf-8-sig') as json_file:
        json.dump(finish_result, json_file, indent=4, sort_keys=True)

    with open(f'output/errors_enable_lldp_{region}.json', 'w', encoding='utf-8-sig') as json_file2:
        json.dump(fail_to_connect, json_file2, indent=4, sort_keys=True)

    logger.info(f'LLDP включен на {len(finish_result)} коммутаторах' )
