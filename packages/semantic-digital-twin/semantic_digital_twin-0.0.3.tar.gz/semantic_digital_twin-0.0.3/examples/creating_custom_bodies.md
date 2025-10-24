---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---
(creating-custom-bodies)=
# Creating Custom Bodies

The tutorial demonstrates the creation of a body and its visual and collision information
In our kinematic structure, each entity needs to have a unique name. For this we can use a simple datastructure called `PrefixedName`. You always need to provide a name, but the prefix is optional.

```{code-cell} ipython2
from semantic_digital_twin.datastructures.prefixed_name import PrefixedName
from semantic_digital_twin.spatial_types.spatial_types import TransformationMatrix, RotationMatrix
from semantic_digital_twin.utils import get_semantic_digital_twin_directory_root
from semantic_digital_twin.world import World
from semantic_digital_twin.world_description.world_entity import Body

world = World()
body = Body(name=PrefixedName("my first body", "my first prefix"))
```

Next, let's create the visual and collision information for our body.

The collision describes the geometry to use when calculating collision relevant things, for instance if your robot is colliding with a table while moving.
The visual information is purely for esthetics.
Both of these are collections of shapes.

Supported Shapes are:
- Box
- Sphere
- Cylinder
- FileMesh/TriangleMesh

```{code-cell} ipython2
import os
from semantic_digital_twin.spatial_types import Point3, Vector3
from semantic_digital_twin.world_description.shape_collection import ShapeCollection
from semantic_digital_twin.world_description.geometry import Box, Scale, Sphere, Cylinder, FileMesh, Color

box_origin = TransformationMatrix.from_xyz_rpy(x=0, y=0, z=0, roll=0, pitch=0, yaw=0, reference_frame=body)
box = Box(origin=box_origin, scale=Scale(1., 1., 0.5), color=Color(1., 0., 0., 1., ))

sphere_origin = TransformationMatrix.from_xyz_quaternion(pos_x=0, pos_y=1., pos_z=1., quat_x=0., quat_y=0., quat_z=0.,
                                                   quat_w=1., reference_frame=body)
sphere = Sphere(origin=sphere_origin, radius=0.4)

cylinder_origin = TransformationMatrix.from_point_rotation_matrix(point=Point3.from_iterable([1, -1, 2]),
                                                                  rotation_matrix=RotationMatrix.from_axis_angle(
                                                                      Vector3.from_iterable([1., 0., 0.]), 0.8, ),
                                                                  reference_frame=body)
cylinder = Cylinder(origin=cylinder_origin, width=0.05, height=0.5)

mesh = FileMesh(origin=TransformationMatrix.from_xyz_rpy(reference_frame=body),
            filename=os.path.join(get_semantic_digital_twin_directory_root(os.getcwd()), "resources", "stl", "milk.stl"))

body.collision = ShapeCollection([cylinder, sphere, box], body)
body.visual = ShapeCollection([mesh], body)
```

When modifying your world, keep in mind that you need to open a `world.modify_world()` whenever you want to add or remove things to/from your world

```{code-cell} ipython2
with world.modify_world():
    world.add_body(body)

from semantic_digital_twin.spatial_computations.raytracer import RayTracer
rt = RayTracer(world)
rt.update_scene()
rt.scene.show("jupyter")
```

If you want to see your generated world, check out the [](visualizing-worlds) tutorial.
```{warning}
If you are trying to create multiple bodies without connecting them,
you will run into trouble with the world validation.
If you want to see how to create multiple bodies, 
check out the [](world-structure-manipulation) tutorial.
```