import taichi as ti

PI = 3.14159265

@ti.func
def cal_triangle_area(a,b,c):
    ab=b-a
    ac=c-a
    tmp=ab.cross(ac)
    return ti.sqrt(pow(tmp[0],2)+pow(tmp[1],2)+pow(tmp[2],2))*0.5
@ti.func
def cal_rectangle_area(a,b,c,d):
    ac=c-a
    bd=d-b
    tmp=ac.cross(bd)
    return ti.sqrt(pow(tmp[0],2)+pow(tmp[1],2)+pow(tmp[2],2))*0.5

@ti.func
def rand3():
    return ti.Vector([ti.random(), ti.random(), ti.random()])

@ti.func
def random_in_unit_sphere():
    p = 2.0 * rand3() - ti.Vector([1, 1, 1])
    while p.norm() >= 1.0:
        p = 2.0 * rand3() - ti.Vector([1, 1, 1])
    return p

@ti.func
def random_unit_vector():
    return random_in_unit_sphere().normalized()

@ti.func
def to_light_source(hit_point, light_source):
    return light_source - hit_point

@ti.func
def reflect(v, normal):
    return v - 2 * v.dot(normal) * normal

@ti.func
def refract(uv, n, etai_over_etat):
    cos_theta = min(n.dot(-uv), 1.0)
    r_out_perp = etai_over_etat * (uv + cos_theta * n)
    r_out_parallel = -ti.sqrt(abs(1.0 - r_out_perp.dot(r_out_perp))) * n
    return r_out_perp + r_out_parallel

@ti.func
def reflectance(cosine, ref_idx):
    # Use Schlick's approximation for reflectance.
    r0 = (1 - ref_idx) / (1 + ref_idx)
    r0 = r0 * r0
    return r0 + (1 - r0) * pow((1 - cosine), 5)

@ti.data_oriented
class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction
    def at(self, t):
        return self.origin + t * self.direction
@ti.data_oriented
class Point:
    def __init__(self,pos):
        self.pos=pos
    def __init__(self,pos,normal):
        self.pos=pos
        self.normal=normal
@ti.data_oriented
class Sphere:
    def __init__(self, center, radius, material, color):
        self.center = center
        self.radius = radius
        self.material = material
        self.color = color

    @ti.func
    def hit(self, ray, t_min=0.001, t_max=10e8):
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c
        is_hit = False
        front_face = False
        root = 0.0  #root=t
        hit_point =  ti.Vector([0.0, 0.0, 0.0])
        hit_point_normal = ti.Vector([0.0, 0.0, 0.0])
        if discriminant > 0:
            sqrtd = ti.sqrt(discriminant)
            root = (-b - sqrtd) / (2 * a)
            if root < t_min or root > t_max:
                root = (-b + sqrtd) / (2 * a)
                if root >= t_min and root <= t_max:
                    is_hit = True
            else:
                is_hit = True
        if is_hit:
            hit_point = ray.at(root)
            hit_point_normal = (hit_point - self.center) / self.radius
            # Check which side does the ray hit, we set the hit point normals always point outward from the surface
            if ray.direction.dot(hit_point_normal) < 0:
                front_face = True
            else:
                hit_point_normal = -hit_point_normal
        return is_hit, root, hit_point, hit_point_normal, front_face, self.material, self.color

@ti.data_oriented
class Model:
    def __init__(self,v,vt,vn,f,color=ti.Vector([0.6,0.6,0.6]),material=1,max_vertex_num=1024,max_face_num=1024):
         self.vertex_num=ti.field(dtype=ti.i32,)
         self.vt=vt
         self.vn=vn
         self.f=f
         self.color=color
         self.material=material
    
        

@ti.data_oriented
class Triangle:
    def __init__(self,a,b,c,material,color):
        self.material=material
        self.color=color
        self.a=a
        self.b=b
        self.c=c
        self.center=(a+b+c)/3
    @ti.func
    def hit(self,ray,t_min=0.001,t_max=10e8):
        oc=ray.origin-self.center
        is_hit=False
        root=0.0
        hit_point=ti.Vector([1.0,0.0,0.0])
        hit_point_normal = ti.Vector([0.0, 0.0, 0.0])
        front_face = False
        normal=ti.math.cross(self.b-self.a,self.c-self.a).normalized()
        discriminat=ray.direction.dot(normal)
        if discriminat!=0:
            root=-(normal[0]*oc[0]+normal[1]*oc[1]+normal[2]*oc[2])/(normal[0]*ray.direction[0]+normal[1]*ray.direction[1]+normal[2]*ray.direction[2])
            hit_point=ray.at(root)
            if cal_triangle_area(self.a,self.b,hit_point)+cal_triangle_area(self.b,self.c,hit_point)+cal_triangle_area(self.a,self.c,hit_point)==cal_triangle_area(self.a,self.b,self.c):
                if root>=t_min and root<= t_max:
                    is_hit=True
        if is_hit:
            hit_point_normal=normal
            if ray.direction.dot(hit_point_normal)<0:
                front_face=True
            else:
                hit_point_normal = -hit_point_normal
        return is_hit,root,hit_point,hit_point_normal,front_face,self.material,self.color


        


@ti.data_oriented
class Hittable_list:
    def __init__(self):
        self.objects = []
    def add(self, obj):
        self.objects.append(obj)
    def clear(self):
        self.objects = []

    @ti.func
    def hit(self, ray, t_min=0.001, t_max=10e8):
        closest_t = t_max
        is_hit = False
        front_face = False
        hit_point = ti.Vector([0.0, 0.0, 0.0])  #交点
        hit_point_normal = ti.Vector([0.0, 0.0, 0.0])   #交点法线方向
        color = ti.Vector([0.0, 0.0, 0.0])
        material = 1
        for index in ti.static(range(len(self.objects))):
            is_hit_tmp, root_tmp, hit_point_tmp, hit_point_normal_tmp, front_face_tmp, material_tmp, color_tmp =  self.objects[index].hit(ray, t_min, closest_t)
            if is_hit_tmp and closest_t>root_tmp:
                    closest_t = root_tmp
                    is_hit = is_hit_tmp
                    hit_point = hit_point_tmp
                    hit_point_normal = hit_point_normal_tmp
                    front_face = front_face_tmp
                    material = material_tmp
                    color = color_tmp
        return is_hit, hit_point, hit_point_normal, front_face, material, color

    @ti.func
    def hit_shadow(self, ray, t_min=0.001, t_max=10e8):
        is_hit_source = False
        is_hit_source_temp = False
        hitted_dielectric_num = 0
        is_hitted_non_dielectric = False
        # Compute the t_max to light source
        is_hit_tmp, root_light_source, hit_point_tmp, hit_point_normal_tmp, front_face_tmp, material_tmp, color_tmp = \
        self.objects[0].hit(ray, t_min)
        for index in ti.static(range(len(self.objects))):
            is_hit_tmp, root_tmp, hit_point_tmp, hit_point_normal_tmp, front_face_tmp, material_tmp, color_tmp =  self.objects[index].hit(ray, t_min, root_light_source)
            if is_hit_tmp:
                if material_tmp != 3 and material_tmp != 0:
                    is_hitted_non_dielectric = True
                if material_tmp == 3:
                    hitted_dielectric_num += 1
                if material_tmp == 0:
                    is_hit_source_temp = True
        if is_hit_source_temp and (not is_hitted_non_dielectric) and hitted_dielectric_num == 0:
            is_hit_source = True
        return is_hit_source, hitted_dielectric_num, is_hitted_non_dielectric


@ti.data_oriented
class Camera:
    def __init__(self, fov=60, aspect_ratio=1.0):
        # Camera parameters
        self.lookfrom = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.lookat = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.vup = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.fov = fov
        self.aspect_ratio = aspect_ratio

        self.cam_lower_left_corner = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.cam_horizontal = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.cam_vertical = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.cam_origin = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.reset()

    @ti.kernel
    def reset(self):
        self.lookfrom[None] = [0.0, 1.0, -5.0]
        self.lookat[None] = [0.0, 1.0, -1.0]
        self.vup[None] = [0.0, 1.0, 0.0]
        theta = self.fov * (PI / 180.0)
        half_height = ti.tan(theta / 2.0)
        half_width = self.aspect_ratio * half_height
        self.cam_origin[None] = self.lookfrom[None]
        w = (self.lookfrom[None] - self.lookat[None]).normalized()
        u = (self.vup[None].cross(w)).normalized()
        v = w.cross(u)
        self.cam_lower_left_corner[None] = ti.Vector([-half_width, -half_height, -1.0])
        self.cam_lower_left_corner[
            None] = self.cam_origin[None] - half_width * u - half_height * v - w
        self.cam_horizontal[None] = 2 * half_width * u
        self.cam_vertical[None] = 2 * half_height * v

    @ti.func
    def get_ray(self, u, v):
        return Ray(self.cam_origin[None], self.cam_lower_left_corner[None] + u * self.cam_horizontal[None] + v * self.cam_vertical[None] - self.cam_origin[None])