import netmiko
import pynetbox
from netmiko.utilities import get_structured_data
import json
# import logging
from loguru import logger

# TODO: Check file exists
with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError

nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

# logging.basicConfig(filename='test.log', level=logging.DEBUG)
# logger = logging.getLogger("netmiko")

# report = []

commands = {
    'eltex':
    [
        'sh lldp configuration'
    ],

    'd-link':
    [
        'enable lldp',
        'config lldp ports {range} admin_status rx_only',
        'sh lldp',
    ]
}

configs = {
    'eltex':
    [
        'lldp run',
        'int ra {range}',
        'no lldp transmit',
    ]
}
fail_to_connect = []


def filter_by_key(_data_file, param):
    return [d for d in _data_file if d[param[0]] == param[1]]


def make_ports(device_id):
    _list_ports = nb.dcim.interfaces.filter(device_id=device_id, type='100base-tx')
    _ports_for_command = '-'.join([_list_ports[0].name, _list_ports[-1].name.split('/')[-1]])
    return _ports_for_command


with open('output/result.json', 'r', encoding='utf-8-sig') as data_file:
    _data_file = json.load(data_file)

    _modified_data_file = filter_by_key(_data_file, ('lldp_forward_status', True))
    if len(_modified_data_file) > 0:
        raise NotImplementedError

    # _modified_data_file = filter_by_key(_data_file, ('lldp_status', False))
    _modified_data_file = filter_by_key(_data_file, ('lldp_status', True))  # for debug

    for device in _modified_data_file:

        _range = make_ports(device['id'])
        _type = device['model']
        _driver = device['netmiko_driver']
        _vendor = device['vendor']
        _ip = device['ip']



        if not _driver:
            logger.info(f"Нет драйвера:{_type}, {_driver}")
            continue
        logger.debug(f"Есть драйвер: {_type}, {_driver}")

        _params = {
            'device_type': _driver,
            'username': dev_conf['username'],
            'password': dev_conf['password'],
            'secret': 'admin',
            'ip': _ip
        }

        try:
            with netmiko.ConnectHandler(**_params) as ssh:

                if configs.get(_vendor):
                    _conf = [c.format(range=_range) for c in configs.get(_vendor)]
                    out = ssh.send_config_set(_conf)
                    logger.info(f'Проверяю выполнение конфига Элтекса: {out}')

                for command in commands[_vendor]:

                    out = ssh.send_command(command.format(range=_range))
                    if command.startswith('sh'):
                        result = get_structured_data(
                            out, command=command, platform=_driver)
                        logger.info(f'Проверяю выполнение команд "show": {result}')

                        if not isinstance(result, list):
                            raise ValueError("Error in result", result, _params['ip'], command)

                    else:
                        logger.info(f'Посылаю команду: {out}')


                    ssh.save_config()
                # report.append(_device)
        except Exception as ex :
            # print(_ip, ex)
            fail_to_connect.append({_ip: ex.args})

# print('', report)
logger.info(f'Невозможно соединиться: {fail_to_connect}')
