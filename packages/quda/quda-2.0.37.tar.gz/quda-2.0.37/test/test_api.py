# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/10/24 14:13
# Description:

from quda.data import api

if __name__ == '__main__':
    data = api.get_secumain()
    print(data)