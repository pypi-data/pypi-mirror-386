import logging

from entity_query_language import entity, let, in_, infer, rule_mode
from numpy.ma.testutils import (
    assert_equal,
)  # You could replace this with numpy's regular assert for better compatibility

from semantic_digital_twin.reasoning.world_reasoner import WorldReasoner
from semantic_digital_twin.testing import *
from semantic_digital_twin.semantic_annotations.semantic_annotations import *

try:
    from ripple_down_rules.user_interface.gui import RDRCaseViewer
    from PyQt6.QtWidgets import QApplication
except ImportError as e:
    logging.debug(e)
    QApplication = None
    RDRCaseViewer = None

try:
    from semantic_digital_twin.reasoning.world_rdr import world_rdr
except ImportError:
    world_rdr = None


@dataclass(eq=False)
class TestSemanticAnnotation(SemanticAnnotation):
    """
    A Generic semantic annotation for multiple bodies.
    """

    _private_entity: KinematicStructureEntity = field(default=None)
    entity_list: List[KinematicStructureEntity] = field(
        default_factory=list, hash=False
    )
    semantic_annotations: List[SemanticAnnotation] = field(
        default_factory=list, hash=False
    )
    root_entity_1: KinematicStructureEntity = field(default=None)
    root_entity_2: KinematicStructureEntity = field(default=None)
    tip_entity_1: KinematicStructureEntity = field(default=None)
    tip_entity_2: KinematicStructureEntity = field(default=None)

    def add_entity(self, body: KinematicStructureEntity):
        self.entity_list.append(body)
        body._semantic_annotations.add(self)

    def add_semantic_annotation(self, semantic_annotation: SemanticAnnotation):
        self.semantic_annotations.append(semantic_annotation)
        semantic_annotation._semantic_annotations.add(self)

    @property
    def chain(self) -> list[KinematicStructureEntity]:
        """
        Returns itself as a kinematic chain.
        """
        return self._world.compute_chain_of_kinematic_structure_entities(
            self.root_entity_1, self.tip_entity_1
        )

    @property
    def _private_chain(self) -> list[KinematicStructureEntity]:
        """
        Private chain computation.
        """
        return self._world.compute_chain_of_kinematic_structure_entities(
            self.root_entity_2, self.tip_entity_2
        )


def test_semantic_annotation_hash(apartment_world):
    semantic_annotation1 = Handle(body=apartment_world.bodies[0])
    apartment_world.add_semantic_annotation(semantic_annotation1)
    assert hash(semantic_annotation1) == hash((Handle, apartment_world.bodies[0].name))

    semantic_annotation2 = Handle(body=apartment_world.bodies[0])
    assert semantic_annotation1 == semantic_annotation2


def test_aggregate_bodies(kitchen_world):
    world_semantic_annotation = TestSemanticAnnotation(_world=kitchen_world)

    # Test bodies added to a private dataclass field are not aggregated
    world_semantic_annotation._private_entity = (
        kitchen_world.kinematic_structure_entities[0]
    )

    # Test aggregation of bodies added in custom properties
    world_semantic_annotation.root_entity_1 = (
        kitchen_world.kinematic_structure_entities[1]
    )
    world_semantic_annotation.tip_entity_1 = kitchen_world.kinematic_structure_entities[
        4
    ]

    # Test aggregation of normal dataclass field
    body_subset = kitchen_world.kinematic_structure_entities[5:10]
    [world_semantic_annotation.add_entity(body) for body in body_subset]

    # Test aggregation of bodies in a new as well as a nested semantic annotation
    semantic_annotation1 = TestSemanticAnnotation()
    semantic_annotation1_subset = kitchen_world.kinematic_structure_entities[10:18]
    [semantic_annotation1.add_entity(body) for body in semantic_annotation1_subset]

    semantic_annotation2 = TestSemanticAnnotation()
    semantic_annotation2_subset = kitchen_world.kinematic_structure_entities[20:]
    [semantic_annotation2.add_entity(body) for body in semantic_annotation2_subset]

    semantic_annotation1.add_semantic_annotation(semantic_annotation2)
    world_semantic_annotation.add_semantic_annotation(semantic_annotation1)

    # Test that bodies added in a custom private property are not aggregated
    world_semantic_annotation.root_entity_2 = (
        kitchen_world.kinematic_structure_entities[18]
    )
    world_semantic_annotation.tip_entity_2 = kitchen_world.kinematic_structure_entities[
        20
    ]

    assert_equal(
        world_semantic_annotation.kinematic_structure_entities,
        set(kitchen_world.kinematic_structure_entities)
        - {
            kitchen_world.kinematic_structure_entities[0],
            kitchen_world.kinematic_structure_entities[19],
        },
    )


def test_handle_semantic_annotation_eql(apartment_world):
    with rule_mode():
        body = let(
            type_=Body,
        )
        query = infer(entity(Handle(body=body), in_("handle", body.name.name.lower())))

    handles = list(query.evaluate())
    assert len(handles) > 0


@pytest.mark.parametrize(
    "semantic_annotation_type, update_existing_semantic_annotations, scenario",
    [
        (Handle, False, None),
        (Container, False, None),
        (Drawer, False, None),
        (Cabinet, False, None),
        (Door, False, None),
    ],
)
def test_infer_apartment_semantic_annotation(
    semantic_annotation_type,
    update_existing_semantic_annotations,
    scenario,
    apartment_world,
):
    fit_rules_and_assert_semantic_annotations(
        apartment_world,
        semantic_annotation_type,
        update_existing_semantic_annotations,
        scenario,
    )


@pytest.mark.skipif(world_rdr is None, reason="requires world_rdr")
def test_generated_semantic_annotations(kitchen_world):
    found_semantic_annotations = world_rdr.classify(kitchen_world)[
        "semantic_annotations"
    ]
    drawer_container_names = [
        v.body.name.name for v in found_semantic_annotations if isinstance(v, Container)
    ]
    assert len(drawer_container_names) == 14


@pytest.mark.order("second_to_last")
def test_apartment_semantic_annotations(apartment_world):
    world_reasoner = WorldReasoner(apartment_world)
    world_reasoner.fit_semantic_annotations(
        [Handle, Container, Drawer, Cabinet],
        world_factory=lambda: apartment_world,
        scenario=None,
    )

    found_semantic_annotations = world_reasoner.infer_semantic_annotations()
    drawer_container_names = [
        v.body.name.name for v in found_semantic_annotations if isinstance(v, Container)
    ]
    assert len(drawer_container_names) == 19


def fit_rules_and_assert_semantic_annotations(
    world, semantic_annotation_type, update_existing_semantic_annotations, scenario
):
    world_reasoner = WorldReasoner(world)
    world_reasoner.fit_semantic_annotations(
        [semantic_annotation_type],
        update_existing_semantic_annotations=update_existing_semantic_annotations,
        world_factory=lambda: world,
        scenario=scenario,
    )

    found_semantic_annotations = world_reasoner.infer_semantic_annotations()
    assert any(
        isinstance(v, semantic_annotation_type) for v in found_semantic_annotations
    )


def test_semantic_annotation_serde_once(apartment_world):
    handle_body = apartment_world.bodies[0]
    door_body = apartment_world.bodies[1]

    handle = Handle(body=handle_body)
    door = Door(body=door_body, handle=handle)

    apartment_world.add_semantic_annotation(handle)
    apartment_world.add_semantic_annotation(door)

    door_se = door.to_json()
    door_de = Door.from_json(door_se)

    assert door == door_de
    assert type(door.handle) == type(door_de.handle)
    assert type(door.body) == type(door_de.body)


def test_semantic_annotation_serde_multiple(apartment_world):
    handle_body = apartment_world.bodies[0]
    door_body = apartment_world.bodies[1]

    handle = Handle(body=handle_body)
    door = Door(body=door_body, handle=handle)

    apartment_world.add_semantic_annotation(handle)
    apartment_world.add_semantic_annotation(door)

    door_se1 = door.to_json()
    door_de1 = Door.from_json(door_se1)

    assert door == door_de1
    assert type(door.handle) == type(door_de1.handle)
    assert type(door.body) == type(door_de1.body)

    door_se2 = door_de1.to_json()
    door_de2 = Door.from_json(door_se2)

    assert door == door_de2
    assert type(door.handle) == type(door_de2.handle)
    assert type(door.body) == type(door_de2.body)
