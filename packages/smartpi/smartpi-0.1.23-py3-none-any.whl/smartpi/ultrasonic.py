# coding=utf-8
import time
from typing import List, Optional
from smartpi import base_driver
        
#��������ഫ���� port:����P�˿�  �������أ��������; ��ȡ����-1     
def get_value(port:bytes) -> Optional[bytes]:
    ultrasonic_str=[0xA0, 0x06, 0x00, 0xBE]
    ultrasonic_str[0]=0XA0+port
    ultrasonic_str[2]=1 
    response = base_driver.single_operate_sensor(ultrasonic_str,0)
        
    if response == None:
        return None
    else:
        distance_data=response[4:-1]
        distance_num=int.from_bytes(distance_data, byteorder='big', signed=True)
        return distance_num
        