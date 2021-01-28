import requests
import pynetbox
import json
from loguru import logger
from retry import retry


with open("../config.json") as json_conf_file:
    conf = json.load(json_conf_file)

nb_conf =  conf.get('netbox')




def main(region):



if __name__ == '__main__':
    region = 'kb'
    main(region)