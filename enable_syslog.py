import json
from loguru import logger
import pynetbox
import netmiko

with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError

nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)


# commands = {
    # 'eltex':
    #     ['sh ip ssh'],
#     'd-link':
#         [
#         'enable ssh',
#         ],
# }

configs = {
    'eltex':
        [
            'logging buffered',
            'logging buffered 400',
            'logging host 10.100.3.130 port 1514 severity debugging',

        ]
}

fail_to_connect = []
error = []
finish_result = []


# list_ip_for_enable_syslog = nb.dcim.devices.filter(region='kb', role='access-switch')




# for device in list_ip_for_enable_syslog:


_params = {
    # 'device_type': device['netmiko_driver'],
    'device_type': 'eltex_telnet',
    'username': dev_conf['username'],
    'password': dev_conf['password'],
    'ip': '10.100.0.207'
    # 'ip': device['ip'],
}

_device_result = {}
try:

    with netmiko.ConnectHandler(**_params) as ssh:
        # посылаем конфиг Элтекса, если он есть
        if configs.get('eltex'):

            out = ssh.send_config_set(configs.get('eltex'), cmd_verify=False)
            # logger.info(f'Выполняю configs Элтекса: {out}')


        # if commands.get(device['vendor']):
        #     _vendor = device['vendor']

            # _device_result['vendor'] = _vendor


            # for command in commands.get(device['vendor']):
            #     _ip = device['ip']
            #     _device_result['ip'] = _ip

            #     if 'config admin local_enable' in command:
            #         out = ssh.send_command_timing(command, use_textfsm=True)
            #         while isinstance(out, str) and out.startswith(':', -1):
            #             out = ssh.send_command_timing("\n")
            #             out = netmiko.utilities.get_structured_data(out, platform=_params['device_type'], command=command)
            #     else:
            #         out = ssh.send_command(command, use_textfsm=True)
            #     logger.info(f'Применяю команду: {command} на {_vendor} IP: {_ip} {out}')

            #     if not isinstance(out, list):
            #         error.append({_ip, out})

                    # continue
                    # raise ValueError("Error in result", out, device, command)


        ssh.save_config()


except (TimeoutError, ConnectionResetError, netmiko.ssh_exception.NetMikoTimeoutException) as ex:
    _device_result['ip'] = _params['ip']
    # _device_result['vendor'] = device['vendor']
    _device_result['error'] = f'{ex.args} - {ex.__class__.__name__}'

    # fail_to_connect.append({device['ip']: _device_result['error']})

    # logger.info(f'Невозможно соединиться{fail_to_connect[-1]}')

# finish_result.append(_device_result)

logger.info(f'{_device_result}')
# logger.info(f'{error}')

# with open('output/enable_ssh.json', 'w', encoding='utf-8-sig') as json_file:
#     json.dump(finish_result, json_file, indent=4, sort_keys=True)