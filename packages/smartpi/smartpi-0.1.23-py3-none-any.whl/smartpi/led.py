# coding=utf-8
import time
from typing import List, Optional
from smartpi import base_driver


#�ʵƿ��� port:����P�˿ڣ�command:0:�صƣ�1:�죻2:�̣�3:����4:�ƣ�5:�ϣ�6:�ࣻ7:�ף�  �������أ�0; ��ȡ����-1  
def set_color(port:bytes,command:bytes) -> Optional[bytes]:
    color_lamp_str=[0xA0, 0x05, 0x00, 0xBE]
    color_lamp_str[0]=0XA0+port
    color_lamp_str[2]=command
    response = base_driver.single_operate_sensor(color_lamp_str,0)
    if response == None:
        return None
    else:
        return 0
        