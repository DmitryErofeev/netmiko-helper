import pynetbox
import netmiko
import json


with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

dev_conf = conf.get('device')
if not dev_conf:
    raise ValueError

nb_conf = conf.get('netbox')
if not nb_conf:
    raise ValueError


nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)


commands = {
    'eltex':
        ['show ip ssh']
}

configs = {
    'eltex':
        ['ip ssh server']
}

