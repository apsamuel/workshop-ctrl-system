from gpiozero import *
import time
import json
from json import JSONEncoder
from RPi import GPIO
from bs4 import BeautifulSoup
import requests
import re

from urllib.parse import (
    urlparse,
    urljoin)


class PiInfoEncoder(JSONEncoder):
    def default(self, object, klass):
        if isinstance(object, klass):
            return object.__dict__
        else:
            return JSONEncoder.default(
                self,
                object
            )
class PiInfo(object):
    data = pi_info()


    def __json__(self):
        return json.dumps(self.__dict__)
        
    def to_json(self):
        return self.__json__()
    ##GPIO.setmode(GPIO.BCM)
    def __init__(self):
        data = self.__class__.data
        factory = Device._default_pin_factory()
        self.GPIO_FUNCTIONS = {
        'input':   GPIO.IN,
        'output':  GPIO.OUT,
        'i2c':     GPIO.I2C,
        'spi':     GPIO.SPI,
        'pwm':     GPIO.HARD_PWM,
        'serial':  GPIO.SERIAL,
        'unknown': GPIO.UNKNOWN,
        }

        self.GPIO_PULL_UPS = {
        'up':       GPIO.PUD_UP,
        'down':     GPIO.PUD_DOWN,
        'floating': GPIO.PUD_OFF,
        }

        self.GPIO_EDGES = {
        'both':    GPIO.BOTH,
        'rising':  GPIO.RISING,
        'falling': GPIO.FALLING,
        }


        self.headers = list(
            data.headers.keys()
        )

        j8 = data.headers['J8']
        poe = data.headers['POE']
        self.poepins = poe.pins
        self.gpiopins = j8.pins
        self.system = {
            'manufacturer': data.manufacturer,
            'system': "Raspberry Pi {} ({})".format(data.model, data.revision),
            'released': data.released,
            'model': data.model,
            'revision': data.revision,
            'soc': data.soc,
            'pcb_revision': data.pcb_revision,
            'memory': data.memory,
            'storage': data.storage,
            'ethernet_speed': data.eth_speed,
            'has_wifi': data.wifi,
            'has_bluetooth': data.bluetooth,
            'usb_ports': data.usb,
            'usb3_ports': data.usb3,
            'board_headers': list(data.headers.keys())
        }
        pinmap = {
            str(pin.number): {
                'label': pin.function,
                # 'function': factory.pin_class(factory, pin.number).function,
                'header_row': pin.row,
                'header_col': pin.col,
                'info_url': self.__class__.pinout(pin.number, pin.function),
                'data': self.__class__.pindata(pin.number, pin.function)
            }
            for pin in self.gpiopins.values()
        }
        self.pinmap = dict(sorted(pinmap.items(), key=lambda x: x[0]))
        self.gpios = [i for i in self.pinmap.values()]
        self.pimap = {'system': self.system, 'gpio': self.gpios}


    @classmethod
    def pinout(cls,pin: int = None, label: str = None):
        base_url = "https://pinout.xyz/pinout/"
        powerpins = {
            'GND': 'ground',
            '3V3': '3v3_power',
            '5V': '5v_power'
        }
        if label.startswith("GPIO"):
            return urljoin(base_url, "pin{}_{}".format(pin, label.lower()))
        if label in powerpins.keys():
            return urljoin(base_url, powerpins[label])

    @classmethod
    def pindata(cls, pin: int = None, label: str = None):
        parser = ""
        powerpins = {
            'GND': 'page_ground',
            '3V3': 'page_3v3_power',
            '5V': 'page_5v_power'
        }
        if label.startswith("GPIO"):
            articleid = "pin{}_{}".format(pin, label.lower())
            parser = "gpiopin"
        if label in powerpins.keys():
            articleid = powerpins[label]
            parser = "power"
        pin_url = cls.pinout(pin, label)
        response = requests.get(pin_url)
        html = BeautifulSoup(response.text, 'html.parser')
        article = html.find('article', class_="{}".format(articleid))
        if parser == "gpiopin":
            #print("CONT: ".format(article.contents))
            pin_map_rgx = r".*pin\s(\d)"
            key_map_rgx = r"(.+) .*pin\s.+"
            phys_key, gpio_key, wiringpi_key = [
                re.search(key_map_rgx, i.string).group(1) for i in article.contents[2].find_all('li')
            ][0:3]
            phys_val, gpio_val, wiringpi_val = [
                re.search(pin_map_rgx, i.string).group(1) for i in article.contents[2].find_all('li')
            ][0:3]
            boardmap = dict(
                list(
                    zip(
                        [
                            phys_key, gpio_key, wiringpi_key
                        ],
                        [
                            phys_val, gpio_val, wiringpi_val
                        ]
                    )
                )
            )
            #print(boardmap)


            funcs = [i.string for i in article.contents[1].find_all('td')]
            if None in funcs:
                funcs.remove(None)
            #print(funcs)
            return {
                "title" : article.contents[0].string,
                "descr": "{}".format(articleid),
                "funcs" : funcs,
                "boardmap": boardmap
            }
        else:
            desc = list(filter(
                lambda x: type(x.string) is not type(None),
                list(article.find_all('p'))
            ))

            return {
                "title": "{}".format(article.contents[0].string),
                "descr": " ".join([i.string.replace("\n", " ") for i in desc]),
                "funcs": "this is a {} pin!!!".format(parser)
            }




#print(pinmap)