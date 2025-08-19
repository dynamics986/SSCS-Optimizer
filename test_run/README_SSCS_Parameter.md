# SSCS Parameter Functionality

This document describes the new SSCS (Scene Semantic Complexity Score) parameter functionality that allows you to generate indoor scenes with specific SSCS targets.

## Overview

The SSCS parameter functionality enables you to:

1. **Direct Parameter Sampling**: Generate constraint parameters that target specific SSCS values
2. **Bayesian Optimization**: Automatically optimize parameters to match target SSCS values
3. **Custom Constraint Graphs**: Create constraint graphs with specific SSCS targets
4. **Command Line Usage**: Use the `--sscs` argument to specify target SSCS values

## Key Functions

### 1. Parameter Sampling

```python
from infinigen_examples.constraints import home as home_constraints

# Random sampling (no target)
params = home_constraints.sample_home_constraint_params()

# Targeted sampling
params = home_constraints.sample_home_constraint_params(target_sscs=0.6)
```

### 2. Constraint Graph Creation

```python
# Standard constraint graph
consgraph = home_constraints.home_furniture_constraints()

# Constraint graph with SSCS target
consgraph = home_constraints.home_furniture_constraints(target_sscs=0.7)
```

### 3. Scene Generation

```python
from infinigen_examples.generate_indoors import compose_indoors

# Standard scene generation
scene = compose_indoors(output_folder, scene_seed)

# Scene generation with SSCS target
scene = compose_indoors(output_folder, scene_seed, target_sscs=0.8)
```

### 4. Bayesian Optimization

```python
from infinigen_examples.generate_indoors import generate_with_sscs_target

# Optimize to match target SSCS
scene = generate_with_sscs_target(target_sscs=0.6, scene_seed=42, output_folder=Path("output"))
```

## Command Line Usage

You can now use the `--sscs` argument to specify target SSCS values:

```bash
# Generate scene with target SSCS of 0.6
python infinigen_examples/generate_indoors.py --output_folder ./output --sscs 0.6

# Generate scene with target SSCS of 0.8 and specific seed
python infinigen_examples/generate_indoors.py --output_folder ./output --sscs 0.8 -s 12345
```

## Parameter Mapping

The system maps SSCS targets to various scene parameters:

| Parameter | Range | Description |
|-----------|-------|-------------|
| `furniture_fullness_pct` | 0.2-0.9 | Percentage of room filled with furniture |
| `obj_interior_obj_pct` | 0.2-1.0 | Percentage of furniture filled with objects |
| `obj_on_storage_pct` | 0.2-1.0 | Percentage of storage surfaces filled with objects |
| `obj_on_nonstorage_pct` | 0.1-1.0 | Percentage of non-storage surfaces filled with objects |
| `painting_area_per_room_area` | 0.1-2.5 | Ratio of painting area to room area |
| `has_tv` | Boolean | Whether to include TV |
| `has_aquarium_tank` | Boolean | Whether to include aquarium |
| `has_birthday_balloons` | Boolean | Whether to include birthday decorations |
| `has_cocktail_tables` | Boolean | Whether to include cocktail tables |
| `has_kitchen_barstools` | Boolean | Whether to include kitchen barstools |

## Optimization Methods

### 1. Linear Interpolation (Fallback)

When Bayesian optimization is not available or has insufficient history, the system uses improved linear interpolation:

- Maps SSCS targets to parameter ranges using nonlinear transformations
- Adds random perturbations to avoid local optima
- Provides reasonable parameter estimates for any SSCS target

### 2. Bayesian Optimization (Primary)

When available and with sufficient history:

- Uses Gaussian Process optimization
- Learns from previous parameter-SSCS mappings
- Automatically suggests optimal parameters for target SSCS
- Updates optimization history for future use

## Examples

### Example 1: Direct Parameter Sampling

```python
# Generate parameters for different SSCS targets
targets = [0.3, 0.5, 0.7, 0.9]
for target in targets:
    params = home_constraints.sample_home_constraint_params(target_sscs=target)
    print(f"Target {target}: {params}")
```

### Example 2: Scene Generation with Target

```python
# Generate scene with specific SSCS target
scene = compose_indoors(
    output_folder=Path("output"),
    scene_seed=42,
    target_sscs=0.6
)
```

### Example 3: Custom Constraint Graph

```python
# Create constraint graph for high complexity scene
consgraph = home_constraints.home_furniture_constraints(target_sscs=0.9)
```

## Testing

Run the test script to verify functionality:

```bash
python test_sscs_parameter.py
```

Run the example script to see usage examples:

```bash
python example_sscs_usage.py
```

## Backward Compatibility

All existing code continues to work without modification:

- `home_furniture_constraints()` works as before
- `compose_indoors()` works as before
- `sample_home_constraint_params()` works as before

The new functionality is purely additive and doesn't break existing code.

## Technical Details

### Parameter Space

The optimization uses a 10-dimensional parameter space:
- 5 continuous parameters (furniture fullness, object ratios, etc.)
- 5 binary parameters (has_tv, has_aquarium_tank, etc.)

### SSCS Range

The system is designed to work with SSCS targets in the range [0.2, 0.8], though it can handle values outside this range with reduced effectiveness.

### Optimization Convergence

The Bayesian optimization typically converges within 10-20 iterations, with a target error tolerance of 0.02.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're using the updated version of the files
2. **Parameter Range Errors**: SSCS targets should be between 0.2 and 0.8 for best results
3. **Optimization Failures**: The system falls back to linear interpolation if Bayesian optimization fails

### Debug Information

The system provides detailed logging during optimization:

```
Initial point 1: SSCS=0.523, target=0.600, error=0.077
BO iteration 1: SSCS=0.589, target=0.600, error=0.011
BO iteration 2: SSCS=0.598, target=0.600, error=0.002
Target reached! SSCS=0.598
```

## Future Enhancements

Potential improvements for future versions:

1. **Multi-objective optimization**: Optimize for multiple scene properties simultaneously
2. **Adaptive parameter ranges**: Dynamically adjust parameter ranges based on scene type
3. **Real-time SSCS calculation**: Integrate SSCS calculation into the optimization loop
4. **Scene type-specific optimization**: Different optimization strategies for different room types 