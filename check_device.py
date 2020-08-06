import netmiko
from pprint import pprint
from netmiko.utilities import get_structured_data
import json
import logging
import pynetbox


with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)


nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError
dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError


logging.basicConfig(filename='test.log', level=logging.DEBUG)
logger = logging.getLogger("netmiko")

nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)


report = []

commands = {
    'eltex':
    [
        'sh system',
        'sh lldp configuration',
        'sh ver',
        'sh ip ssh',
        'sh snmp'
    ],

    'd-link':
    [
        'sh sw',
        'sh lldp'
    ]

}

_list = nb.dcim.devices.filter(region='tc', role='access-switch')

fail_to_connect = []


def make_true(func):
    if func is not None:
        if func in '':
            func = None
        elif func.lower() in 'disabled':
            func = False
        elif func.lower() in 'enabled':
            func = True
    return func


for device in _list:
    _type = device.device_type.display_name
    _driver = device.device_type.custom_fields['netmiko_driver']
    _ip = device.primary_ip


    if not _driver:
        print("Device:", _type, _driver)
        continue
    print("Device:", _type, _driver)


    _params = {
        'device_type': _driver,
        'username': dev_conf['username'],
        'password': dev_conf['password'],
        'secret': 'admin',
        'ip': _ip.address.split('/')[0]
    }


    try:
        with netmiko.ConnectHandler(**_params) as ssh:

            _device = {
                'ip': _ip.address.split('/')[0],
                'id': device.id,
                'vendor': device.device_type.manufacturer.slug,
                'netmiko_driver' : _driver
            }


            for command in commands.get(_device['vendor']):
                out = ssh.send_command(command)
                result = get_structured_data(
                    out, command=command, platform=_driver)

                print(device.primary_ip.address, command, result)
                if isinstance(result, list):
                    _device.update(result[0])
                else:
                    raise ValueError("Error in result", result, _device, command)

            _device['lldp_status'] = make_true(_device.get('lldp_status'))

            _device['lldp_forward_status'] = make_true(_device.get('lldp_forward_status'))

            _device['ssh_status'] = make_true(_device.get('ssh_status'))

            _device['snmp_status'] = make_true(_device.get('snmp_status'))

            report.append(_device)
    except netmiko.ssh_exception.NetMikoTimeoutException as ex :
        print(_ip, ex)
        fail_to_connect.append({_ip: ex.args})

pprint(report)
print('Невозможно соединиться:', fail_to_connect)


with open('output/result.json', 'w', encoding='utf-8-sig') as json_file:
    json.dump(report, json_file, indent=4, sort_keys=True)
