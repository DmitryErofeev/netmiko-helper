
# from sys import platform
import netmiko
import json
from loguru import logger


with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError


commands = {
    # 'eltex':
        # ['sh ip ssh'],
    'd-link':
        [
        'enable ssh',
        'sh sw',
        'config authen_login default method local',
        'config authen_login method_list_name rad_ext method radius local',
        'config authen_enable default method local',
        'config authen_enable method_list_name rad_ext_ena method radius',
        'config authen application all login method_list_name rad_ext',
        'config authen application all enable method_list_name rad_ext_ena',
        'config authen application console login default',
        'config authen application console enable default',
        'config authen parameter response_timeout 30',
        'config authen parameter attempt 3',
        'enable authen_policy',
        'config admin local_enable',
        ],
}

configs = {
    # 'eltex':
        # [
        #     'ip ssh server',
        #     'aaa authentication enable default enable',
        #     'aaa authentication enable rad_ext_ena radius',
        #     'ip http authentication aaa login-authentication radius local',
        #     'aaa authentication login default local',
        #     'aaa authentication login rad_ext radius local',

        #     'line telnet',
        #     ' login authentication rad_ext',
        #     ' enable authentication rad_ext_ena',

        #     'line ssh',
        #     ' login authentication rad_ext',
        #     ' enable authentication rad_ext_ena',
            # 'exit',
        # ]
}

fail_to_connect = []
error = []


# def filter_by_key(_data_file):
#     return [d for d in _data_file if d['ssh_status'] == False]
    # return [d for d in _data_file if d['ssh_status'] == True] # for debug


def make_list_ip_for_enable_ssh(_data):
    _list = [ {'vendor': x['vendor'], 'ip': x['ip']} for x in _data if x]
    return _list


finish_result = []


with open('output/errors_syslog.json', 'r', encoding='utf-8-sig') as data_file:
    _data = json.load(data_file)
    # _modified_data = filter_by_key(_data)
    _modified_data = make_list_ip_for_enable_ssh(_data)
    logger.info(f'Список на включение SSH: {make_list_ip_for_enable_ssh(_modified_data)}')
    logger.info(f'Итого: {len(make_list_ip_for_enable_ssh(_modified_data))} штук')


    for device in _modified_data:
        _device_result = {}
        _params = {
            'device_type': 'dlink_ds_telnet',
            'username': dev_conf['username'],
            'password': dev_conf['password'],
            'ip': device['ip'],
        }


        try:
            with netmiko.ConnectHandler(**_params) as ssh:
                # посылаем конфиг Элтекса, если он есть
                # if configs.get(device['vendor']):

                #     out = ssh.send_config_set(configs.get(device['vendor']), cmd_verify=False)
                #     logger.info(f'Выполняю configs Элтекса: {out}')


                if commands.get(device['vendor']):
                    _vendor = device['vendor']

                    _device_result['vendor'] = _vendor


                    for command in commands.get(device['vendor']):
                        _ip = device['ip']
                        _device_result['ip'] = _ip

                        if 'config admin local_enable' in command:
                            out = ssh.send_command_timing(command, use_textfsm=True)
                            while isinstance(out, str) and out.startswith(':', -1):
                                out = ssh.send_command_timing("\n")
                                out = netmiko.utilities.get_structured_data(out, platform=_params['device_type'], command=command)
                        else:
                            out = ssh.send_command(command, use_textfsm=True)
                        logger.info(f'Применяю команду: {command} на {_vendor} IP: {_ip} {out}')

                        if not isinstance(out, list):
                            error.append({_ip, out})

                            continue
                            # raise ValueError("Error in result", out, device, command)


                        if out[0].get('ssh_enable') and not out[0].get('ssh_enable').lower() in 'success':
                            raise ValueError("Error in result", out, device, command)


                        if out[0].get('ssh_status'):
                            if out[0].get('ssh_status').lower() in 'enabled':
                                _device_result['result']  = 'ok'
                            else:
                                _device_result['result']  = 'error'
                                _device_result['ssh_status'] = out[0].get('ssh_status')

                ssh.save_config()


        except (TimeoutError,  EOFError, ConnectionResetError, netmiko.ssh_exception.NetMikoTimeoutException) as ex:
            _device_result['ip'] = device['ip']
            _device_result['vendor'] = device['vendor']
            _device_result['error'] = f'{ex.args} - {ex.__class__.__name__}'

            fail_to_connect.append({device['ip']: _device_result['error']})

            logger.info(f'Невозможно соединиться{fail_to_connect[-1]}')

        finish_result.append(_device_result)

logger.info(f'{finish_result}')
logger.info(f'{error}')

with open('output/enable_ssh.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(finish_result, json_file, indent=4, sort_keys=True)