# SSCS Parameter Optimization Summary

## 问题分析

您遇到的问题是生成的场景SSCS数值不理想，离目标差距较大。通过分析代码，我发现了根本原因：

### 1. **参数定义与SSCS指标不匹配**

**原始优化参数**主要影响：
- 家具填充度 (`furniture_fullness_pct`)
- 对象内部对象填充度 (`obj_interior_obj_pct`)
- 存储对象上的对象填充度 (`obj_on_storage_pct`)
- 非存储对象上的对象填充度 (`obj_on_nonstorage_pct`)
- 绘画面积比例 (`painting_area_per_room_area`)
- 各种布尔参数 (`has_tv`, `has_aquarium_tank`等)

**SSCS指标组成**：
- **OD (Object Diversity)**: 类别数量、实例数量、交互类别比例
- **LC (Layout Complexity)**: 空间熵
- **FP (Functional Properties)**: 交互对象比例、交互类型数量
- **VD (Visual Diversity)**: 材质数量、平均多边形数量

### 2. **参数影响范围有限**

原始参数主要影响对象密度和分布，但SSCS指标还涉及：
- 材质多样性
- 交互类型多样性
- 空间分布复杂性

## 解决方案

### 1. **新增SSCS对齐参数**

在`infinigen_examples/generate_indoors.py`中修改了`param_space`：

```python
param_space = [
    # Object Diversity (OD) - 直接影响类别数量和实例数量
    Real(0.1, 0.8, name='category_diversity_target'),  # 目标类别多样性
    Real(0.2, 1.0, name='instance_density_target'),    # 目标实例密度
    Real(0.1, 0.9, name='interactive_category_ratio'), # 交互类别比例
    
    # Layout Complexity (LC) - 影响空间分布
    Real(0.1, 0.9, name='spatial_distribution_spread'), # 空间分布分散度
    Real(0.2, 0.8, name='room_utilization_balance'),   # 房间利用率平衡
    
    # Functional Properties (FP) - 影响交互对象和交互类型
    Real(0.1, 0.8, name='interactive_object_ratio'),   # 交互对象比例
    Real(0.1, 0.9, name='interaction_type_diversity'), # 交互类型多样性
    
    # Visual Diversity (VD) - 影响材质和几何复杂度
    Real(0.2, 0.9, name='material_diversity_target'),  # 材质多样性目标
    Real(0.1, 0.8, name='geometry_complexity_target'), # 几何复杂度目标
    
    # 原有的填充度参数（保留但调整权重）
    Real(0.2, 0.9, name='furniture_fullness_pct'),
    Real(0.2, 1.0, name='obj_interior_obj_pct'),
    Real(0.2, 1.0, name='obj_on_storage_pct'),
    Real(0.1, 1.0, name='obj_on_nonstorage_pct'),
    Real(0.1, 2.5, name='painting_area_per_room_area'),
    
    # 布尔参数（保留）
    Integer(0, 1, name='has_tv_prob'),
    Integer(0, 1, name='has_aquarium_tank_prob'),
    Integer(0, 1, name='has_birthday_balloons_prob'),
    Integer(0, 1, name='has_cocktail_tables_prob'),
    Integer(0, 1, name='has_kitchen_barstools_prob'),
]
```

### 2. **更新参数采样函数**

在`infinigen_examples/constraints/home.py`中更新了：
- `_random_sample_params()`: 添加SSCS对齐参数
- `linear_interpolation()`: 改进插值算法
- `_bayesian_optimization_sample()`: 支持新参数
- `_calculate_param_similarity()`: 包含新参数

### 3. **添加SSCS对齐约束**

在`home_furniture_constraints()`函数中添加了新的约束：

```python
# region SSCS-aligned constraints
if 'category_diversity_target' in params:
    # Object Diversity (OD) constraints
    score_terms["category_diversity"] = (
        obj.count().safediv(rooms.count())
        .sub(params["category_diversity_target"])
        .abs()
        .minimize(weight=8)
    )
    
    score_terms["instance_density"] = (
        obj.count().safediv(rooms.sum(lambda r: r.area()))
        .sub(params["instance_density_target"])
        .abs()
        .minimize(weight=8)
    )
    
    # ... 更多约束
# endregion SSCS-aligned constraints
```

### 4. **更新优化器参数转换**

更新了`BayesianOptimizer`类中的：
- `_sample_random_params()`: 包含新参数
- `_convert_to_dict()`: 正确处理新参数
- `_update_optimizer()`: 包含新参数

## 参数映射关系

| SSCS组件 | 对应参数 | 影响范围 |
|---------|---------|---------|
| **OD (Object Diversity)** | `category_diversity_target`<br>`instance_density_target`<br>`interactive_category_ratio` | 类别数量、实例密度、交互类别比例 |
| **LC (Layout Complexity)** | `spatial_distribution_spread`<br>`room_utilization_balance` | 空间分布、房间利用率 |
| **FP (Functional Properties)** | `interactive_object_ratio`<br>`interaction_type_diversity` | 交互对象比例、交互类型多样性 |
| **VD (Visual Diversity)** | `material_diversity_target`<br>`geometry_complexity_target` | 材质多样性、几何复杂度 |

## 预期效果

通过这些修改，优化过程现在能够：

1. **直接控制SSCS指标**：新参数直接对应SSCS的四个组件
2. **更精确的优化**：参数与目标指标有明确的映射关系
3. **更好的收敛性**：参数空间更符合SSCS指标的结构
4. **保持兼容性**：原有参数仍然保留，确保向后兼容

## 测试验证

创建了测试脚本`test_run/test_sscs_params_direct.py`来验证修改：

- ✅ 参数采样功能正常
- ✅ 线性插值工作正确
- ✅ 参数映射关系正确
- ✅ 所有SSCS组件都有对应的参数

## 使用建议

1. **重新运行优化**：使用新的参数空间重新进行贝叶斯优化
2. **调整目标值**：根据新的参数映射，可能需要调整目标SSCS值
3. **监控收敛**：观察优化过程是否更快收敛到目标值
4. **参数调优**：根据实际效果调整各参数的权重和范围

这些修改应该能显著改善SSCS优化效果，使生成的场景更接近目标SSCS值。 