import requests


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


def make_ports(ip): # функция для вызова из главного файла
    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/walk_vlan'
    r = requests.get(url).json()

    ungagged_ports_in_vlans = r["response"]["data"]['VlanList']

    port_list = set()

    for vlan, ports in ungagged_ports_in_vlans.items():  # записываем untagged порты во всех виланах во множество
        port_list.update(get_untagged_ports(decode_ports(ports)))

    sorted_port_list = sorted(port_list) # сортируем порты по порядку
    ports_for_command = make_port_range(sorted_port_list)
    return ports_for_command




if __name__ == '__main__':

    # url = 'http://192.168.81.130:7577/teleusl/10.100.0.207/1/walk_vlan'
    url = 'http://192.168.81.130:7577/teleusl/10.110.10.137/1/walk_vlan' #DES-3200-10
    # url = 'http://192.168.81.130:7577/teleusl/10.100.3.59/1/walk_vlan' #DES-3200-28-C1


    r = requests.get(url).json()
    # v3 = r["response"]["data"]['VlanList']['1.2.3']
    # v777 = r["response"]["data"]['VlanList']['1.2.777']
    ungagged_ports_in_vlans = r["response"]["data"]['VlanList']


    port_list = set()

    for vlan, ports in ungagged_ports_in_vlans.items():  # записываем untagged порты во всех виланах во множество
        port_list.update(get_untagged_ports(decode_ports(ports)))

    sorted_port_list = sorted(port_list) # сортируем порты по порядку
    ports_for_command = make_port_range(sorted_port_list)


    # print(port_list)
    # print(sorted_port_list)
    # print(ports_for_command)





