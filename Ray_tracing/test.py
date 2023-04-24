import taichi as ti
import numpy as np
from read_obj import Obj
obj=Obj()
obj.readObj(ObjFilePath="/home/syy/taichi_ray_tracing/Cube.obj")
print(obj.v,len(obj.v))
