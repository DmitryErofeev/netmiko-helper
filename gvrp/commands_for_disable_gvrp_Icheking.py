from loguru import logger
import netmiko


commands = {

    'd-link':
    [
        'config gvrp all ingress_checking disable',
    ]
}


def do_connect(vendor, ip, params): # ports
    _device_result = {}

    with netmiko.ConnectHandler(**params) as ssh:

        for command in commands[vendor]:
            _device_result['ip'] = ip
            _device_result['vendor'] = vendor
            # _device_result['ports'] = ports
            logger.info(f'Выполняю команду: {command}')
            out = ssh.send_command(command, use_textfsm=True) # command = command.format(range=ports)
            _device_result['gvrp_disabled'] = out[0]['gvrp_disable']
            logger.info(f'GVRP выключен на: {ip}')

        ssh.save_config()
        _success = _device_result

    return _success
