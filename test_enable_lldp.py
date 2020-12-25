from make_ports_for_lldp import make_port_range

DLINK_PORTS = range(1, 29)
# ELTEX_PORTS = [
#     "fa1/0/1",
#     "fa1/0/2",
#     "fa1/0/3",
#     "fa1/0/4",
#     "fa1/0/5",
#     "fa1/0/6",
#     "fa1/0/7",
#     "fa1/0/8",
#     "fa1/0/9",
#     "fa1/0/10",
#     "fa1/0/11",
#     "fa1/0/12",
#     "fa1/0/13",
#     "fa1/0/14",
#     "fa1/0/15",
#     "fa1/0/16",
#     "fa1/0/17",
#     "fa1/0/18",
#     "fa1/0/19",
#     "fa1/0/20",
#     "fa1/0/21",
#     "fa1/0/22",
#     "fa1/0/23",
#     "fa1/0/24",
# ]

# def make_ports(_list_ports):
#     _ports_for_command = '-'.join([_list_ports[0], _list_ports[-1].split('/')[-1]])
#     return _ports_for_command

# def test_make_ports():
#     assert make_ports(ELTEX_PORTS) == "fa1/0/1-24"
#     assert make_ports(ELTEX_PORTS[0:5]) == "fa1/0/1-5"
#     assert make_ports(ELTEX_PORTS[1:3]) == "fa1/0/2-3"


# def get_untagged_ports(data):
#     list_ports = []
#     pos = 0
#     while pos != -1:
#         port = data.find('1', pos)
#         if port == -1:
#             pos = -1
#         else:
#             list_ports.append(port + 1)
#             pos = port + 1
#     return list_ports


# def test_get_untagged_ports():
#     assert get_untagged_ports('1111111100000000000000000000000000000000000000000000000000000000') == [1, 2, 3, 4, 5, 6, 7, 8]

def test_make_port_range():
    assert make_port_range(DLINK_PORTS) == "1-28"
    assert make_port_range(DLINK_PORTS[0:24]) == "1-24"
    assert make_port_range([1, 2, 3, 4, 5, 7, 8, 12, 13, 15, 18]) == "1-5,7-8,12-13,15,18"


# if __name__ == '__main__':
#     print(get_untagged_ports('1111111101000000000110000000000000000000000000000000000000000000'))
