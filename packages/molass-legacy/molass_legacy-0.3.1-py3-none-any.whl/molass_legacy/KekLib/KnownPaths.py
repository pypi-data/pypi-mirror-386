# coding: utf-8
"""
    KnownPaths.py

    excerpts from https://gist.github.com/mkropat/7550097
"""

import ctypes, sys
from ctypes import windll, wintypes
from uuid import UUID

class GUID(ctypes.Structure):   # [1]
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ] 

    def __init__(self, uuid_):
        ctypes.Structure.__init__(self)
        self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1], rest = uuid_.fields
        for i in range(2, 8):
            self.Data4[i] = rest>>(8 - i - 1)*8 & 0xff

class UserHandle:   # [3]
    current = wintypes.HANDLE(0)
    common  = wintypes.HANDLE(-1)

_CoTaskMemFree = windll.ole32.CoTaskMemFree     # [4]
_CoTaskMemFree.restype= None
_CoTaskMemFree.argtypes = [ctypes.c_void_p]

_SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath     # [5] [3]
_SHGetKnownFolderPath.argtypes = [
    ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
] 

class PathNotFoundException(Exception): pass

def get_path(folderid, user_handle=UserHandle.common):
    fid = GUID(folderid) 
    pPath = ctypes.c_wchar_p()
    S_OK = 0
    if _SHGetKnownFolderPath(ctypes.byref(fid), 0, user_handle, ctypes.byref(pPath)) != S_OK:
        raise PathNotFoundException()
    path = pPath.value
    _CoTaskMemFree(pPath)
    return path

def get_downloads_folder():
    Downloads = UUID('{374DE290-123F-4565-9164-39C4925E467B}')
    return str(get_path(Downloads))
