"""
Base specifications for declarative dependency management.

This module provides the core classes for defining step dependencies and outputs
in a declarative, type-safe manner using Pydantic V2 BaseModel.
"""

from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING, Union
from abc import ABC, abstractmethod
import logging

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from .enums import DependencyType, NodeType

if TYPE_CHECKING:
    from .contract_base import ScriptContract, ValidationResult
else:
    # For runtime, we'll use Any to avoid circular imports
    ScriptContract = Any
    ValidationResult = Any

logger = logging.getLogger(__name__)


class DependencySpec(BaseModel):
    """Declarative specification for a step's dependency requirement."""

    model_config = ConfigDict(
        # Enable enum validation by value
        use_enum_values=True,
        # Validate assignment after object creation
        validate_assignment=True,
        # Allow arbitrary types for complex objects
        arbitrary_types_allowed=True,
        # Generate JSON schema
        json_schema_extra={
            "examples": [
                {
                    "logical_name": "training_data",
                    "dependency_type": "processing_output",
                    "required": True,
                    "compatible_sources": ["DataLoadingStep", "PreprocessingStep"],
                    "semantic_keywords": ["data", "dataset", "input"],
                    "data_type": "S3Uri",
                    "description": "Training dataset for model training",
                }
            ]
        },
    )

    logical_name: str = Field(
        ...,
        description="How this dependency is referenced",
        min_length=1,
        examples=["training_data", "model_input", "config_data"],
    )
    dependency_type: DependencyType = Field(..., description="Type of dependency")
    required: bool = Field(
        default=True, description="Whether this dependency is required"
    )
    compatible_sources: List[str] = Field(
        default_factory=list,
        description="Compatible step types that can provide this dependency",
    )
    semantic_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords for semantic matching during dependency resolution",
    )
    data_type: str = Field(
        default="S3Uri", description="Expected data type of the dependency"
    )
    description: str = Field(
        default="", description="Human-readable description of the dependency"
    )

    @field_validator("logical_name")
    @classmethod
    def validate_logical_name(cls, v: str) -> str:
        """Validate logical name is not empty and follows naming conventions."""
        if not v or not v.strip():
            raise ValueError("logical_name cannot be empty or whitespace")

        # Optional: Add naming convention validation
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "logical_name should contain only alphanumeric characters, underscores, and hyphens"
            )

        return v.strip()

    @field_validator("dependency_type")
    @classmethod
    def validate_dependency_type(cls, v: Any) -> DependencyType:
        """Validate dependency type is a valid enum value."""
        if isinstance(v, str):
            try:
                return DependencyType(v)
            except ValueError:
                valid_values = [e.value for e in DependencyType]
                raise ValueError(f"dependency_type must be one of: {valid_values}")
        elif isinstance(v, DependencyType):
            # With use_enum_values=True, we should return the enum value
            return v
        else:
            raise ValueError(
                "dependency_type must be a DependencyType enum or valid string value"
            )

    @field_validator("compatible_sources")
    @classmethod
    def validate_compatible_sources(cls, v: List[str]) -> List[str]:
        """Validate compatible sources list."""
        if not isinstance(v, list):
            raise ValueError("compatible_sources must be a list")

        # Remove empty strings and duplicates
        cleaned = list(set(source.strip() for source in v if source and source.strip()))
        return cleaned

    @field_validator("semantic_keywords")
    @classmethod
    def validate_semantic_keywords(cls, v: List[str]) -> List[str]:
        """Validate semantic keywords list."""
        if not isinstance(v, list):
            raise ValueError("semantic_keywords must be a list")

        # Remove empty strings, convert to lowercase, and remove duplicates
        cleaned = list(
            set(keyword.strip().lower() for keyword in v if keyword and keyword.strip())
        )
        return cleaned

    def matches_name_or_alias(self, name: str) -> bool:
        """
        Check if the given name matches the logical name or any alias.

        Args:
            name: The name to check

        Returns:
            True if the name matches the logical name or any alias
        """
        if name == self.logical_name:
            return True

        # DependencySpec doesn't have aliases in the current implementation
        # but we'll add this for consistency with the test expectations
        return hasattr(self, "aliases") and name in getattr(self, "aliases", [])


class OutputSpec(BaseModel):
    """Declarative specification for a step's output."""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "examples": [
                {
                    "logical_name": "processed_data",
                    "aliases": ["ProcessedData", "DATA"],
                    "output_type": "processing_output",
                    "property_path": "properties.ProcessingOutputConfig.Outputs['processed_data'].S3Output.S3Uri",
                    "data_type": "S3Uri",
                    "description": "Processed training data output",
                }
            ]
        },
    )

    logical_name: str = Field(
        ...,
        description="Primary name for this output",
        min_length=1,
        examples=["processed_data", "model_artifacts", "evaluation_results"],
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names that can be used to reference this output",
    )
    output_type: DependencyType = Field(..., description="Type of output")
    property_path: str = Field(
        ...,
        description="Runtime SageMaker property path to access this output",
        min_length=1,
    )
    data_type: str = Field(default="S3Uri", description="Output data type")
    description: str = Field(
        default="", description="Human-readable description of the output"
    )

    @field_validator("logical_name")
    @classmethod
    def validate_logical_name(cls, v: str) -> str:
        """Validate logical name is not empty and follows naming conventions."""
        if not v or not v.strip():
            raise ValueError("logical_name cannot be empty or whitespace")

        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "logical_name should contain only alphanumeric characters, underscores, and hyphens"
            )

        return v.strip()

    @field_validator("output_type")
    @classmethod
    def validate_output_type(cls, v: Any) -> DependencyType:
        """Validate output type is a valid enum value."""
        if isinstance(v, str):
            try:
                return DependencyType(v)
            except ValueError:
                valid_values = [e.value for e in DependencyType]
                raise ValueError(f"output_type must be one of: {valid_values}")
        elif isinstance(v, DependencyType):
            # With use_enum_values=True, we should return the enum value
            return v
        else:
            raise ValueError(
                "output_type must be a DependencyType enum or valid string value"
            )

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, v: List[str]) -> List[str]:
        """Validate aliases list."""
        if not isinstance(v, list):
            raise ValueError("aliases must be a list")

        # Remove empty strings, strip whitespace, and remove duplicates
        cleaned = []
        seen = set()
        for alias in v:
            if alias and alias.strip():
                alias_clean = alias.strip()
                # Validate alias follows same naming conventions as logical names
                if not alias_clean.replace("_", "").replace("-", "").isalnum():
                    raise ValueError(
                        f"alias '{alias_clean}' should contain only alphanumeric characters, underscores, and hyphens"
                    )
                if alias_clean.lower() not in seen:
                    cleaned.append(alias_clean)
                    seen.add(alias_clean.lower())

        return cleaned

    @field_validator("property_path")
    @classmethod
    def validate_property_path(cls, v: str) -> str:
        """Validate property path is not empty and has basic structure."""
        if not v or not v.strip():
            raise ValueError("property_path cannot be empty or whitespace")

        # Basic validation for SageMaker property path structure
        v = v.strip()
        if not v.startswith("properties."):
            raise ValueError("property_path should start with 'properties.'")

        return v

    @model_validator(mode="after")
    def validate_aliases_no_conflict(self) -> "OutputSpec":
        """Validate that aliases don't conflict with the logical name."""
        if self.aliases:
            # Check if any alias matches the logical name (case-insensitive)
            logical_name_lower = self.logical_name.lower()
            for alias in self.aliases:
                if alias.lower() == logical_name_lower:
                    raise ValueError(
                        f"alias '{alias}' cannot be the same as logical_name '{self.logical_name}'"
                    )

        return self

    def matches_name_or_alias(self, name: str) -> bool:
        """
        Check if the given name matches the logical name or any alias.

        Args:
            name: The name to check

        Returns:
            True if the name matches the logical name or any alias
        """
        if name == self.logical_name:
            return True

        return name in self.aliases


# PropertyReference has been moved to property_reference.py
# Import moved to avoid circular dependency - use TYPE_CHECKING if needed
if TYPE_CHECKING:
    from ..deps.property_reference import PropertyReference


class StepSpecification(BaseModel):
    """Complete specification for a step's dependencies and outputs."""

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
        use_enum_values=False,  # Store enum instances, not values
        json_schema_extra={
            "examples": [
                {
                    "step_type": "DataProcessingStep",
                    "node_type": "internal",
                    "dependencies": {
                        "input_data": {
                            "logical_name": "input_data",
                            "dependency_type": "processing_output",
                            "required": True,
                            "compatible_sources": ["DataLoadingStep"],
                            "data_type": "S3Uri",
                        }
                    },
                    "outputs": {
                        "processed_data": {
                            "logical_name": "processed_data",
                            "output_type": "processing_output",
                            "property_path": "properties.ProcessingOutputConfig.Outputs['ProcessedData'].S3Output.S3Uri",
                            "data_type": "S3Uri",
                        }
                    },
                }
            ]
        },
    )

    step_type: str = Field(
        ..., description="Type identifier for this step", min_length=1
    )
    node_type: NodeType = Field(
        ..., description="Node type classification for validation"
    )
    dependencies: Dict[str, DependencySpec] = Field(
        default_factory=dict,
        description="Dictionary of dependency specifications keyed by logical name",
    )
    outputs: Dict[str, OutputSpec] = Field(
        default_factory=dict,
        description="Dictionary of output specifications keyed by logical name",
    )
    script_contract: Optional["ScriptContract"] = Field(
        default=None, description="Optional script contract for validation"
    )

    def __init__(
        self,
        step_type: Optional[str] = None,
        dependencies: Optional[List[DependencySpec]] = None,
        outputs: Optional[List[OutputSpec]] = None,
        node_type: Optional[NodeType] = None,
        **data: Any,
    ) -> None:
        """
        Initialize step specification with backward compatibility.

        Args:
            step_type: Type identifier for this step
            dependencies: List of dependency specifications
            outputs: List of output specifications
            node_type: Node type classification for validation
        """
        # Handle direct model_validate calls
        if step_type is None and "step_type" in data:
            step_type = data.pop("step_type")
        if node_type is None and "node_type" in data:
            node_type = data.pop("node_type")
        if dependencies is None and "dependencies" in data:
            deps_data = data.pop("dependencies")
            if isinstance(deps_data, dict):
                # Already in dict format from model_validate
                dependencies = list(deps_data.values())
            else:
                dependencies = deps_data
        if outputs is None and "outputs" in data:
            outputs_data = data.pop("outputs")
            if isinstance(outputs_data, dict):
                # Already in dict format from model_validate
                outputs = list(outputs_data.values())
            else:
                outputs = outputs_data

        # Set defaults
        if dependencies is None:
            dependencies = []
        if outputs is None:
            outputs = []

        # Convert lists to dictionaries for internal storage
        if isinstance(dependencies, list):
            deps_dict = {dep.logical_name: dep for dep in dependencies}
        else:
            deps_dict = dependencies

        if isinstance(outputs, list):
            outputs_dict = {out.logical_name: out for out in outputs}
        else:
            outputs_dict = outputs

        # Check for duplicates
        if isinstance(dependencies, list) and len(deps_dict) != len(dependencies):
            raise ValueError("Duplicate dependency logical names found")
        if isinstance(outputs, list) and len(outputs_dict) != len(outputs):
            raise ValueError("Duplicate output logical names found")

        super().__init__(
            step_type=step_type,
            node_type=node_type,
            dependencies=deps_dict,
            outputs=outputs_dict,
            **data,
        )

    @field_validator("step_type")
    @classmethod
    def validate_step_type(cls, v: str) -> str:
        """Validate step type is not empty."""
        if not v or not v.strip():
            raise ValueError("step_type cannot be empty or whitespace")
        return v.strip()

    @field_validator("node_type", mode="before")
    @classmethod
    def validate_node_type(cls, v: Any) -> NodeType:
        """Validate node type is a valid enum value."""
        if isinstance(v, str):
            try:
                return NodeType(v)
            except ValueError:
                valid_values = [e.value for e in NodeType]
                raise ValueError(f"node_type must be one of: {valid_values}, got: {v}")
        elif isinstance(v, NodeType):
            # Return the enum instance
            return v
        else:
            # Handle other cases more gracefully
            try:
                if hasattr(v, "value") and v.value in [e.value for e in NodeType]:
                    return NodeType(v.value)  # Convert enum-like object to NodeType
                return NodeType(str(v))  # Try to convert to string and then to NodeType
            except:
                raise ValueError(
                    f"node_type must be a NodeType enum or valid string value, got: {type(v).__name__}"
                )

    @model_validator(mode="after")
    def validate_node_type_constraints(self) -> "StepSpecification":
        """Validate that dependencies and outputs match the node type."""
        has_deps = len(self.dependencies) > 0
        has_outputs = len(self.outputs) > 0

        if self.node_type == NodeType.SOURCE:
            if has_deps:
                raise ValueError(
                    f"SOURCE node '{self.step_type}' cannot have dependencies"
                )
            if not has_outputs:
                raise ValueError(f"SOURCE node '{self.step_type}' must have outputs")
        elif self.node_type == NodeType.INTERNAL:
            if not has_deps:
                raise ValueError(
                    f"INTERNAL node '{self.step_type}' must have dependencies"
                )
            if not has_outputs:
                raise ValueError(f"INTERNAL node '{self.step_type}' must have outputs")
        elif self.node_type == NodeType.SINK:
            if not has_deps:
                raise ValueError(f"SINK node '{self.step_type}' must have dependencies")
            if has_outputs:
                raise ValueError(f"SINK node '{self.step_type}' cannot have outputs")
        elif self.node_type == NodeType.SINGULAR:
            if has_deps:
                raise ValueError(
                    f"SINGULAR node '{self.step_type}' cannot have dependencies"
                )
            if has_outputs:
                raise ValueError(
                    f"SINGULAR node '{self.step_type}' cannot have outputs"
                )

        # Validate that aliases don't conflict across outputs
        self._validate_output_aliases()

        return self

    def _validate_output_aliases(self) -> None:
        """Validate that aliases don't conflict across different outputs."""
        if not self.outputs:
            return

        # Collect all logical names and aliases (case-insensitive)
        all_names = set()
        conflicts = []

        for output_spec in self.outputs.values():
            # Check logical name
            logical_name_lower = output_spec.logical_name.lower()
            if logical_name_lower in all_names:
                conflicts.append(
                    f"Duplicate logical name: '{output_spec.logical_name}'"
                )
            else:
                all_names.add(logical_name_lower)

            # Check aliases
            for alias in output_spec.aliases:
                alias_lower = alias.lower()
                if alias_lower in all_names:
                    conflicts.append(
                        f"Alias '{alias}' conflicts with existing name or alias"
                    )
                else:
                    all_names.add(alias_lower)

        if conflicts:
            raise ValueError(
                f"Output name/alias conflicts in step '{self.step_type}': {'; '.join(conflicts)}"
            )

    def get_dependency(self, logical_name: str) -> Optional[DependencySpec]:
        """Get dependency specification by logical name."""
        return self.dependencies.get(logical_name)

    def get_output(self, logical_name: str) -> Optional[OutputSpec]:
        """Get output specification by logical name."""
        return self.outputs.get(logical_name)

    def get_output_by_name_or_alias(self, name: str) -> Optional[OutputSpec]:
        """
        Get output specification by logical name or alias.

        Args:
            name: The logical name or alias to search for

        Returns:
            OutputSpec if found, None otherwise
        """
        # First try exact logical name match
        if name in self.outputs:
            return self.outputs[name]

        # Then search through aliases (case-insensitive)
        name_lower = name.lower()
        for output_spec in self.outputs.values():
            for alias in output_spec.aliases:
                if alias.lower() == name_lower:
                    return output_spec

        return None

    def list_all_output_names(self) -> List[str]:
        """
        Get list of all possible output names (logical names + aliases).

        Returns:
            List of all names that can be used to reference outputs
        """
        all_names = []
        for output_spec in self.outputs.values():
            all_names.append(output_spec.logical_name)
            all_names.extend(output_spec.aliases)
        return all_names

    def list_required_dependencies(self) -> List[DependencySpec]:
        """Get list of required dependencies."""
        return [dep for dep in self.dependencies.values() if dep.required]

    def list_optional_dependencies(self) -> List[DependencySpec]:
        """Get list of optional dependencies."""
        return [dep for dep in self.dependencies.values() if not dep.required]

    def list_dependencies_by_type(
        self, dependency_type: DependencyType
    ) -> List[DependencySpec]:
        """Get list of dependencies of a specific type."""
        return [
            dep
            for dep in self.dependencies.values()
            if dep.dependency_type == dependency_type
        ]

    def list_outputs_by_type(self, output_type: DependencyType) -> List[OutputSpec]:
        """Get list of outputs of a specific type."""
        return [out for out in self.outputs.values() if out.output_type == output_type]

    def validate_specification(self) -> List[str]:
        """Validate the specification for consistency (legacy method for backward compatibility)."""
        # This method is kept for backward compatibility
        # Pydantic V2 handles most validation automatically
        errors = []

        # Additional custom validation can be added here
        if (
            not self.dependencies
            and not self.outputs
            and self.node_type != NodeType.SINGULAR
        ):
            errors.append(f"Step '{self.step_type}' has no dependencies or outputs")

        return errors

    def validate_contract_alignment(self) -> "ValidationResult":
        """
        Validate that script contract aligns with step specification.

        This validation logic:
        - Specs can provide more inputs than contracts require (extra dependencies allowed)
        - Contracts can have fewer outputs than specs provide (aliases allowed)
        - For every contract input, there must be a matching spec dependency
        - For every contract output, there must be a matching spec output

        Returns:
            ValidationResult indicating whether the contract aligns with the specification
        """
        # Import here to avoid circular imports
        from .contract_base import ValidationResult

        if not self.script_contract:
            return ValidationResult.success("No contract to validate")

        errors = []

        # Validate input alignment: every contract input must have a matching spec dependency
        contract_inputs = set(self.script_contract.expected_input_paths.keys())
        spec_dependency_names = set(
            dep.logical_name for dep in self.dependencies.values()
        )

        missing_spec_dependencies = contract_inputs - spec_dependency_names
        if missing_spec_dependencies:
            errors.append(
                f"Contract inputs missing from specification dependencies: {missing_spec_dependencies}"
            )

        # Validate output alignment: every contract output must have a matching spec output
        contract_outputs = set(self.script_contract.expected_output_paths.keys())
        spec_output_names = set(output.logical_name for output in self.outputs.values())

        missing_spec_outputs = contract_outputs - spec_output_names
        if missing_spec_outputs:
            errors.append(
                f"Contract outputs missing from specification outputs: {missing_spec_outputs}"
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def validate_script_compliance(self, script_path: str) -> "ValidationResult":
        """
        Validate script implementation against contract.

        Args:
            script_path: Path to the script file to validate

        Returns:
            ValidationResult indicating whether the script complies with the contract
        """
        if not self.script_contract:
            # Import here to avoid circular imports
            from .contract_base import ValidationResult

            return ValidationResult.success("No script contract defined")
        return self.script_contract.validate_implementation(script_path)

    def __repr__(self) -> str:
        return (
            f"StepSpecification(type='{self.step_type}', "
            f"dependencies={len(self.dependencies)}, "
            f"outputs={len(self.outputs)})"
        )

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "StepSpecification":
        """Custom model_validate to handle enum conversion."""
        if isinstance(obj, dict) and "node_type" in obj:
            # Convert string node_type to enum instance
            if isinstance(obj["node_type"], str):
                try:
                    obj = obj.copy()  # Create a copy to avoid modifying the original
                    obj["node_type"] = NodeType(obj["node_type"])
                except ValueError:
                    pass  # Let the validator handle the error
            elif hasattr(obj["node_type"], "value"):
                # Handle case where node_type is already an enum instance
                try:
                    obj = obj.copy()
                    obj["node_type"] = NodeType(obj["node_type"].value)
                except ValueError:
                    pass  # Let the validator handle the error
        return super().model_validate(obj, **kwargs)


# Note: SpecificationRegistry has been moved to specification_registry.py
# See registry_manager.py for registry management functionality
