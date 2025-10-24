# coding=utf-8
import time
from typing import List, Optional
from smartpi import base_driver

#��ɫ��ȡ  ��������ֵ��1-��ɫ��2-��ɫ��3-��ɫ��4-��ɫ��5-��ɫ��6-��ɫ��  ��ȡ����-1  
def get_value(port:bytes) -> Optional[bytes]:
    color_str=[0xA0, 0x04, 0x00, 0xBE]
    color_str[0]=0XA0+port
    color_str[2]=1
    response = base_driver.single_operate_sensor(color_str,0)        
    if response == None:
        return None
    else:
        return response[4]
        
        