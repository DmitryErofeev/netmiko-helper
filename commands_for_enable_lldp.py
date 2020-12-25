from loguru import logger
import netmiko


commands = {
    'eltex':
    [
        'sh lldp configuration'
    ],

    'd-link':
    [
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


def do_connect(vendor, ip, params, ports):
    _device_result = {}
    _error = {} # ошибки выполнение команд
    _success = {} # успешное выполнение команд

    try:
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

                if command.startswith('sh') :
                    out = ssh.send_command(command, use_textfsm=True)
                    _device_result['lldp_status'] = out[0]['lldp_status']

                command = command.format(range=ports)
                out = ssh.send_command(command, use_textfsm=True)
                logger.info(f'Проверяю выполнение команды: {command}: {out}')

                # if not isinstance(out, list):
                #     raise ValueError("Error in result", out, _params['ip'], command)

                # else:
                #     out = ssh.send_command(command.format(range=_range))
                #     logger.info(f'Посылаю команду: {out}')


            ssh.save_config()
            _success = _device_result

    except (TimeoutError, netmiko.ssh_exception.SSHException, ConnectionResetError, netmiko.ssh_exception.NetmikoAuthenticationException,
        netmiko.ssh_exception.NetMikoTimeoutException) as ex:
        _device_result['ip'] = ip
        _device_result['vendor'] = vendor
        _device_result['error'] = f'{ex.args} - {ex.__class__.__name__}'

        _error = _device_result
    return _error, _success
