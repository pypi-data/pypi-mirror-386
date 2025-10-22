import json
from collections import Counter

import pytest

from dagshub_annotation_converter.formats.label_studio.keypointlabels import KeyPointLabelsAnnotation
from dagshub_annotation_converter.formats.label_studio.rectanglelabels import RectangleLabelsAnnotation
from dagshub_annotation_converter.formats.label_studio.task import parse_ls_task, LabelStudioTask
from dagshub_annotation_converter.ir.image import (
    IRPoseImageAnnotation,
    CoordinateStyle,
    IRBBoxImageAnnotation,
    IRPosePoint,
)
from tests.label_studio.common import generate_annotation, generate_task


@pytest.fixture
def keypoint_annotation() -> dict:
    annotation = {
        "x": 50,
        "y": 50,
        "keypointlabels": ["cat"],
    }
    return generate_annotation(annotation, "keypointlabels", "deadbeef")


@pytest.fixture
def keypoint_task(keypoint_annotation) -> str:
    return generate_task([keypoint_annotation])


@pytest.fixture
def parsed_keypoint_task(keypoint_task) -> LabelStudioTask:
    return parse_ls_task(keypoint_task)


def test_keypoint_parsing(parsed_keypoint_task):
    actual = parsed_keypoint_task
    assert len(actual.annotations) == 1
    assert len(actual.annotations[0].result) == 1

    ann = actual.annotations[0].result[0]
    assert isinstance(ann, KeyPointLabelsAnnotation)
    assert ann.value.x == 50
    assert ann.value.y == 50


def test_keypoint_ir(parsed_keypoint_task):
    actual = parsed_keypoint_task.annotations[0].result[0].to_ir_annotation()

    assert len(actual) == 1
    ann = actual[0]
    assert isinstance(ann, IRPoseImageAnnotation)

    assert len(ann.points) == 1
    assert ann.points[0].x == 0.5
    assert ann.points[0].y == 0.5

    assert ann.coordinate_style == CoordinateStyle.NORMALIZED


def test_pose_consolidation():
    # Very long LS task that has: 3 keypoint + 1 bounding box for 1 pose, another 3+1 for another pose + 1 random bbox
    ls_task = {
        "annotations": [
            {
                "completed_by": 1,
                "result": [
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat1",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 50,
                            "y": 50,
                            "keypointlabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat2",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 100,
                            "y": 50,
                            "keypointlabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat3",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 50,
                            "y": 100,
                            "keypointlabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "rectanglelabels",
                        "id": "catbox",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 25,
                            "y": 25,
                            "width": 50,
                            "height": 50,
                            "rectanglelabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "dog1",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 75,
                            "y": 75,
                            "keypointlabels": ["dog"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "dog2",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 150,
                            "y": 75,
                            "keypointlabels": ["dog"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "dog3",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 75,
                            "y": 150,
                            "keypointlabels": ["dog"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "rectanglelabels",
                        "id": "dogbox",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 75,
                            "y": 75,
                            "width": 50,
                            "height": 50,
                            "rectanglelabels": ["dog"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "rectanglelabels",
                        "id": "randombox",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 100,
                            "y": 100,
                            "width": 20,
                            "height": 20,
                            "rectanglelabels": ["dog"],
                        },
                    },
                ],
                "ground_truth": True,
            }
        ],
        "meta": {},
        "data": {
            "image": "/path/to/image.jpg",
            "pose_boxes": [
                "catbox",
                "dogbox",
            ],
            "pose_points": [["cat1", "cat2", "cat3"], ["dog1", "dog2", "dog3"]],
        },
        "project": 0,
        "created_at": "2021-10-01T00:00:00Z",
        "updated_at": "2021-10-01T00:00:00Z",
        "id": 1,
    }

    parsed_task = parse_ls_task(json.dumps(ls_task))
    annotations = parsed_task.to_ir_annotations()

    annotation_types = [type(ann) for ann in annotations]
    # The order is different because the new poses are appended to the end
    expected_types = [IRBBoxImageAnnotation, IRPoseImageAnnotation, IRPoseImageAnnotation]

    assert annotation_types == expected_types

    assert annotations[0].categories == {"dog": 1.0}
    assert annotations[1].categories == {"cat": 1.0}
    assert len(annotations[1].points) == 3
    assert annotations[2].categories == {"dog": 1.0}
    assert len(annotations[2].points) == 3


def test_ir_pose_addition():
    task = LabelStudioTask()

    task.add_ir_annotation(
        IRPoseImageAnnotation(
            image_height=200,
            image_width=200,
            categories={"cat": 1.0},
            coordinate_style=CoordinateStyle.NORMALIZED,
            left=0.25,
            top=0.25,
            width=0.3,
            height=0.4,
            points=[
                IRPosePoint(x=0.5, y=0.5),
                IRPosePoint(x=1.0, y=0.5),
                IRPosePoint(x=0.5, y=1.0),
            ],
        )
    )

    assert len(task.annotations[0].result) == 4

    # test bbox
    bbox = task.annotations[0].result[0]
    assert bbox.value.x == 25
    assert bbox.value.y == 25
    assert bbox.value.width == 30
    assert bbox.value.height == 40

    # test keypoints
    kp1 = task.annotations[0].result[1]
    assert (kp1.value.x, kp1.value.y) == (50, 50)
    kp2 = task.annotations[0].result[2]
    assert (kp2.value.x, kp2.value.y) == (100, 50)
    kp3 = task.annotations[0].result[3]
    assert (kp3.value.x, kp3.value.y) == (50, 100)


def test_single_keypoint_to_ir():
    ls_task = {
        "annotations": [
            {
                "completed_by": 1,
                "result": [
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat1",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 50,
                            "y": 50,
                            "keypointlabels": ["cat"],
                        },
                    },
                ],
                "ground_truth": True,
            }
        ],
        "meta": {},
        "data": {
            "image": "/path/to/image.jpg",
        },
        "project": 0,
        "created_at": "2021-10-01T00:00:00Z",
        "updated_at": "2021-10-01T00:00:00Z",
        "id": 1,
    }

    parsed_task = parse_ls_task(json.dumps(ls_task))
    annotations = parsed_task.to_ir_annotations()

    assert len(annotations) == 1

    assert annotations[0].categories == {"cat": 1.0}
    assert len(annotations[0].points) == 1


def test_add_single_keypoint():
    task = LabelStudioTask()

    task.add_ir_annotation(
        IRPoseImageAnnotation.from_points(
            image_height=200,
            image_width=200,
            categories={"cat": 1.0},
            coordinate_style=CoordinateStyle.NORMALIZED,
            points=[IRPosePoint(x=0.5, y=0.5)],
        )
    )

    assert len(task.annotations[0].result) == 1

    kp = task.annotations[0].result[0]
    assert kp.value.x == 50
    assert kp.value.y == 50
    assert kp.value.keypointlabels == ["cat"]


def test_round_trip_with_pose_and_single_keypoint():
    # Task contains: Pose with 3 keypoints and a bounding box, and a single keypoint
    ls_task = {
        "annotations": [
            {
                "completed_by": 1,
                "result": [
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat1",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 50,
                            "y": 50,
                            "keypointlabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat2",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 100,
                            "y": 50,
                            "keypointlabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "cat3",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 50,
                            "y": 100,
                            "keypointlabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "rectanglelabels",
                        "id": "catbox",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 25,
                            "y": 25,
                            "width": 50,
                            "height": 50,
                            "rectanglelabels": ["cat"],
                        },
                    },
                    {
                        "original_width": 200,
                        "original_height": 200,
                        "image_rotation": 0.0,
                        "type": "keypointlabels",
                        "id": "dog1",
                        "origin": "manual",
                        "to_name": "image",
                        "from_name": "label",
                        "value": {
                            "x": 75,
                            "y": 75,
                            "keypointlabels": ["dog"],
                        },
                    },
                ],
                "ground_truth": True,
            }
        ],
        "meta": {},
        "data": {
            "image": "/path/to/image.jpg",
            "pose_boxes": [
                "catbox",
            ],
            "pose_points": [["cat1", "cat2", "cat3"]],
        },
        "project": 0,
        "created_at": "2021-10-01T00:00:00Z",
        "updated_at": "2021-10-01T00:00:00Z",
        "id": 1,
    }

    parsed_task = parse_ls_task(json.dumps(ls_task))
    annotations = parsed_task.to_ir_annotations()

    # Assertions for IR annotations
    # 2 annotations: 1 pose + 1 keypoint
    annotation_types = [type(ann) for ann in annotations]
    # The order is different because the new poses are appended to the end
    expected_types = [IRPoseImageAnnotation, IRPoseImageAnnotation]
    assert Counter(annotation_types) == Counter(expected_types)

    reexported_task = LabelStudioTask.from_ir_annotations(annotations)

    # Assertions for LS task reexport
    # Pose metadata exists, 3 points + 1 bbox
    assert len(reexported_task.data["pose_points"]) == 1
    assert len(reexported_task.data["pose_points"][0]) == 3
    assert len(reexported_task.data["pose_boxes"]) == 1

    # 5 LS annotations: (3 keypoints + 1 bbox) for the pose + 1 single keypoint
    expected_ls_annotation_types = [
        KeyPointLabelsAnnotation,
        KeyPointLabelsAnnotation,
        KeyPointLabelsAnnotation,
        KeyPointLabelsAnnotation,
        RectangleLabelsAnnotation,
    ]
    reexported_annotation_types = [type(ann) for ann in reexported_task.annotations[0].result]
    assert Counter(reexported_annotation_types) == Counter(expected_ls_annotation_types)
