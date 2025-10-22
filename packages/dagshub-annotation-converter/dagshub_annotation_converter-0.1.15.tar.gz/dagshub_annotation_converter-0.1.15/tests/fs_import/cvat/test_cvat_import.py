from pathlib import Path

from dagshub_annotation_converter.converters.cvat import load_cvat_from_xml_file
from dagshub_annotation_converter.ir.image import (
    IRBBoxImageAnnotation,
    IRSegmentationImageAnnotation,
    IRPoseImageAnnotation,
)


def test_cvat_import():
    annotation_file = Path(__file__).parent / "annotations.xml"
    annotations = load_cvat_from_xml_file(annotation_file)

    expected_files = ["001.png", "002.png", "003.png", "004.png"]
    assert list(annotations.keys()) == list(expected_files)

    # Check only the annotation types, but not the annotations themselves (otherwise the parsing tests would fail)
    expected_annotations = [
        [IRBBoxImageAnnotation],
        [
            IRSegmentationImageAnnotation,
            IRBBoxImageAnnotation,
            IRSegmentationImageAnnotation,
            IRSegmentationImageAnnotation,
            IRBBoxImageAnnotation,
            IRSegmentationImageAnnotation,
        ],
        [IRBBoxImageAnnotation, IRPoseImageAnnotation],
        [IRPoseImageAnnotation],
    ]

    actual_annotations = [[type(ann) for ann in annotations[file]] for file in expected_files]

    assert expected_annotations == actual_annotations
