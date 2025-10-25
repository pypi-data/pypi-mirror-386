"""
Temporal Feature Engineering Testing Step Specification.

This module defines the declarative specification for temporal feature engineering steps
specifically for testing data, including their dependencies and outputs.
"""

from ...core.base.specification_base import (
    StepSpecification,
    DependencySpec,
    OutputSpec,
    DependencyType,
    NodeType,
)
from ...registry.step_names import get_spec_step_type_with_job_type


# Import the contract at runtime to avoid circular imports
def _get_temporal_feature_engineering_contract():
    from ..contracts.temporal_feature_engineering_contract import TEMPORAL_FEATURE_ENGINEERING_CONTRACT

    return TEMPORAL_FEATURE_ENGINEERING_CONTRACT


# Temporal Feature Engineering Testing Step Specification
TEMPORAL_FEATURE_ENGINEERING_TESTING_SPEC = StepSpecification(
    step_type=get_spec_step_type_with_job_type("TemporalFeatureEngineering", "testing"),
    node_type=NodeType.INTERNAL,
    script_contract=_get_temporal_feature_engineering_contract(),
    dependencies=[
        DependencySpec(
            logical_name="normalized_sequences",
            dependency_type=DependencyType.PROCESSING_OUTPUT,
            required=True,
            compatible_sources=["TemporalSequenceNormalization", "ProcessingStep"],
            semantic_keywords=[
                "normalized_sequences",
                "sequences",
                "temporal_data",
                "sequence_data",
                "normalized_data",
                "processed_sequences",
                "testing_sequences",
                "temporal",
                "sequence",
                "time_series",
                "sequential",
                "testing",
                "test",
                "model_testing",
            ],
            data_type="S3Uri",
            description="Normalized testing temporal sequences for feature engineering",
        )
    ],
    outputs=[
        OutputSpec(
            logical_name="temporal_feature_tensors",
            aliases=[
                "features",
                "temporal_features",
                "feature_tensors",
                "engineered_features",
                "feature_matrix",
                "ml_features",
                "testing_features",
            ],
            output_type=DependencyType.PROCESSING_OUTPUT,
            property_path="properties.ProcessingOutputConfig.Outputs['temporal_feature_tensors'].S3Output.S3Uri",
            data_type="S3Uri",
            description="Testing temporal feature tensors for machine learning model consumption",
        )
    ],
)
