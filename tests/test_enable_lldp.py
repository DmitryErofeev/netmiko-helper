# from make_ports_for_lldp import make_port_range

# DLINK_PORTS = range(1, 29)
ELTEX_PORTS = [
    "fa1/0/1",
    "fa1/0/2",
    "fa1/0/3",
    "fa1/0/4",
    "fa1/0/5",
    "fa1/0/6",
    "fa1/0/7",
    "fa1/0/8",
    "fa1/0/9",
    "fa1/0/10",
    "fa1/0/11",
    "fa1/0/12",
    "fa1/0/13",
    "fa1/0/14",
    "fa1/0/15",
    "fa1/0/16",
    "fa1/0/17",
    "fa1/0/18",
    "fa1/0/19",
    "fa1/0/20",
    "fa1/0/21",
    "fa1/0/22",
    "fa1/0/23",
    "fa1/0/24",
]

def make_ports(_list_ports):
    _ports_for_command = '-'.join([_list_ports[0], _list_ports[-1].split('/')[-1]])
    return _ports_for_command

# def test_make_ports():
#     assert make_ports(ELTEX_PORTS) == "fa1/0/1-24"
#     assert make_ports(ELTEX_PORTS[0:5]) == "fa1/0/1-5"
#     assert make_ports(ELTEX_PORTS[1:3]) == "fa1/0/2-3"


def get_untagged_ports(data):
    list_ports = []
    pos = 0
    while pos != -1:
        port = data.find('1', pos)
        if port == -1:
            pos = -1
        else:
            list_ports.append(port + 1)
            pos = port + 1
    return list_ports


# def test_get_untagged_ports():
#     assert get_untagged_ports('1111111100000000000000000000000000000000000000000000000000000000') == [1, 2, 3, 4, 5, 6, 7, 8]

# def test_make_port_range():
#     assert make_port_range(DLINK_PORTS) == "1-28"
#     assert make_port_range(DLINK_PORTS[0:24]) == "1-24"
#     assert make_port_range([1, 2, 3, 4, 5, 7, 8, 12, 13, 15, 18]) == "1-5,7-8,12-13,15,18"



import re


def check_is_mac(mac):
    if mac is None:
        return False

    mac_mask = re.compile(r'\.|\-|\:')
    raw_mac = re.sub(mac_mask, '', mac).lower()
    result = re.match("^[0-9a-f]{12}$", raw_mac)

    if not result:
        return False
    else:
        return True


def test_check_is_mac():
    assert check_is_mac('9094E4B4FAC0') == True
    assert check_is_mac('90-94-E4-B4-FA-C0') == True
    assert check_is_mac(None) == False
    assert check_is_mac('z0-d9-e3-39-68-40') == False
    assert check_is_mac('e0-d9-e3-39-ca-80|e0-d9-e3-39-5b-40') == False
    assert check_is_mac('e0-d9-e3-15-6e-80, e0-d9-e3-15-8b-80') == False
    assert check_is_mac('0022.B056.F943') == True
    assert check_is_mac('e0-d9-e3-38-3d-c0 e0-d9-e3-38-80-00') == False
    assert check_is_mac(' 00-22-B0-50-67-E7') == False
    assert check_is_mac('DES-3200-28') == False


if __name__ == '__main__':
    print(get_untagged_ports('1111111101000000000110000000000000000000000000000000000000000000'))