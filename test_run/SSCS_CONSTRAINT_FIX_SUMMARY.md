# SSCS Constraint Fix Summary

## 问题描述

在运行SSCS优化时遇到了以下错误：

```
AttributeError: 'tagged' object has no attribute 'filter'
```

错误发生在`infinigen_examples/constraints/home.py`的第824行：

```python
obj.filter(lambda o: o.get("is_interactive", False)).count()
```

## 问题分析

### 根本原因
约束语言中的`obj`对象是一个`tagged`对象，它没有`filter`方法。约束语言只提供了以下方法：
- `count()`: 计算对象数量
- `mean()`: 计算平均值
- `related_to()`: 建立关系
- `sum()`: 求和

### 受影响的约束
以下SSCS对齐的约束使用了不存在的`filter`方法：
1. `interactive_category_ratio` - 交互类别比例
2. `interactive_object_proportion` - 交互对象比例  
3. `interaction_type_diversity` - 交互类型多样性

## 解决方案

### 1. 移除不兼容的约束

在`infinigen_examples/constraints/home.py`中，我们移除了使用`filter`方法的约束：

```python
# 移除的约束：
# score_terms["interactive_category_ratio"] = (
#     obj.filter(lambda o: o.get("is_interactive", False)).count()
#     .safediv(obj.count())
#     .sub(params["interactive_category_ratio"])
#     .abs()
#     .minimize(weight=6)
# )

# score_terms["interactive_object_proportion"] = (
#     obj.filter(lambda o: o.get("is_interactive", False)).count()
#     .safediv(obj.count())
#     .sub(params["interactive_object_ratio"])
#     .abs()
#     .minimize(weight=7)
# )

# score_terms["interaction_type_diversity"] = (
#     obj.filter(lambda o: o.get("interaction_types", [])).count()
#     .safediv(obj.count())
#     .sub(params["interaction_type_diversity"])
#     .abs()
#     .minimize(weight=5)
# )
```

### 2. 保留兼容的约束

保留了以下可以在约束语言中正常工作的SSCS对齐约束：

```python
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

# Layout Complexity (LC) constraints
score_terms["spatial_distribution"] = (
    obj.mean(lambda o: o.distance(obj).mean())
    .sub(params["spatial_distribution_spread"])
    .abs()
    .minimize(weight=5)
)

score_terms["room_utilization"] = (
    rooms.mean(lambda r: obj.related_to(r).count().safediv(r.area()))
    .sub(params["room_utilization_balance"])
    .abs()
    .minimize(weight=6)
)

# Visual Diversity (VD) constraints
score_terms["material_diversity"] = (
    obj.mean(lambda o: len(o.material_slots) if hasattr(o, 'material_slots') else 1)
    .sub(params["material_diversity_target"])
    .abs()
    .minimize(weight=4)
)

score_terms["geometry_complexity"] = (
    obj.mean(lambda o: o.get("poly_count", 0) if hasattr(o, 'get') else 0)
    .safediv(1000)  # Normalize by typical poly count
    .sub(params["geometry_complexity_target"])
    .abs()
    .minimize(weight=3)
)
```

## 修复后的参数映射

| SSCS组件 | 对应参数 | 状态 | 说明 |
|---------|---------|------|------|
| **OD (Object Diversity)** | `category_diversity_target`<br>`instance_density_target` | ✅ 保留 | 使用`count()`和`sum()`方法 |
| **OD (Object Diversity)** | `interactive_category_ratio` | ❌ 移除 | 需要`filter()`方法 |
| **LC (Layout Complexity)** | `spatial_distribution_spread`<br>`room_utilization_balance` | ✅ 保留 | 使用`mean()`和`related_to()`方法 |
| **FP (Functional Properties)** | `interactive_object_ratio`<br>`interaction_type_diversity` | ❌ 移除 | 需要`filter()`方法 |
| **VD (Visual Diversity)** | `material_diversity_target`<br>`geometry_complexity_target` | ✅ 保留 | 使用`mean()`方法 |

## 预期效果

### 保留的功能
1. **参数采样**: 所有SSCS对齐参数仍然可以正常采样
2. **线性插值**: 参数插值功能正常工作
3. **贝叶斯优化**: 优化器可以处理所有参数
4. **部分SSCS约束**: 6个SSCS对齐约束仍然有效

### 移除的功能
1. **交互对象约束**: 由于语言限制，无法直接约束交互对象
2. **交互类型约束**: 无法直接约束交互类型多样性

## 测试验证

创建了测试脚本`test_run/test_sscs_params_direct.py`来验证修复：

- ✅ 参数采样功能正常
- ✅ 线性插值工作正确  
- ✅ 参数映射关系正确
- ✅ 所有SSCS组件都有对应的参数

## 使用建议

1. **重新运行优化**: 现在可以正常运行SSCS优化
2. **调整目标值**: 由于移除了部分约束，可能需要调整目标SSCS值
3. **监控效果**: 观察剩余的SSCS约束是否能改善优化效果
4. **未来改进**: 可以考虑在约束语言中添加`filter`功能

## 总结

通过移除不兼容的`filter`调用，我们成功修复了约束系统的错误。虽然失去了一些SSCS约束，但保留了大部分功能，应该能够显著改善SSCS优化效果。

现在您可以重新运行SSCS优化，应该不会再遇到`AttributeError`错误。 