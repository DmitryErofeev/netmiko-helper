from loguru import logger
import netmiko


commands = {
    # 'eltex':
    # [
    #     'sh lldp configuration'
    # ],

    'd-link':
    [
        # 'config lldp ports {range} admin_status rx_only',
        # 'enable lldp',
        'config lldp forward_message disable',
        'sh lldp',
    ]
}

configs = {
    # 'eltex':
    # [
    #     'lldp run',
    #     'int ra {range}',
    #     'no lldp transmit',
    # ]
}


def do_connect(vendor, ip, params): # ports
    _device_result = {}

    with netmiko.ConnectHandler(**params) as ssh:

        # посылаем конфиг Элтекса, если он есть
        # if cfg := configs.get(vendor):
        #     eltex_config = []
        #     for command in cfg:
        #         eltex_config.append(command.format(range=ports))
        #     out = ssh.send_config_set(eltex_config, cmd_verify=False)
        #     logger.info(f'Выполняю configs Элтекса:{ip} {out}')
        #     _device_result['ip'] = ip
        #     _device_result['vendor'] = vendor
        #     _device_result['ports'] = ports

        for command in commands[vendor]:
            _device_result['ip'] = ip
            _device_result['vendor'] = vendor
            # _device_result['ports'] = ports
            logger.info(f'Выполняю команду: {command}')
            out = ssh.send_command(command, use_textfsm=True) # command = command.format(range=ports)
            if command.startswith('sh lldp'):
                _device_result['forward_lldp'] = out[0]['lldp_forward_status']
                logger.info(f'lldp forward: {out}')
            # if command.startswith('sh') :
            #     out = ssh.send_command(command, use_textfsm=True)
            #     _device_result['lldp_status'] = out[0]['lldp_status']
            #     logger.info(f'Проверяю выполнение команды: {command}: {out}')

            # elif command.startswith('config lldp ports') :
            #     out = ssh.send_command(command, use_textfsm=True)
            #     _device_result['config_lldp_ports'] = out[0]['lldp_ports']
            #     _device_result['ports'] = ports
            #     logger.info(f'Проверяю выполнение команды: {command}: {out}')

            # else:
                # out = ssh.send_command(command, use_textfsm=True)
                # _device_result['enable_lldp'] = out[0]['lldp_enable']
                # logger.info(f'Проверяю выполнение команды: {command}: {out}')

        ssh.save_config()
        _success = _device_result
    return _success
