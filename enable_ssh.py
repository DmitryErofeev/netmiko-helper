# from check_device import json_file
import netmiko
import json
from loguru import logger
# from netmiko.utilities import get_structured_data


with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError


commands = {
    'eltex':
        ['sh ip ssh'],
    'd-link':
        [
        'enable ssh',
        'sh sw'
        ],
}

configs = {
    'eltex':
        [
            # 'pi ssh server',
        ]
}

fail_to_connect = []


def filter_by_key(_data_file):
    return [d for d in _data_file if d['ssh_status'] == False]
    # return [d for d in _data_file if d['ssh_status'] == True] # for debug


def make_list_ip_for_enable_ssh(_data):
    _list = [ {x['model']: x['ip']} for x in _data ]
    return _list


finish_result = []


with open('output/result.json', 'r', encoding='utf-8-sig') as data_file:
    _data = json.load(data_file)
    _modified_data = filter_by_key(_data)
    logger.info(f'Список на включение SSH: {make_list_ip_for_enable_ssh(_modified_data)}')



    for device in _modified_data:
        _device_result = {}
        _params = {
            'device_type': device['netmiko_driver'],
            'username': dev_conf['username'],
            'password': dev_conf['password'],
            'ip': device['ip'],
        }
        _error = []
        try:
            with netmiko.ConnectHandler(**_params) as ssh:
                #посылаем конфиг Элтекса, если он есть
                if configs.get(device['vendor']):

                    out = ssh.send_config_set(configs.get(device['vendor']))
                    logger.info(f'Выполняю configs Элтекса: {out}')


                if commands.get(device['vendor']):
                    _vendor = device['vendor']

                    _device_result['vendor'] = _vendor

                    for command in commands.get(device['vendor']):
                        _ip = device['ip']
                        _device_result['ip'] = _ip

                        out = ssh.send_command(command, use_textfsm=True)
                        logger.info(f'Применяю команду: {command} на {_vendor} IP: {_ip} {out}')

                        if not isinstance(out, list):
                            raise ValueError("Error in result", out, device, command)



                        if out[0].get('ssh_enable') and not out[0].get('ssh_enable').lower() in 'success':
                            raise ValueError("Error in result", out, device, command)

                        if out[0].get('ssh_status'):
                            if out[0].get('ssh_status').lower() in 'enabled':
                                _device_result['result']  = 'ok'
                            else:
                                _device_result['result']  = 'error'
                                _device_result['error'] = out

                ssh.save_config()


        except netmiko.ssh_exception.NetMikoTimeoutException as ex :
            fail_to_connect.append({device['ip']: ex.args})
            logger.info(f'Невозможно соединиться{fail_to_connect}')

        finish_result.append(_device_result)

logger.info(f'{finish_result}')
with open('output/enable_ssh.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(finish_result, json_file, indent=4, sort_keys=True)