# coding=utf-8
import time
from typing import List, Optional
from smartpi import base_driver

#����ֵ��ȡ port:����P�˿ڣ�  �������أ���ֵ����; ��ȡ����-1  
def get_value(port:bytes) -> Optional[bytes]:
    light_str=[0xA0, 0x02, 0x00, 0xBE]
    light_str[0]=0XA0+port
    light_str[2]=0x01
    response = base_driver.single_operate_sensor(light_str,0)       
    if response == None:
        return None
    else:
        light_data=response[4:-1]
        light_num=int.from_bytes(light_data, byteorder='big', signed=True)
        return light_num
        
#�����ֵ���� port:����P�˿ڣ� threshold�����õ���ֵ0~4000
def set_threshold(port:bytes,threshold:int) -> Optional[bytes]:
    light_str=[0xA0, 0x02, 0x00, 0x81, 0x00, 0x00, 0xBE]
    light_str[0]=0XA0+port
    light_str[2]=0x04
    light_str[4]=threshold//256
    light_str[5]=threshold%256
    response = base_driver.single_operate_sensor(light_str,0)       
    if response == None:
        return None
    else:
        return 0
        
#�����ֵ��ȡ port:����P�˿ڣ�  
def get_threshold(port:bytes) -> Optional[bytes]:
    light_str=[0xA0, 0x02, 0x00, 0xBE]
    light_str[0]=0XA0+port
    light_str[2]=0x05
    response = base_driver.single_operate_sensor(light_str,0)       
    if response == None:
        return None
    else:
        light_data=response[4:-1]
        light_num=int.from_bytes(light_data, byteorder='big', signed=True)
        return light_num
        
#����ȡ��ǰֵ���趨��ֵ�ȽϺ��boolֵ port:����P�˿ڣ�  
def get_bool_data(port:bytes) -> Optional[bytes]:
    light_str=[0xA0, 0x02, 0x00, 0xBE]
    light_str[0]=0XA0+port
    light_str[2]=0x06
    response = base_driver.single_operate_sensor(light_str,0)       
    if response == None:
        return None
    else:
        return response[4]
        