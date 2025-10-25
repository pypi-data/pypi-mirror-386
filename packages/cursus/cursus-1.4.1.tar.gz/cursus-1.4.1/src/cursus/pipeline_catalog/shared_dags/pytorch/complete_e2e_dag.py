"""
Shared DAG definition for PyTorch Complete End-to-End Pipeline

This module provides the shared DAG definition for a complete PyTorch workflow
that includes training, calibration, packaging, registration, and evaluation.
This DAG can be used by both regular and MODS pipeline variants to ensure consistency.

The DAG includes:
1) Data Loading (training)
2) Preprocessing (training)
3) PyTorch Model Training
4) Model Calibration
5) Package Model
6) Payload Generation
7) Model Registration
8) Data Loading (calibration)
9) Preprocessing (calibration)
10) Model Evaluation (calibration)
"""

import logging
from typing import Dict, Any

from ....api.dag.base_dag import PipelineDAG
from .. import DAGMetadata

logger = logging.getLogger(__name__)


def create_pytorch_complete_e2e_dag() -> PipelineDAG:
    """
    Create a DAG for complete PyTorch E2E pipeline.

    This DAG represents a complete end-to-end workflow including training,
    calibration, packaging, registration, and evaluation of a PyTorch model.

    Returns:
        PipelineDAG: The directed acyclic graph for the pipeline
    """
    dag = PipelineDAG()

    # Add all nodes - using PyTorchTraining instead of XGBoostTraining
    dag.add_node("CradleDataLoading_training")  # Data load for training
    dag.add_node("TabularPreprocessing_training")  # Tabular preprocessing for training
    dag.add_node("PyTorchTraining")  # PyTorch training step
    dag.add_node(
        "ModelCalibration_calibration"
    )  # Model calibration step with calibration variant
    dag.add_node("Package")  # Package step
    dag.add_node("Registration")  # MIMS registration step
    dag.add_node("Payload")  # Payload step
    dag.add_node("CradleDataLoading_calibration")  # Data load for calibration
    dag.add_node(
        "TabularPreprocessing_calibration"
    )  # Tabular preprocessing for calibration
    dag.add_node("PyTorchModelEval_calibration")  # Model evaluation step

    # Training flow
    dag.add_edge("CradleDataLoading_training", "TabularPreprocessing_training")
    dag.add_edge("TabularPreprocessing_training", "PyTorchTraining")

    # Calibration flow
    dag.add_edge("CradleDataLoading_calibration", "TabularPreprocessing_calibration")

    # Evaluation flow
    dag.add_edge("PyTorchTraining", "PyTorchModelEval_calibration")
    dag.add_edge("TabularPreprocessing_calibration", "PyTorchModelEval_calibration")

    # Model calibration flow - depends on model evaluation
    dag.add_edge("PyTorchModelEval_calibration", "ModelCalibration_calibration")

    # Output flow
    dag.add_edge("ModelCalibration_calibration", "Package")
    dag.add_edge("PyTorchTraining", "Package")  # Raw model is also input to packaging
    dag.add_edge("PyTorchTraining", "Payload")  # Payload test uses the raw model
    dag.add_edge("Package", "Registration")
    dag.add_edge("Payload", "Registration")

    logger.info(
        f"Created PyTorch complete E2E DAG with {len(dag.nodes)} nodes and {len(dag.edges)} edges"
    )
    return dag


def get_dag_metadata() -> DAGMetadata:
    """
    Get metadata for the PyTorch complete end-to-end DAG.

    Returns:
        DAGMetadata: Metadata describing the DAG structure and purpose
    """
    return DAGMetadata(
        description="Complete PyTorch end-to-end pipeline with training, calibration, packaging, registration, and evaluation",
        complexity="comprehensive",
        features=["training", "calibration", "packaging", "registration", "evaluation"],
        framework="pytorch",
        node_count=10,
        edge_count=11,
        extra_metadata={
            "name": "pytorch_complete_e2e",
            "task_type": "end_to_end",
            "entry_points": [
                "CradleDataLoading_training",
                "CradleDataLoading_calibration",
            ],
            "exit_points": ["Registration"],
            "required_configs": [
                "CradleDataLoading_training",
                "CradleDataLoading_calibration",
                "TabularPreprocessing_training",
                "TabularPreprocessing_calibration",
                "PyTorchTraining",
                "PyTorchModelEval_calibration",
                "ModelCalibration_calibration",
                "Package",
                "Payload",
                "Registration",
            ],
        },
    )


def validate_dag_structure(dag: PipelineDAG) -> Dict[str, Any]:
    """
    Validate the structure of the PyTorch complete end-to-end DAG.

    Args:
        dag: The DAG to validate

    Returns:
        Dict containing validation results
    """
    metadata = get_dag_metadata()

    validation_result = {"is_valid": True, "errors": [], "warnings": []}

    # Check node count
    if len(dag.nodes) != metadata.node_count:
        validation_result["errors"].append(
            f"Expected {metadata.node_count} nodes, found {len(dag.nodes)}"
        )
        validation_result["is_valid"] = False

    # Check edge count
    if len(dag.edges) != metadata.edge_count:
        validation_result["errors"].append(
            f"Expected {metadata.edge_count} edges, found {len(dag.edges)}"
        )
        validation_result["is_valid"] = False

    # Check required nodes exist
    required_configs = metadata.extra_metadata.get("required_configs", [])
    missing_nodes = set(required_configs) - set(dag.nodes)
    if missing_nodes:
        validation_result["errors"].append(f"Missing required nodes: {missing_nodes}")
        validation_result["is_valid"] = False

    # Check entry points exist
    entry_points = metadata.extra_metadata.get("entry_points", [])
    missing_entry_points = set(entry_points) - set(dag.nodes)
    if missing_entry_points:
        validation_result["errors"].append(
            f"Missing entry points: {missing_entry_points}"
        )
        validation_result["is_valid"] = False

    # Check exit points exist
    exit_points = metadata.extra_metadata.get("exit_points", [])
    missing_exit_points = set(exit_points) - set(dag.nodes)
    if missing_exit_points:
        validation_result["errors"].append(
            f"Missing exit points: {missing_exit_points}"
        )
        validation_result["is_valid"] = False

    return validation_result
