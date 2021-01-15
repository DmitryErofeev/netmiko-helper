import requests
from retry import retry
from loguru import logger


PORT_MAP = {
    '1': 'fa1/0/1',
    '2': 'fa1/0/2',
    '3': 'fa1/0/3',
    '4': 'fa1/0/4',
    '5': 'fa1/0/5',
    '6': 'fa1/0/6',
    '7': 'fa1/0/7',
    '8': 'fa1/0/8',
    '9': 'fa1/0/9',
    '10': 'fa1/0/10',
    '11': 'fa1/0/11',
    '12': 'fa1/0/12',
    '13': 'fa1/0/13',
    '14': 'fa1/0/14',
    '15': 'fa1/0/15',
    '16': 'fa1/0/16',
    '17': 'fa1/0/17',
    '18': 'fa1/0/18',
    '19': 'fa1/0/19',
    '20': 'fa1/0/20',
    '21': 'fa1/0/21',
    '22': 'fa1/0/22',
    '23': 'fa1/0/23',
    '24': 'fa1/0/24',

    '49' : 'gi1/0/1',
    '50' : 'gi1/0/2',
    '51' : 'gi1/0/3',
    '52' : 'gi1/0/4',
    '53' : 'gi1/0/5',
    '54' : 'gi1/0/6',
    '55' : 'gi1/0/7',
    '56' : 'gi1/0/8',
    '57' : 'gi1/0/9',
    '58' : 'gi1/0/10',
    '59' : 'gi1/0/11',
    '60' : 'gi1/0/12',
    '61' : 'gi1/0/13',
    '62' : 'gi1/0/14',
    '63' : 'gi1/0/15',
    '64' : 'gi1/0/16',
    '65' : 'gi1/0/17',
    '66' : 'gi1/0/18',
    '67' : 'gi1/0/19',
    '68' : 'gi1/0/20',
    '69' : 'gi1/0/21',
    '70' : 'gi1/0/22',
    '71' : 'gi1/0/23',
    '72' : 'gi1/0/24',

    '105': 'te1/0/1',
    '106': 'te1/0/2',
    '107': 'te1/0/3',
    '108': 'te1/0/4',

    '109': 'fa2/0/1',
    '110': 'fa2/0/2',
    '111': 'fa2/0/3',
    '112': 'fa2/0/4',
    '113': 'fa2/0/5',
    '114': 'fa2/0/6',
    '115': 'fa2/0/7',
    '116': 'fa2/0/8',
    '117': 'fa2/0/9',
    '118': 'fa2/0/11',
    '119': 'fa2/0/11',
    '120': 'fa2/0/12',
    '121': 'fa2/0/13',
    '122': 'fa2/0/14',
    '123': 'fa2/0/15',
    '124': 'fa2/0/16',
    '125': 'fa2/0/17',
    '126': 'fa2/0/18',
    '127': 'fa2/0/19',
    '128': 'fa2/0/20',
    '129': 'fa2/0/21',
    '130': 'fa2/0/22',
    '131': 'fa2/0/23',
    '132': 'fa2/0/24',

    '157': 'gi2/0/1',
    '158': 'gi2/0/2',
    '159': 'gi2/0/3',
    '160': 'gi2/0/4',
    '161': 'gi2/0/5',
    '162': 'gi2/0/6',
    '163': 'gi2/0/7',
    '164': 'gi2/0/8',
    '165': 'gi2/0/9',
    '166': 'gi2/0/10',
    '167': 'gi2/0/11',
    '168': 'gi2/0/12',
    '169': 'gi2/0/13',
    '170': 'gi2/0/14',
    '171': 'gi2/0/15',
    '172': 'gi2/0/16',
    '173': 'gi2/0/17',
    '174': 'gi2/0/18',
    '175': 'gi2/0/19',
    '176': 'gi2/0/20',
    '177': 'gi2/0/21',
    '178': 'gi2/0/22',
    '179': 'gi2/0/23',
    '180': 'gi2/0/24',

    '213': 'te2/0/1',
    '214': 'te2/0/2',
    '215': 'te2/0/3',
    '216': 'te2/0/4',
    }


class VlanListNotFound(Exception):
    pass


def decode_ports(hex_ports): # преобразуем хекс в двоичный формат
    return ''.join('{:08b}'.format(b) for c, b in enumerate(hex_ports.encode('utf-16-le')) if c % 2 == 0 )


def get_untagged_ports(data): # преобразуем бинарный список портов в цифры
    list_ports = []
    pos = -1
    while (pos := data.find('1', pos + 1)) != -1:
        list_ports.append(pos + 1)

    return list_ports


def make_port_range(intList): # из листа создает строку с номерами портов вида 1-24
    """
    for D-Link
    """
    ret = []
    for val in sorted(intList):
        if not ret or ret[-1][-1]+1 != val:
            ret.append([val])
        else:
            ret[-1].append(val)
    return ",".join([str(x[0]) if len(x)==1 else str(x[0])+"-"+str(x[-1]) for x in ret])


def convert_indexPort_to_numberPort(ports):# Переводит индекса порта Элтекса в номер порта:'49' -> 'gi1/0/1',
    list_ports = []
    for index in ports:
        eltex_port = PORT_MAP[str(index)]
        list_ports.append(eltex_port)
    return list_ports


def make_port_range_eltex(portsList): # из листа создает строку с номерами портов вида fa1/0/2,fa1/0/7,fa1/0/10-12,gi1/0/2
    """
    for Eltex
    """
    intList = convert_indexPort_to_numberPort(portsList)

    ret = {} # в дикте создаются листы с именем fa1/0
    for val in intList:  # 'fa1/0/2'
        _vs = val.rsplit('/', 1)  # ['fa1/0', '2']
        if not ret.get(_vs[0]):
            ret[_vs[0]] = []  # {'fa1/0': []}
        if not ret[_vs[0]] or ret[_vs[0]][-1][-1]+1 != int(_vs[1]):
            ret[_vs[0]].append([int(_vs[1])])
        else:
            ret[_vs[0]][-1].append(int(_vs[1]))

    result = []
    for pr in ret:
        result.append( ",".join([pr+"/"+str(x[0]) if len(x)==1 else pr+"/"+str(x[0])+"-"+str(x[-1]) for x in ret[pr]]) )

    return ",".join(result)


# def make_port_range_eltex(list_ports): # из листа создает строку с номерами портов вида fa1/0/10-12
#     _ports_for_command = '-'.join([list_ports[0], list_ports[-1].split('/')[-1]])
#     return _ports_for_command


@retry(exceptions=Exception, tries=5, delay=2, backoff=2, logger=logger) #Функция для Д-Линка

def make_ports(ip): # функция для вызова из главного файла
    """
    for D-Link
    """
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/walk_vlan'
    r = requests.get(url).json()

    ungagged_ports_in_vlans = r["response"]["data"].get('VlanList')
    if not ungagged_ports_in_vlans:
        return None
    port_list = set()

    for vlan, ports in ungagged_ports_in_vlans.items():  # записываем untagged порты во всех виланах во множество
        port_list.update(get_untagged_ports(decode_ports(ports)))

    sorted_port_list = sorted(port_list) # сортируем порты по порядку
    ports_for_command = make_port_range(sorted_port_list)
    return ports_for_command


@retry(exceptions=Exception, tries=5, delay=2, backoff=2, logger=logger) #Функция для Д-Линка
def make_ports_eltex(ip): # функция для вызова из главного файла
    """
    for Eltex
    """
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/walk_vlan'
    r = requests.get(url).json()

    ungagged_ports_in_vlans = r["response"]["data"].get('VlanList')
    if not ungagged_ports_in_vlans:
        return None
    port_list = set()

    for vlan, ports in ungagged_ports_in_vlans.items():  # записываем untagged порты во всех виланах во множество
        port_list.update(get_untagged_ports(decode_ports(ports)))

    sorted_port_list = sorted(port_list) # сортируем порты по порядку
    ports_for_command = make_port_range_eltex(sorted_port_list)
    return ports_for_command

if __name__ == '__main__':

    url = 'http://192.168.81.130:7577/teleusl/10.100.0.207/1/walk_vlan'

    # url = 'http://192.168.81.130:7577/teleusl/10.100.3.58/1/walk_vlan' #DES-2124
    # url = 'http://192.168.81.130:7577/teleusl/10.110.10.137/1/walk_vlan' #DES-3200-10
    # url = 'http://192.168.81.130:7577/teleusl/10.100.3.59/1/walk_vlan' #DES-3200-28-C1

    r = requests.get(url).json()
    ungagged_ports_in_vlans = r["response"]["data"]['VlanList']

    port_list = set()

    for vlan, ports in ungagged_ports_in_vlans.items():  # записываем untagged порты во всех виланах во множество
        port_list.update(get_untagged_ports(decode_ports(ports)))

    sorted_port_list = sorted(port_list) # сортируем порты по порядку
    ports_for_command = make_port_range(sorted_port_list)
    eltex_ports = convert_indexPort_to_numberPort(sorted_port_list)
    eltex_ports_for_command = make_port_range_eltex(eltex_ports)


    print(port_list)
    print(sorted_port_list)
    print(ports_for_command)
    print(eltex_ports)
    print(eltex_ports_for_command)



