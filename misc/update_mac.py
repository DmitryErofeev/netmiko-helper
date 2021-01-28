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

nb = pynetbox.api(url=netbox_conf['url'], token=netbox_conf['token'], threading=True)

fail = []
succes = []

def get_devices_in_region(region, role):
    logger.info(f'Получаем из Нетбокса список коммутаторов в {region}')
    devices_list = nb.dcim.devices.filter(region=region, status='active', role=role)
    return devices_list

@retry(exceptions=Exception, tries=5, delay=3, backoff=2, logger=logger)
def ask_devices_for_mac(ip):
    temp_dict = {}

    url = f'http://192.168.81.130:7577/teleusl/{ip}/1/get_deviceMac'
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


def main(region, role):
    devices_in_region = get_devices_in_region(region, role)

    for device in devices_in_region:
        # try:
            no_error = {}
            logger.info(f'Получаем по API MAC адрес устройства {device}')
            device_ip = device.primary_ip.address.split('/')[0]
            valid_data_from_device = ask_devices_for_mac(device_ip)

            # logger.info(f'Записываем из Нетбокса кастомное поле с МАКом') # может и не надо, но, пока, пусть будет
            # p_mac_from_netbox = device.custom_fields.P_MAC


            custom_fields = device.custom_fields.copy()

            if not custom_fields.get('Model'):
                if valid_data_from_device.get('model') == "None":
                    logger.error(f'API не вернул model {device.device_type.model} ')
                    error = {}
                    error['ip'] = device.primary_ip.address.split('/')[0]
                    fail.append(error)

                else:
                    custom_fields |= {'Model': valid_data_from_device['model'] }
                    logger.info(f'Записываем model из устройства в кастомное поле "Model" в Нетбокс')
                    no_error['Model'] = 'Model-yes'
                    no_error['ip'] = device_ip
                    succes.append(no_error)

            if not custom_fields.get('sysDescr'):
                if not valid_data_from_device.get('sys_descr'):
                    logger.error(f'API не вернул sys_descr {device.device_type.model} ')
                    error = {}
                    error['ip'] = device.primary_ip.address.split('/')[0]
                    fail.append(error)

                else:
                    custom_fields |= {'sysDescr': valid_data_from_device['sys_descr'] }
                    logger.info(f'Записываем sysDescr из устройства в кастомное поле "sysDescr" в Нетбокс')
                    no_error['sysDescr'] = 'sysDescr-yes'
                    no_error['ip'] = device_ip
                    succes.append(no_error)


            if not custom_fields.get('MAC'):
                if not valid_data_from_device.get('mac'):
                    logger.error(f'API не вернул Mac {device.device_type.model} ')
                    error = {}
                    error['ip'] = device.primary_ip.address.split('/')[0]
                    fail.append(error)

                else:
                    custom_fields |= {'MAC': valid_data_from_device['mac'].lower() }
                    logger.info(f'Записываем МАК из устройства в кастомное поле "Mac" в Нетбокс')
                    no_error['MAC'] = 'MAC-yes'
                    no_error['ip'] = device_ip
                    succes.append(no_error)

            device.update({'custom_fields': custom_fields})


    logger.info(f'Регион обработан')


if __name__ == '__main__':
    region = 'oz'
    role = 'access-switch'
    main(region, role)

    with open(f'output/success_mac_{region}.json', 'w') as file1:
        json.dump(succes, file1, indent=4, sort_keys=True)

    with open(f'output/error_mac_{region}.json', 'w') as file2:
        json.dump(fail, file2, indent=4, sort_keys=True)
