from typing import List

import pytest

from dagshub_annotation_converter.formats.label_studio.polygonlabels import PolygonLabelsAnnotation
from dagshub_annotation_converter.formats.label_studio.task import parse_ls_task, LabelStudioTask
from dagshub_annotation_converter.ir.image import (
    IRSegmentationImageAnnotation,
    CoordinateStyle,
    IRSegmentationPoint,
)
from tests.label_studio.common import generate_annotation, generate_task


@pytest.fixture
def segmentation_points() -> List[List[int]]:
    return [
        [50, 50],
        [75, 75],
        [75, 50],
    ]


@pytest.fixture
def segmentation_annotation(segmentation_points) -> dict:
    annotation = {
        "points": segmentation_points,
        "polygonlabels": ["dog"],
        "closed": True,
    }
    return generate_annotation(annotation, "polygonlabels", "deadbeef")


@pytest.fixture
def segmentation_task(segmentation_annotation) -> str:
    return generate_task([segmentation_annotation])


@pytest.fixture
def parsed_segmentation_task(segmentation_task) -> LabelStudioTask:
    return parse_ls_task(segmentation_task)


def test_segmentation_parsing(parsed_segmentation_task, segmentation_points):
    actual = parsed_segmentation_task
    assert len(actual.annotations) == 1
    assert len(actual.annotations[0].result) == 1

    ann = actual.annotations[0].result[0]
    assert isinstance(ann, PolygonLabelsAnnotation)
    assert ann.value.points == segmentation_points


def test_segmentation_ir(parsed_segmentation_task, segmentation_points):
    actual = parsed_segmentation_task.annotations[0].result[0].to_ir_annotation()

    assert len(actual) == 1
    ann = actual[0]
    assert isinstance(ann, IRSegmentationImageAnnotation)

    converted_points = [IRSegmentationPoint(x=x / 100, y=y / 100) for x, y in segmentation_points]

    assert ann.points == converted_points
    assert ann.coordinate_style == CoordinateStyle.NORMALIZED


def test_ir_segmentation_addition():
    task = LabelStudioTask()

    task.add_ir_annotation(
        IRSegmentationImageAnnotation(
            image_height=100,
            image_width=100,
            categories={"dog": 1.0},
            coordinate_style=CoordinateStyle.NORMALIZED,
            points=[
                IRSegmentationPoint(x=0.5, y=0.5),
                IRSegmentationPoint(x=0.75, y=0.75),
                IRSegmentationPoint(x=0.75, y=0.5),
            ],
        )
    )

    assert len(task.annotations) == 1
    assert len(task.annotations[0].result) == 1

    ann = task.annotations[0].result[0]
    assert isinstance(ann, PolygonLabelsAnnotation)
    assert ann.value.points == [[50, 50], [75, 75], [75, 50]]
    assert ann.value.polygonlabels == ["dog"]
