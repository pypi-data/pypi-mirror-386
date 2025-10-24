import socket
import json
import time

class _gui_client:
    def __init__(self, host="127.0.0.1", port=65167):
        self.sock = socket.create_connection((host, port))
        self.clear()

    def _send(self, cmd):
        self.sock.sendall((json.dumps(cmd) + "\n").encode())
        time.sleep(0.1)

    def show_text(self, x, y, text, color="black", size=16):
        self._send({"type": "text", "x": x, "y": y, "text": text, "color": color, "size": size})

    def print(self, text):
        self._send({"type": "print", "text": text})

    def println(self, text):
        self._send({"type": "println", "text": text})

    def show_image(self, x, y, path, width, height):
        self._send({"type": "image", "x": x, "y": y, "path": path, "width": width, "height": height})

    def draw_line(self, x1, y1, x2, y2, color="black", width=1):
        self._send({"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color, "width": width})

    def fill_rect(self, x, y, w, h, color="black"):
        self._send({"type": "fill_rect", "x": x, "y": y, "w": w, "h": h, "color": color})
        
    def draw_rect(self, x, y, w, h, width, color="black"):
        self._send({"type": "draw_rect", "x": x, "y": y, "w": w, "h": h, "width": width, "color": color})

    def fill_circle(self, cx, cy, r, color="black"):
        self._send({"type": "fill_circle", "cx": cx, "cy": cy, "r": r, "color": color})

    def draw_circle(self, cx, cy, r, width, color="black"):
        self._send({"type": "draw_circle", "cx": cx, "cy": cy, "r": r, "width": width, "color": color})
    
    def clear(self):
        self._send({"type": "clear"})

    def finish(self):
        self.sock.close()

# 创建全局实例
_client_instance = _gui_client()

# 将类方法提升为模块级别的函数
def show_text(x, y, text, color="black", size=16):
    _client_instance.show_text(x, y, text, color, size)

def print(text):
    _client_instance.print(text)

def println(text):
    _client_instance.println(text)

def show_image(x, y, path, width, height):
    _client_instance.show_image(x, y, path, width, height)

def draw_line(x1, y1, x2, y2, color="black", width=1):
    _client_instance.draw_line(x1, y1, x2, y2, color, width)

def fill_rect(x, y, w, h, color="black"):
    _client_instance.fill_rect(x, y, w, h, color)
    
def draw_rect(x, y, w, h, width, color="black"):
    _client_instance.draw_rect(x, y, w, h, width, color)

def fill_circle(cx, cy, r, color="black"):
    _client_instance.fill_circle(cx, cy, r, color)

def draw_circle(cx, cy, r, width, color="black"):
    _client_instance.draw_circle(cx, cy, r, width, color)

def clear():
    _client_instance.clear()

def finish():
    _client_instance.finish()

# 可选：如果希望仍然可以使用类创建新实例
def create_client(host="127.0.0.1", port=65167):
    return _gui_client(host, port)
    