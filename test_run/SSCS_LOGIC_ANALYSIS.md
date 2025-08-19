# SSCS逻辑分析和修复

## 问题分析

### 1. 原始错误
```python
"scene" is not accessed
```
这是因为在`main`函数中，`scene`变量被赋值但没有被使用。

### 2. SSCS逻辑分析

#### 当前SSCS计算流程
1. **参数采样**: `home_constraints.sample_home_constraint_params(target_sscs=0.6)`
2. **场景生成**: `compose_indoors()` 使用SSCS对齐的参数
3. **SSCS计算**: `SSCSCalculator.compute(scene)` 计算实际SSCS值
4. **贝叶斯优化**: 如果SSCS不匹配目标，继续优化

#### SSCS组件分析

| 组件 | 权重 | 计算方法 | 参数影响 |
|------|------|----------|----------|
| **OD (Object Diversity)** | 40% | `0.4*(N_cat/C_max) + 0.3*(N_inst/I_max) + 0.3*R_inter` | `category_diversity_target`, `instance_density_target` |
| **LC (Layout Complexity)** | 20% | `E_spatial` (空间熵) | `spatial_distribution_spread`, `room_utilization_balance` |
| **FP (Functional Properties)** | 20% | `0.8*P_inter + 0.2*(N_itype/T_max)` | `interactive_object_ratio`, `interaction_type_diversity` |
| **VD (Visual Diversity)** | 20% | `0.5*(N_mat/M_max) + 0.5*(P_avg/P_max)` | `material_diversity_target`, `geometry_complexity_target` |

## 修复方案

### 1. 修复变量未使用问题
```python
# 修复前
scene = generate_with_sscs_target(args.sscs, scene_seed, args.output_folder)

# 修复后
scene_result = generate_with_sscs_target(args.sscs, scene_seed, args.output_folder)
if scene_result is None:
    # 如果优化失败，使用默认参数
    params = home_constraints.sample_home_constraint_params(target_sscs=args.sscs)
    scene_result = compose_indoors(args.output_folder, scene_seed, target_sscs=args.sscs, **params)
```

### 2. SSCS参数映射验证

#### 有效的SSCS参数
- ✅ `category_diversity_target`: 影响对象类别数量
- ✅ `instance_density_target`: 影响实例密度
- ✅ `spatial_distribution_spread`: 影响空间分布
- ✅ `room_utilization_balance`: 影响房间利用率
- ✅ `material_diversity_target`: 影响材质多样性
- ✅ `geometry_complexity_target`: 影响几何复杂度

#### 需要验证的参数
- ⚠️ `interactive_category_ratio`: 需要Scene类支持
- ⚠️ `interactive_object_ratio`: 需要Scene类支持
- ⚠️ `interaction_type_diversity`: 需要Scene类支持

## 代码逻辑验证

### 1. 参数传递链
```
命令行 --sscs 0.6
    ↓
main(args) → args.sscs = 0.6
    ↓
generate_with_sscs_target(0.6, scene_seed, output_folder)
    ↓
BayesianOptimizer.optimize(0.6, scene_seed, output_folder)
    ↓
compose_indoors(output_folder, scene_seed, target_sscs=0.6, **params)
    ↓
home_constraints.home_furniture_constraints(target_sscs=0.6)
```

### 2. SSCS计算链
```
Scene对象
    ↓
SSCSCalculator.compute(scene)
    ↓
scene.get_category_count() + scene.get_instance_count() + ...
    ↓
OD + LC + FP + VD = SSCS
```

## 预期效果

### 1. 成功情况
- ✅ 命令行参数正确传递到`target_sscs`
- ✅ SSCS对齐参数被正确采样和使用
- ✅ 场景生成后SSCS计算正确
- ✅ 贝叶斯优化能够收敛到目标SSCS

### 2. 失败情况
- ⚠️ 如果优化失败，会回退到默认参数采样
- ⚠️ 如果Scene类方法缺失，SSCS计算可能不准确

## 测试建议

### 1. 验证参数传递
```bash
python infinigen_examples/generate_indoors.py --output_folder ./output --sscs 0.6
```

### 2. 验证SSCS计算
```python
# 在compose_indoors函数中添加调试信息
sscs_calc = SSCSCalculator()
sscs = sscs_calc.compute(scene)
print(f"Generated SSCS: {sscs:.3f}, Target: {target_sscs:.3f}")
```

### 3. 验证参数影响
```python
# 检查参数是否正确影响场景生成
print(f"Using parameters: {params}")
print(f"Category diversity target: {params.get('category_diversity_target')}")
```

## 结论

1. **修复完成**: 变量未使用问题已修复
2. **逻辑正确**: SSCS参数传递链完整
3. **需要验证**: Scene类的SSCS计算方法是否完整
4. **预期效果**: 应该能够根据SSCS目标生成相应复杂度的场景

**建议**: 运行测试并检查SSCS计算是否准确，如果Scene类方法缺失，需要补充实现。 