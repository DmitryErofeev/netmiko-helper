from loguru import logger
import netmiko
# import paramiko
# from paramiko.ssh_exception import SSHException
# from netmiko.ssh_exception import NetmikoTimeoutException



commands = {
    'eltex':
    [
        'sh lldp configuration'
    ],

    'd-link':
    [
        'enable admin',
        'config lldp ports {range} admin_status rx_only',
        'enable lldp',
        'sh lldp',
    ]
}

# configs = {
#     'eltex':
#     [
#         'lldp run',
#         'int ra {range}',
#         'no lldp transmit',
#     ]
# }


def do_connect_3010(vendor, ip, params, ports):
    _device_result = {}
    # _error = {} # ошибки выполнение команд
    _success = {} # успешное выполнение команд

    # try:
    with netmiko.ConnectHandler(**params) as ssh:

        # if configs.get(_vendor):
        #     _conf = [c.format(range=_range) for c in configs.get(_vendor)]
        #     out = ssh.send_config_set(_conf)
        #     logger.info(f'Выполнен конфиг Элтекса.')
        #     if "Unrecognized command" in out:
        #         logger.info(f'Achtung!: {out}')

        for command in commands[vendor]:
            _device_result['ip'] = ip
            _device_result['vendor'] = vendor
            command = command.format(range=ports)

            if 'enable admin' in command:
                logger.info(f'Включаю enable на: {ip}')
                out = ssh.send_command_timing(command, use_textfsm=True)
                while isinstance(out, str) and out.startswith(':', -1):
                    out = ssh.send_command_timing("admin")
                    logger.info(f'{out}')
                    # out = netmiko.utilities.get_structured_data(out, platform=_params['device_type'], command=command)

            elif command.startswith('sh') :
                out = ssh.send_command(command, use_textfsm=True)
                _device_result['lldp_status'] = out[0]['lldp_status']
                logger.info(f'Проверяю выполнение команды: {command}: {out}')

            elif command.startswith('config lldp ports') :
                out = ssh.send_command(command, use_textfsm=True)
                _device_result['config_lldp_ports'] = out[0]['lldp_ports']
                _device_result['ports'] = ports
                logger.info(f'Проверяю выполнение команды: {command}: {out}')

            else:
                out = ssh.send_command(command, use_textfsm=True)
                _device_result['enable_lldp'] = out
                logger.info(f'Проверяю выполнение команды: {command}: {out}')

        ssh.save_config()
        _success = _device_result


    # except (TimeoutError, NetmikoTimeoutException, OSError, SSHException, netmiko.ssh_exception.NetmikoTimeoutException, paramiko.ssh_exception.SSHException,
    # ConnectionResetError, netmiko.ssh_exception.NetmikoAuthenticationException, netmiko.ssh_exception.NetMikoTimeoutException) as ex:
    #     _device_result['ip'] = ip
    #     _device_result['vendor'] = vendor
    #     _device_result['error'] = f'{ex.args} - {ex.__class__.__name__}'

    #     _error = _device_result
    return _success
