from loguru import logger
import netmiko
# import logging

# logging.basicConfig(filename='test.log', level=logging.DEBUG)

commands = {
    # 'eltex':
    #     ['show syslog-servers'],
    'd-link':
        [
            'enable snmp',
            'enable snmp tra',
            'delete snmp community public',
            'delete snmp community private',
            'delete snmp community tuslemon5',
            'create snmp community tuslemon5 ReadOnly',
            'create snmp community tuslemon5 view CommunityView read_only',
        ],
}

configs = {
        'eltex':
            [
                'snmp-server community encrypted dd80932159a7e0717e ro view Default',
            ]
}


def do_connect(_vendor, _ip, _params):
    _device_result = {}
    _error = {} # ошибки выполнение команд
    _success = {} # успешное выполнение команд

    try:
        with netmiko.ConnectHandler(**_params) as ssh:

            # посылаем конфиг Элтекса, если он есть
            if cfg := configs.get(_vendor):
                out = ssh.send_config_set(cfg, cmd_verify=False)
                logger.info(f'Выполняю configs Элтекса:{_ip} {out}')
                _device_result['ip'] = _ip
                _device_result['vendor'] = _vendor

            if commands.get(_vendor):
                _device_result['vendor'] = _vendor
                for command in commands.get(_vendor):
                    _device_result['ip'] = _ip

                    # if 'enable admin' in command:
                    #     logger.info(f'Включаю enable на: {_ip}')
                    #     out = ssh.send_command_timing(command, use_textfsm=True)
                    #     while isinstance(out, str) and out.startswith(':', -1):
                    #         out = ssh.send_command_timing("admin")
                    #         logger.info(f'{out}')
                    #         # out = netmiko.utilities.get_structured_data(out, platform=_params['device_type'], command=command)

                    # else:
                    logger.info(f'Применяю команду: {command} на {_vendor} IP: {_ip}')
                    out = ssh.send_command(command, use_textfsm=True)
                    logger.info(f'Результат: {command} на {_vendor} IP: {_ip} {out}')

                    # if 'show syslog-servers' in command:
                    #     _device_result['status'] = out[0]['status']

                    # if 'enable syslog' in command:
                    #     _device_result['enable_syslog'] = out[0]['enable']

                    # if 'show syslog host' in command:
                    #     _device_result['ip_syslog_sever'] = out[0]['ip']

            ssh.save_config()
            logger.info(f'{_device_result}')

        _success = _device_result

    except (TimeoutError, OSError, ConnectionResetError, netmiko.ssh_exception.SSHException, netmiko.ssh_exception.NetmikoAuthenticationException,
        netmiko.ssh_exception.NetMikoTimeoutException) as ex:
        _device_result['ip'] = _ip
        _device_result['vendor'] = _vendor
        _device_result['error'] = f'{ex.args} - {ex.__class__.__name__}'

        _error = _device_result
    return _error, _success
