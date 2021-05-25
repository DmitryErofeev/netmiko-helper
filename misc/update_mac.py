import requests
import pynetbox
import json
from loguru import logger
from retry import retry
# Обновляет в Нетбоксе поле MAC, Model, Sys_Descr маком из свитча.


with open('config.json') as json_conf_file:
    config = json.load(json_conf_file)

netbox_conf = config.get('netbox')
# devices_user = config.get('device')

nb = pynetbox.api(url=netbox_conf['url'],
                  token=netbox_conf['token'], threading=True)

fail = []
succes = []


def get_devices_in_region(params):
    logger.info('Получаем из Нетбокса список коммутаторов ')
    devices_list = nb.dcim.devices.filter(**params)
    return devices_list


@retry(exceptions=Exception, tries=5, delay=3, backoff=2, logger=logger)
def ask_devices_for_mac(device):

    temp_dict = {}

    ip = device.primary_ip.address.split('/')[0]

    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/get_deviceMac'
    url_stack = f'http://192.168.81.130:7577/teleusl/{ip}/1/get_StackTable'


    if device.virtual_chassis:
        r = requests.get(url_stack)
        r = r.json()  # r = json.loads(r.text)
        sys_descr = r['response']['sys_descr']
        model = r['response']['model']
        macs = r['response']['data'].get('StackMacAddr')

        temp_dict['sys_descr'] = sys_descr
        temp_dict['model'] = model
        if macs:
            temp_dict['stack'] = macs

        else:
            temp_dict['sys_descr'] = sys_descr
            temp_dict['model'] = model
            temp_dict['mac'] = ''

    else:
        r = requests.get(url)
        r = r.json()  # r = json.loads(r.text)
        sys_descr = r['response']['sys_descr']
        model = r['response']['model']
        mac = r['response']['data'].get('dot1dBaseBridgeAddress')
        if mac:
            temp_dict['sys_descr'] = sys_descr
            temp_dict['model'] = model
            temp_dict['mac'] = mac['.0']
        else:
            temp_dict['sys_descr'] = sys_descr
            temp_dict['model'] = model
            temp_dict['mac'] = ''

    return temp_dict


def write_mac_on_netbox(device, valid_data_from_device):
    no_error ={}
    error = {}

    ip = device.primary_ip.address.split('/')[0] if device.primary_ip else "None"
    custom_fields = device.custom_fields.copy()

    if not custom_fields.get('Model'):
        if valid_data_from_device.get('model') == "None":
            logger.error(
                f'API не вернул model {device.device_type.model} ')
            error['no_model'] = ip

        else:
            custom_fields |= {'Model': valid_data_from_device['model']}
            logger.info(
                'Есть Model')
            no_error['Model'] = 'Model-yes'
            no_error['ip'] = ip
    else:
        logger.info('поле модель уже заполнено')
        no_error['поле модель уже заполнено'] = ip

    if not custom_fields.get('sysDescr'):
        if not valid_data_from_device.get('sys_descr'):
            logger.error(
                f'API не вернул sys_descr {device.device_type.model} ')
            error['no_sys_descr'] = ip

        else:
            custom_fields |= {
                'sysDescr': valid_data_from_device['sys_descr']}
            logger.info(
                'Есть sysDescr ')
            no_error['sysDescr'] = 'sysDescr-yes'
            no_error['ip'] = ip

    else:
        logger.info('поле sysDescr уже заполнено')
        no_error['поле sysDescr уже заполнено'] = ip

    if not custom_fields.get('MAC'):

        if device.virtual_chassis:
            custom_fields |= {'MAC': valid_data_from_device['stack'][str(device.vc_position)].lower()}
            logger.info(
                'Есть МАК')
            no_error['MAC'] = 'MAC-yes'
            no_error['ip'] = ip

        else:
            custom_fields |= {'MAC': valid_data_from_device['mac'].lower()}
            logger.info(
                'Есть МАК')
            no_error['MAC'] = 'MAC-yes'
            no_error['ip'] = ip
    else:
        logger.info('поле MAC уже заполнено')
        no_error['поле MAC уже заполнено'] = ip

    logger.info('Обновляем custom_fields в Нетбоксе.')
    device.update({'custom_fields': custom_fields})
    return no_error, error


def main(params):
    devices_in_region = get_devices_in_region(params)

    for device in devices_in_region:
        valid_data_from_device = ask_devices_for_mac(device)

        if device.virtual_chassis:  # сначала обрабатываем стэки
            stack_devices = nb.dcim.devices.filter(virtual_chassis_id=device.virtual_chassis.id)
            for stack_device in stack_devices:
                logger.warning(f'Получаем по API MAC адрес устройства {stack_device}')
                no_error, error = write_mac_on_netbox(stack_device, valid_data_from_device)
                succes.append(no_error)
                fail.append(error)

        else:  # потом обрабатываем не стековые коммутаторы
            logger.info(f'Получаем по API MAC адрес устройства {device}')
            no_error, error = write_mac_on_netbox(device, valid_data_from_device)
            succes.append(no_error)
            fail.append(error)

        logger.info('Коммутатор или стэк обработан.')


if __name__ == '__main__':
    device_params = {
        'name': 'oz-ul-gagarina-31',
        # 'name': 'dm-ul-novaya-11.3.1',
        # 'region': 'pr-cherepnina-2a',
        # 'role': 'access-switch',
    }
    main(device_params)

    with open('output/success_mac.json', 'w') as file1:
        json.dump(succes, file1, indent=4, sort_keys=True)

    with open('output/error_mac.json', 'w') as file2:
        json.dump(fail, file2, indent=4, sort_keys=True)
