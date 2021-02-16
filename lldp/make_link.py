from os import name, pardir
from functools import lru_cache
import requests
import pynetbox
import json
from loguru import logger
from retry import retry
import netmiko
from icecream import ic
from make_ports_for_lldp import PORT_MAP

#

with open("config.json") as json_conf_file:
    conf = json.load(json_conf_file)

nb_conf =  conf.get('netbox')
nb = pynetbox.api(nb_conf['url'], nb_conf['token'], threading=True)

errors = []
# result = {}


def hex_string(input_string):
    """
    Возвращает HEX-STRING.

    :param str input_string: строка для преобразования в HEX
    :rtype: str
    :return: HEX-STRING
    """

    return ''.join([f'{ord(c):02X}' for c in input_string])


def hex_ip(input_string):
    _hex = hex_string(input_string)
    return '.'.join([str(int(_hex[n:n+2], 16)) for n in range(0,len(_hex),2)])



def get_devices(args):
    list_devices = nb.dcim.devices.filter(**args)
    return  list_devices

@lru_cache
@retry(exceptions=json.JSONDecodeError, tries=5, delay=3, backoff=2, logger=logger)
def walk_lldp(ip, device):
    logger.info(f'Запрашиваем API по {ip}, имя {device}')
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/walk_lldp'
    r = requests.get(url)
    data = r.json()
    lldp_rem_table = data['response']['data'].get('ldpRemTable')
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


def get_local_port_id_from_netbox(device, port):
    port_id = None
    if device.device_type.manufacturer.slug == 'eltex':
        port_name = PORT_MAP.get(port)
        nb_port = nb.dcim.interfaces.get(device_id=device.id, name=port_name)
    else:
        nb_port = nb.dcim.interfaces.get(device_id=device.id, name=port)
    try:
        port_id = nb_port.id
        # ic(nb_port.__dict__)
    except Exception as ex:
        logger.error(f'Exception: {ex}')
        errors.append({device.primary_ip.address.split('/')[0]: 'Нет локального порта в Нетбоксе'})

    return port_id


def get_device_vc_from_netbox(device, port):
    result = None
    for _device in nb.dcim.devices.filter(virtual_chassis_id=device.virtual_chassis.id, id__n=device.id):
        if get_local_port_id_from_netbox(_device, port) and not result:
            result = _device
        else:
            logger.error(f'В шасси есть дублирующиеся порты!')
            errors.append({_device.primary_ip.address.split('/')[0]: 'В шасси задвоились порты в Нетбоксе'})
    return result


def get_remote_device_from_netbox(local_device, local_port, neightbor):

    if neightbor['CidType'] == '4':
        mac = neightbor['Cid']
        device = nb.dcim.devices.get(status='active', cf_MAC=mac )
        if device:
            ic(local_device, 'Сосед найден в Нетбокс')
    elif neightbor['CidType'] == '5':
        _ip = hex_ip(neightbor['Cid'])
        logger.info(f'Не найден IP в Нетбоксе!')
        errors.append({
                        'local_device': local_device.primary_ip.address,
                         _ip: 'Не найден IP в Нетбоксе!',
                        'local_port': local_port,
                        })
        device = None
    else:
        logger.error(f'Не найден МАК в Нетбоксе!')
        errors.append({
                        'local_device': local_device.primary_ip.address,
                        neightbor['Cid']: 'Не найден МАК в Нетбоксе!',
                        'local_port': local_port,
                        })
        device = None
    return device


def get_remote_port_id_from_netbox(remote_device, local_device, neightbor):
    port_id = None
    nb_port = None
    port_name = None
    if remote_device.device_type.manufacturer.slug == 'eltex':
        port_name = neightbor['Pid']
        # nb_port = nb.dcim.interfaces.get(device_id=device.id, name=port_name)

    elif remote_device.device_type.manufacturer.slug == 'd-link':

        # Если вместо номера порта- МАК
        if neightbor['PidType'] == '3':
            if remote_device.device_type.slug == 'dgs-3420-28sc':

                # Диапазон портов - ChaissisID + StackID * 256
                chaisis = (int(neightbor['Pid'], 16) - int(neightbor['Cid'], 16)) // 256
                port = (int(neightbor['Pid'], 16) - int(neightbor['Cid'], 16)) % 256
                port_name = port + 1

            else:
                port_name = int(neightbor['Pid'], 16) - int(neightbor['Cid'], 16)

        if neightbor['PidType'] == '5':
            ...


        # '1/25\x00'
        if neightbor['PidType'] == '7':
            if len(neightbor['Pid']) == 12:
                 neightbor['Pid'] = bytes.fromhex(neightbor['Pid']).decode('utf-8')
            port_name = neightbor['Pid'].strip('\x00').split('/')[-1]

    if port_name:
        nb_port = nb.dcim.interfaces.get(device_id=remote_device.id, name=port_name)
    else:
        logger.error(f'Не удалось вычислить порт соседа: {neightbor}')

    try:
        port_id = nb_port.id
    except Exception as ex:
        logger.error(f'Exception: {ex}')
        errors.append({remote_device.primary_ip.address.split('/')[0]: 'Нет удаленного порта в Нетбоксе',
                    local_device.primary_ip.address.split('/')[0]: remote_device.primary_ip.address.split('/')[0],
                    'Удаленный порт': neightbor['Pid'],
                         })

    return port_id


def create_link(lid, rid):
    result = None
    link_parameters = {
        'termination_a_type': 'dcim.interface',
        'termination_a_id': lid,
        'termination_b_type': 'dcim.interface',
        'termination_b_id': rid,
        'status': 'connected',
        'tags': [{'name':'auto-lldp',
                  'slug':'auto-lldp'}],
        # 'type': '',
    }
    check_lid = nb.dcim.interfaces.get(lid)
    check_rid = nb.dcim.interfaces.get(rid)

    # Проверяем на отсутствие линка в Нетбоксе
    if not check_lid.cable and not check_rid.cable:
        new_link = nb.dcim.cables.create(**link_parameters)
        result = 'Линк создан'
    else:
        result = 'Линк уже есть'
    return result


def main(region):
    logger.info(f'Получаем список устройств в {region} из Нетбокса')
    devices_in_region = get_devices(region)
    # _result = {}
    for device in devices_in_region:

        if device.primary_ip:
            _ip = device.primary_ip.address.split('/')[0]
        else:
            logger.info(f"Нет IP на {device}")
            continue
        ic(device, _ip)
        # Возвращает таблицу соседства из API: 1.5.634570.26.1	"84c9b29913c0"
        lldp_rem_table = walk_lldp(_ip, device)

        if lldp_rem_table:

            # Возвращает таблицу соседства: lldpRT = {26:{'CidType':'4','Cid':'df4e','PidType':'7','Pid':'26'}}
            table = make_remote_table(lldp_rem_table)
            for port, neightbor in table.items():

                # Ищет в Нетбоксе id локального порта
                local_port_id = get_local_port_id_from_netbox(device, port)
                ic(local_port_id, port, PORT_MAP.get(port))
                if not local_port_id: # Для коммутаторов в шасси
                    device_vc = get_device_vc_from_netbox(device, port)
                    if not device_vc:
                        raise(ValueError, "Локальный порт не найдет в девайсах и шасси")
                    local_port_id = get_local_port_id_from_netbox(device_vc, port)
                    ic(local_port_id, port, PORT_MAP.get(port), device_vc)

                #Ищет в Нетбоксе коммутатор по Маку
                remote_device = get_remote_device_from_netbox(device, port, neightbor)
                ic(remote_device, neightbor)
                if not remote_device:
                    logger.error(f"Сосед не найден в NetBox - {port}: {neightbor}")
                    errors.append({port: neightbor,
                                    'Сосед не найден в Нетбокс': device.primary_ip.address

                                    })
                    continue

                #Ищет в Нетбоксе id удаленного порта
                remote_port_id = get_remote_port_id_from_netbox(remote_device, device, neightbor)
                ic(remote_port_id)


                # Создает линк между портами коммутаторов в Нетбоксе
                link = create_link(local_port_id, remote_port_id)
                ic(link)
                if link:
                    pass
                else:
                    ic('Error create link', local_port_id, remote_port_id)

        else:
            logger.error(f'Нет соседства у {_ip}')
            errors.append({_ip: 'Нет соседства (lldp_rem_table пуста)'})
    # result.update(_result)


if __name__ == '__main__':
    region = 'pr-cherepnina-2a'
    roles = [
        'distribution-switch',
        'access-switch',
        ]
    for role in roles:
        params = {
            'region': region,
            # 'tag': 'test-lldp',
            'status': 'active',
            'role':role,
            # 'name': 'oz-ul-lopatina-20a.1',
        }
        main(params)


        # with open(f'output/success_lldp_{region}.json', 'w', encoding='utf-8-sig') as json_file:
        #     json.dump(result, json_file, indent=4, sort_keys=True)

        with open(f'output/errors_lldp_{region}_{role}.json', 'w', encoding='utf-8-sig') as json_file2:
            json.dump(errors, json_file2, indent=4, sort_keys=True)

    ic('Готово')
    ic(f'Ошибки: {errors}')


