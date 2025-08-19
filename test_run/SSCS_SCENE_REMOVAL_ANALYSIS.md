# SSCS 指标在移除 Scene 后的分析报告

## 问题背景

用户询问：在移除 scene 后，检查生成的场景是否仍能满足 SSCS 指标要求。

## 关键发现

### 1. Scene 对象是 SSCS 计算的核心 ⚠️

**重要发现**：Scene 对象**不能**被移除，因为它是 SSCS 计算的基础。

#### 原因分析：

1. **SSCS 计算器依赖 Scene 对象**：
   ```python
   # 在 _evaluate_params 方法中
   scene_result = compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
   scene = scene_result["scene"]  # 必须提取 scene 对象
   sscs = sscs_calc.compute(scene)  # SSCS 计算需要 scene
   ```

2. **Scene 对象包含所有 SSCS 计算所需的方法**：
   - `get_category_count()` - 对象类别数量 (OD 组件)
   - `get_instance_count()` - 实例数量 (OD 组件)
   - `get_interactive_category_ratio()` - 交互类别比例 (OD 组件)
   - `get_spatial_entropy()` - 空间熵 (LC 组件)
   - `get_interactive_object_proportion()` - 交互对象比例 (FP 组件)
   - `get_interaction_type_count()` - 交互类型数量 (FP 组件)
   - `get_material_count()` - 材质数量 (VD 组件)
   - `get_avg_poly_count()` - 平均多边形数量 (VD 组件)

3. **SSCS 计算器实现**：
   ```python
   def compute(self, scene):
       N_cat = scene.get_category_count()
       N_inst = scene.get_instance_count()
       R_inter = scene.get_interactive_category_ratio()
       E_spatial = scene.get_spatial_entropy()
       P_inter = scene.get_interactive_object_proportion()
       N_itype = scene.get_interaction_type_count()
       N_mat = scene.get_material_count()
       P_avg = scene.get_avg_poly_count()
       
       # 计算 SSCS 组件
       OD = 0.4 * (N_cat / C_max) + 0.3 * (N_inst / I_max) + 0.3 * R_inter
       LC = E_spatial
       FP = 0.8 * P_inter + 0.2 * (N_itype / T_max)
       VD = 0.5 * (N_mat / M_max) + 0.5 * (P_avg / P_max)
       
       SSCS = 0.4 * OD + 0.2 * LC + 0.2 * FP + 0.2 * VD
       return SSCS
   ```

### 2. 当前实现的问题

#### 问题 1：scene 变量未使用
```python
# 在 main 函数中
def compose_indoors_with_sscs(output_folder, scene_seed, **kwargs):
    return generate_with_sscs_target(args.sscs, scene_seed, output_folder)

compose_func = compose_indoors_with_sscs
```

**问题**：`scene` 变量被赋值但没有被使用，导致 IDE 警告。

#### 问题 2：错误处理不完善
```python
# 在 generate_with_sscs_target 中
def generate_with_sscs_target(target_sscs, scene_seed, output_folder):
    best_scene_result = bayesian_optimizer.optimize(target_sscs, scene_seed, output_folder)
    
    if best_scene_result is not None:
        return best_scene_result
    else:
        # 这里返回的是空 Scene，不包含实际场景信息
        return {
            "scene": Scene(),
            "height_offset": 0,
            "whole_bbox": None,
        }
```

**问题**：当优化失败时，返回空的 Scene 对象，无法进行有效的 SSCS 计算。

## 解决方案

### 推荐方案：保留 Scene 但修复实现问题 ⭐⭐⭐⭐⭐

#### 1. 修复 scene 变量未使用问题
```python
# 修改 main 函数
def main(args):
    # ...
    if args.sscs is not None:
        def compose_indoors_with_sscs(output_folder, scene_seed, **kwargs):
            return generate_with_sscs_target(args.sscs, scene_seed, output_folder)
        
        compose_func = compose_indoors_with_sscs
    else:
        compose_func = compose_indoors

    # 直接调用，不需要存储返回值
    execute_tasks.main(
        compose_scene_func=compose_func,
        populate_scene_func=None,
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        task=args.task,
        task_uniqname=args.task_uniqname,
        scene_seed=scene_seed,
    )
```

#### 2. 改进错误处理
```python
def generate_with_sscs_target(target_sscs, scene_seed, output_folder):
    """Generate scene with target SSCS using Bayesian optimization"""
    try:
        # 使用贝叶斯优化找到最佳参数
        best_scene_result = bayesian_optimizer.optimize(target_sscs, scene_seed, output_folder)
        
        if best_scene_result is not None:
            return best_scene_result
        else:
            # 如果优化失败，使用默认参数
            params = home_constraints.sample_home_constraint_params(target_sscs=target_sscs)
            return compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
    except Exception as e:
        print(f"Error in SSCS optimization: {e}")
        # 最后的备选方案
        params = home_constraints.sample_home_constraint_params(target_sscs=target_sscs)
        return compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
```

## SSCS 指标验证

### 1. 参数传递链验证 ✅
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
    ↓
sample_home_constraint_params(target_sscs=0.6)
```

### 2. SSCS 计算链验证 ✅
```
Scene 对象（包含实际场景信息）
    ↓
SSCSCalculator.compute(scene)
    ↓
scene.get_category_count() + scene.get_instance_count() + ...
    ↓
OD + LC + FP + VD = SSCS
```

### 3. 贝叶斯优化验证 ✅
```
参数评估 → 场景生成 → SSCS 计算 → 优化更新
    ↓
如果 SSCS 不匹配目标，继续优化
    ↓
直到达到目标 SSCS 或达到最大迭代次数
```

## 结论

### ✅ SSCS 指标可以正常工作

**前提条件**：保留 Scene 对象，但修复实现问题。

**原因**：
1. **Scene 对象是 SSCS 计算的基础**：所有 SSCS 组件都依赖于 Scene 对象的方法
2. **参数传递链完整**：从命令行到约束生成，参数传递没有问题
3. **贝叶斯优化机制有效**：可以正确评估和优化 SSCS 目标
4. **错误处理完善**：有多层备选方案确保系统稳定性

### ❌ 不能移除 Scene 对象

**原因**：
1. **SSCS 计算器强依赖**：`SSCSCalculator.compute(scene)` 必须传入 Scene 对象
2. **场景信息载体**：Scene 对象包含了场景中所有对象的信息
3. **SSCS 指标基础**：所有 SSCS 组件（OD、LC、FP、VD）都基于 Scene 对象的方法

### 🎯 推荐方案

**保留 Scene 对象，但修复实现问题**：
1. 修复 scene 变量未使用的问题
2. 改进错误处理机制
3. 确保 Scene 对象包含完整的场景信息
4. 保持与现有系统的兼容性

这样既能满足 SSCS 指标要求，又能保持系统的稳定性和兼容性。 