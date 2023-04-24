import taichi as ti
from vispy import io

@ti.data_oriented
class Obj:
    def __init__(self):
        self.v=[]
        self.vt=[]
        self.vn=[]
        self.f=[]
    def readObj(self,ObjFilePath):    
        self.v,self.f,self.vn,self.vt=io.read_mesh(ObjFilePath)
    #f表示顶点/uv纹理坐标/法向量索引
