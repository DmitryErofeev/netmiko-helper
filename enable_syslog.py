import json
from loguru import logger
import pynetbox
import netmiko
import logging
with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError

nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

logging.basicConfig(filename='test.log', level=logging.DEBUG)
# logger = logging.getLogger("netmiko")

commands = {
    'eltex':
        ['show syslog-servers'],
    'd-link':
        [
        'create syslog host 1 ipaddress 10.100.3.130 udp_port 514 severity warning facility local7 state enable',
        'config syslog host 1 ipaddress 10.100.3.130 udp_port 514 severity warning',
        'enable syslog',
        'show syslog host',
        'enable clipaging',
        ],
}

configs = {
    'eltex':
        [
            'logging buffered',
            'logging buffered 400',
            'logging host 10.100.3.130 port 514 severity debugging',
        ]
}

fail_to_connect = []
finish_result = []

# получаем из нетбокса список коммутаторов для включения syslog-а
# list_for_enable_syslog = nb.dcim.devices.filter(tag='test-syslog', role='access-switch')
list_for_enable_syslog = nb.dcim.devices.filter(region='parkovskaya-3', role='access-switch', status='active')


#запускаем цикл по коммутаторам
for device in list_for_enable_syslog:
    _driver = device.device_type.custom_fields['netmiko_driver']
    _vendor = device.device_type.manufacturer.slug
    _ip = device.primary_ip.address.split('/')[0] # отрезаем префикс от ip
    _params = {
        'device_type': _driver, # имя драйвера для netmiko
        'username': dev_conf['username'],
        'password': dev_conf['password'],
        'ip': _ip,
    }

    _device_result = {}


    try:
        with netmiko.ConnectHandler(**_params) as ssh:

            # посылаем конфиг Элтекса, если он есть
            if cfg := configs.get(_vendor):
                out = ssh.send_config_set(cfg, cmd_verify=False)
                logger.info(f'Выполняю configs Элтекса:{_ip} {out}')
                _device_result['ip'] = _ip
                _device_result['vendor'] = _vendor


            if commands.get(_vendor):
                _device_result['vendor'] = _vendor


                for command in commands.get(_vendor):
                    _device_result['ip'] = _ip
                    out = ssh.send_command(command, use_textfsm=True)
                    logger.info(f'Применяю команду: {command} на {_vendor} IP: {_ip} {out}')

                    if 'show syslog-servers' in command:
                        _device_result['status'] = out[0]['status']

                    if 'enable syslog' in command:
                        _device_result['enable_syslog'] = out[0]['enable']

                    if 'show syslog host' in command:
                        _device_result['ip_syslog_sever'] = out[0]['ip']


            ssh.save_config()

        finish_result.append(_device_result)

    except (TimeoutError, ConnectionResetError, netmiko.ssh_exception.NetMikoTimeoutException) as ex:
        _device_result['ip'] = _ip
        _device_result['vendor'] = _vendor
        _device_result['error'] = f'{ex.args} - {ex.__class__.__name__}'

        fail_to_connect.append(_device_result)
        logger.info(f'Невозможно соединиться{fail_to_connect[-1]}')


    logger.info(f'{_device_result}')
logger.info(f'{finish_result}')

with open('output/success_enable_syslog.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump (finish_result, json_file, indent=4, sort_keys=True)

with open('output/errors_enable_syslog.json', 'w', encoding='utf-8-sig') as json2_file:
    json.dump(fail_to_connect, json2_file, indent=4, sort_keys=True)