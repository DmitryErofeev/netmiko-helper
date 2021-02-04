from os import name, pardir
import requests
import pynetbox
import json
from loguru import logger
from retry import retry
import netmiko
from icecream import ic
from make_ports_for_lldp import PORT_MAP


with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

nb_conf =  conf.get('netbox')
nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

errors = []
# result = {}

def get_devices(args):
    list_devices = nb.dcim.devices.filter(**args)
    return  list_devices


@retry(exceptions=ConnectionError, tries=5, delay=3, backoff=2, logger=logger)
def walk_lldp(ip):
    logger.info(f'Запрашиваем API по {ip}')
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/walk_lldp'
    r = requests.get(url).json()
    lldp_rem_table = r['response']['data'].get('ldpRemTable')
    if lldp_rem_table and list(lldp_rem_table.keys())[0].startswith('.'): # отлавливаем, если ответ возвращается с точкой впереди
        errors.append({ip:'Item value start with DOT!!!'})
        # raise ValueError(lldp_rem_table, "Item keys start with DOT!!!")
    return lldp_rem_table


def make_remote_table(lldp_rem_table):
    key_map = {
        '1.4': 'CidType',
        '1.5': 'Cid',
        '1.6': 'PidType',
        '1.7': 'Pid',
    }
    table = {}

    for key, val in lldp_rem_table.items():
        res = key.rsplit('.', maxsplit=3)
        # _
        if not table.get(res[2]): # надо проверять вендора
            table |= {res[2]: {}}
        if key_map.get(res[0]):
            table[res[2]] |= {key_map[res[0]]: val}

    return table


def get_port_id_from_netbox(device, tables):
    tables_with_id = tables
    for key in tables:

        if device.device_type.manufacturer.slug == 'eltex':
            # key = list(table.keys())
            port_name = PORT_MAP.get(key)
            port = nb.dcim.interfaces.filter(device_id=device.id, name=port_name)
            tables_with_id[key] |= {'local_port_id': port[0].id}
        else:
            # key = list(table.keys())
            # port_name = key
            port = nb.dcim.interfaces.filter(device_id=device.id, name=key)
            try:
                tables_with_id[key] |= {'local_port_id':port[0].id}
            except (IndexError):
                logger.error(f'Нет порта в нетбоксе')
                errors.append(device.primary_ip.address.split('/')[0])

    return tables_with_id


def main(region):
    logger.info(f'Получаем список устройств в {region} из Нетбокса')
    devices_in_region = get_devices(region)
    # _result = {}
    for device in devices_in_region:

        _ip = device.primary_ip.address.split('/')[0]

        lldp_rem_table = walk_lldp(_ip) # Возвращает таблицу соседства из API: 1.5.634570.26.1	"84c9b29913c0"

        if lldp_rem_table:
            table = make_remote_table(lldp_rem_table) # Возвращает таблицу соседства: lldpRT = {26:{'CidType':'4','Cid':'df4e','PidType':'7','Pid':'26'}}

            # _port_name = table[1]
            local_port_id = get_port_id_from_netbox(device, table) # Возвращает id транкового порта

            ic(local_port_id)

        else:
            logger.error(f'Нет соседства у {_ip}')
            errors.append(_ip)
    # result.update(_result)


if __name__ == '__main__':
    region = 'kb'

    params = {
        'region': region,
        # 'tag': 'test-lldp',
        'status': 'active',
        'role':'access-switch',
    }

    main(params)


    # with open(f'output/success_lldp_{region}.json', 'w', encoding='utf-8-sig') as json_file:
    #     json.dump(result, json_file, indent=4, sort_keys=True)

    with open(f'output/errors_lldp_{region}.json', 'w', encoding='utf-8-sig') as json_file2:
        json.dump(errors, json_file2, indent=4, sort_keys=True)

    ic('Готово')
    ic(f'Ошибки: {errors}')


