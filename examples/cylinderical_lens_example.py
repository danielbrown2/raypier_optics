

from raytrace.lenses import GeneralLens, PlanoConvexLens
from raytrace.faces import CylindericalFace, PlanarFace, SphericalFace
from raytrace.materials import OpticalMaterial
from raytrace.shapes import CircleShape
from raytrace.tracer import RayTraceModel
from raytrace.gausslet_sources import CollimatedGaussletSource
from raytrace.fields import EFieldPlane
from raytrace.probes import GaussletCapturePlane
from raytrace.intensity_image import IntensityImageView
from raytrace.intensity_surface import IntensitySurface

from raytrace.cfaces import ShapedSphericalFace, CircularFace
from raytrace.cshapes import CircleShape as CircleShape_
from raytrace.ctracer import FaceList

shape = CircleShape(radius=7.5)

face1 = PlanarFace(z_height=0.0)
face2 = CylindericalFace(z_height=4.0, curvature=100.0)
face2 = SphericalFace(z_height=4.0, curvature=50.0)

mat = OpticalMaterial(refractive_index=1.5)

lens = GeneralLens(name = "Cylinderincal Lens",
                     centre = (0,0,0),
                     direction=(0,0,1),
                     shape=shape, 
                     surfaces=[face2, 
                               face1], 
                     materials=[mat])

lens2 = PlanoConvexLens(centre=(0,0,0),
                        diameter=15.0,
                       CT=4.0,
                       n_inside=1.5,
                       curvature=50.0
                       )

class TestLens(PlanoConvexLens):
    def _faces_default(self):
        fl = FaceList(owner=self)
        fl.faces = [CircularFace(owner=self, diameter=self.diameter,
                                material = self.material), 
                    ShapedSphericalFace(owner=self,
                                        material=self.material,
                                        shape=CircleShape_(radius=self.diameter/2),
                                        z_height=self.CT,
                                        curvature=self.curvature)
                ]
        return fl
    
    def _CT_changed(self, new_ct):
        self.faces.faces[1].z_height = new_ct
        
    def _curvature_changed(self, new_curve):
        self.faces.faces[1].curvature = new_curve
        
lens3 = TestLens(centre=(0,0,0),
                        diameter=15.0,
                       CT=4.0,
                       n_inside=1.5,
                       curvature=50.0
                       )
        

src = CollimatedGaussletSource(origin=(0.001,0,-5.0),
                               direction=(0,0,1),
                               wavelength=1.0,
                               radius=1.0,
                               beam_waist=10.0,
                               resolution=10,
                               max_ray_len=200.0,
                               display='wires',
                               opacity=0.2
                               )

###Add some sensors
capture = GaussletCapturePlane(centre=(0,0,25), 
                               direction=(0,0,1),
                               width=5.0,
                               height=5.0)

field = EFieldPlane(centre=(0,0,25),
                    direction=(0,0,1),
                    detector=capture,
                    align_detector=True,
                    size=100,
                    width=0.2,
                    height=0.2)

image = IntensityImageView(field_probe=field)
surf = IntensitySurface(field_probe=field)


model = RayTraceModel(optics=[lens], 
                      sources=[src], 
                      probes=[capture,field],
                      results=[image,surf])
model.configure_traits()
