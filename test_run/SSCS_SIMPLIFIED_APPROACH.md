# SSCS Simplified Approach

## 问题反思

经过多次尝试，我意识到我们之前的SSCS约束方法存在根本性问题：

### 1. **约束语言限制**
- 约束语言不支持复杂的过滤操作（如`filter`）
- 距离计算不支持嵌套的`mean()`操作
- 添加新约束容易导致语法错误

### 2. **跳过场景生成**
- 复杂的约束可能导致求解器失败
- 约束系统可能直接跳过场景生成步骤
- 无法真正影响SSCS指标

### 3. **参数映射不直接**
- SSCS参数与实际场景生成参数之间映射关系不明确
- 优化过程可能无法收敛到目标SSCS值

## 新的简化方法

### 1. **参数调整而非新约束**
Instead of adding new constraints, we adjust existing parameters based on SSCS targets:

```python
# Adjust existing constraint parameters based on SSCS target
if 'category_diversity_target' in params:
    # Adjust furniture fullness to affect object diversity
    adjusted_furniture_fullness = params["furniture_fullness_pct"] * (1 + params["category_diversity_target"] * 0.3)
    params["furniture_fullness_pct"] = min(adjusted_furniture_fullness, 0.9)
    
    # Adjust object density parameters
    if params["instance_density_target"] > 0.5:
        params["obj_interior_obj_pct"] = min(params["obj_interior_obj_pct"] * 1.2, 1.0)
        params["obj_on_storage_pct"] = min(params["obj_on_storage_pct"] * 1.2, 1.0)
        params["obj_on_nonstorage_pct"] = min(params["obj_on_nonstorage_pct"] * 1.2, 1.0)
```

### 2. **参数映射关系**

| SSCS组件 | 调整的参数 | 影响方式 |
|---------|-----------|---------|
| **Object Diversity** | `furniture_fullness_pct` | 增加家具填充度来增加对象多样性 |
| **Object Diversity** | `obj_interior_obj_pct` | 增加对象内部对象填充度 |
| **Object Diversity** | `obj_on_storage_pct` | 增加存储对象上的对象填充度 |
| **Visual Diversity** | `painting_area_per_room_area` | 增加绘画面积来增加视觉多样性 |
| **Geometry Complexity** | `furniture_fullness_pct` | 增加家具填充度来增加几何复杂度 |

### 3. **优势**
- ✅ **兼容性**: 使用现有的约束系统
- ✅ **稳定性**: 不会导致约束求解失败
- ✅ **直接性**: 参数调整直接影响场景生成
- ✅ **简单性**: 易于理解和维护

## 实现步骤

### 1. **移除复杂约束**
- 移除所有使用`filter()`的约束
- 移除复杂的距离计算约束
- 保留现有的基础约束

### 2. **添加参数调整逻辑**
- 在`home_furniture_constraints()`中添加参数调整
- 根据SSCS目标调整现有参数
- 确保参数在有效范围内

### 3. **保持参数采样**
- 保留SSCS对齐的参数采样
- 确保贝叶斯优化器能正常工作
- 维持参数映射关系

## 预期效果

### 1. **更稳定的优化**
- 约束系统不会失败
- 场景生成过程正常进行
- 优化器能够收敛

### 2. **更直接的影响**
- 参数调整直接影响场景内容
- SSCS目标能够通过现有约束实现
- 生成场景的复杂度与目标匹配

### 3. **更好的可维护性**
- 代码更简单易懂
- 调试更容易
- 扩展性更好

## 使用建议

1. **重新运行优化**: 使用简化方法重新进行SSCS优化
2. **监控效果**: 观察参数调整是否真正影响场景复杂度
3. **调整权重**: 根据实际效果调整参数调整的权重
4. **验证结果**: 确保生成的场景SSCS值接近目标

这种方法应该能够更可靠地根据指定的SSCS生成相应复杂度的场景，而不会跳过场景生成步骤。 