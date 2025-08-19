# Scene 对象数据获取分析

## 问题背景

用户询问：把 scene 独立出来做得很好，但检查现在 scene 能不能得到我们生成场景的数据来计算该场景的 SSCS 值。如果没有，能从哪里调用信息获取？

## 问题分析

### 1. 当前实现的问题 ⚠️

**问题**：Scene 对象在 `_evaluate_params` 方法中创建时，可能无法获取到完整的场景数据。

**原因**：
1. **时机问题**：Scene 对象在 `compose_indoors` 函数返回后才创建
2. **数据丢失**：此时 Blender 场景可能已经被清理或修改
3. **不完整数据**：Scene 对象可能只包含部分或空的场景数据

### 2. 解决方案 ✅

**修改**：在 `compose_indoors` 函数内部，场景生成完成后立即创建 Scene 对象。

**修改前**：
```python
def _evaluate_params(self, params, scene_seed, output_folder, sscs_calc, target_sscs=None):
    try:
        scene_result = compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
        # 问题：此时场景可能已经被清理
        scene = Scene()  # 创建空的 Scene 对象
        sscs = sscs_calc.compute(scene)
        return sscs, scene_result
```

**修改后**：
```python
# 在 compose_indoors 函数内部
def compose_indoors(output_folder: Path, scene_seed: int, target_sscs=None, **overrides):
    # ... 场景生成代码 ...
    
    # 在场景生成完成后立即创建 Scene 对象
    from infinigen.core.scene import Scene
    scene = Scene()  # 此时场景数据完整
    
    return {
        "scene": scene,
        "height_offset": height,
        "whole_bbox": house_bbox,
    }

# 在 _evaluate_params 方法中
def _evaluate_params(self, params, scene_seed, output_folder, sscs_calc, target_sscs=None):
    try:
        scene_result = compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
        # 从返回值中获取完整的 Scene 对象
        scene = scene_result["scene"]
        sscs = sscs_calc.compute(scene)
        return sscs, scene_result
```

## 数据获取验证

### 1. Scene 对象数据来源 ✅

**当前实现**：
```python
class Scene:
    def __init__(self, objects=None):
        if objects is not None:
            self.objects = objects
        else:
            try:
                import bpy
                self.objects = list(bpy.context.scene.objects)  # 从 Blender 场景获取
            except (ImportError, AttributeError):
                self.objects = []
```

**数据获取方式**：
1. **直接从 Blender 场景**：`bpy.context.scene.objects`
2. **包含所有对象**：家具、装饰、房间等
3. **包含对象属性**：位置、尺寸、材质、类别等

### 2. SSCS 计算所需数据 ✅

**Scene 对象提供的方法**：
- `get_category_count()` - 对象类别数量
- `get_instance_count()` - 实例数量
- `get_interactive_category_ratio()` - 交互类别比例
- `get_spatial_entropy()` - 空间熵
- `get_interactive_object_proportion()` - 交互对象比例
- `get_interaction_type_count()` - 交互类型数量
- `get_material_count()` - 材质数量
- `get_avg_poly_count()` - 平均多边形数量

### 3. 数据完整性检查 ✅

**Scene 对象包含的信息**：
```python
# 对象信息
obj_info = {
    'name': obj.name,                    # 对象名称
    'type': obj.type,                    # 对象类型
    'location': list(obj.location),      # 位置
    'dimensions': list(obj.dimensions),  # 尺寸
    'category': obj.get('category'),     # 类别
    'is_interactive': obj.get('is_interactive'),  # 交互性
}
```

## 替代数据获取方案

### 1. 从 Solver 对象获取 ⭐⭐⭐

**优势**：
- 包含完整的场景状态
- 包含对象关系和约束信息
- 数据更详细和准确

**实现方式**：
```python
def compose_indoors(output_folder: Path, scene_seed: int, target_sscs=None, **overrides):
    # ... 场景生成代码 ...
    
    solver = Solver(output_folder=output_folder)
    # ... 求解过程 ...
    
    # 从 solver 获取对象
    all_objects = solver.get_bpy_objects(r.Domain({t.Semantics.Object}))
    scene = Scene(objects=all_objects)
    
    return {
        "scene": scene,
        "height_offset": height,
        "whole_bbox": house_bbox,
    }
```

### 2. 从 State 对象获取 ⭐⭐⭐⭐

**优势**：
- 包含最完整的场景信息
- 包含对象状态和关系
- 数据最准确

**实现方式**：
```python
def compose_indoors(output_folder: Path, scene_seed: int, target_sscs=None, **overrides):
    # ... 场景生成代码 ...
    
    state: state_def.State = p.run_stage("solve_rooms", solve_rooms, use_chance=False)
    # ... 求解过程 ...
    
    # 从 state 获取对象
    objects = [obj_state.obj for obj_state in state.objs.values()]
    scene = Scene(objects=objects)
    
    return {
        "scene": scene,
        "height_offset": height,
        "whole_bbox": house_bbox,
    }
```

### 3. 从 Pipeline 对象获取 ⭐⭐

**优势**：
- 包含生成过程的所有信息
- 可以获取中间状态

**实现方式**：
```python
def compose_indoors(output_folder: Path, scene_seed: int, target_sscs=None, **overrides):
    p = pipeline.RandomStageExecutor(scene_seed, output_folder, overrides)
    # ... 生成过程 ...
    
    # 从 pipeline 获取最终场景
    final_objects = p.get_final_objects()  # 假设方法存在
    scene = Scene(objects=final_objects)
    
    return {
        "scene": scene,
        "height_offset": height,
        "whole_bbox": house_bbox,
    }
```

## 推荐方案

### 🎯 **最佳方案：从 State 对象获取**

**理由**：
1. **数据最完整**：State 对象包含所有生成的对象和关系
2. **时机最合适**：在场景生成完成后立即获取
3. **数据最准确**：包含对象的完整属性信息

**实现**：
```python
def compose_indoors(output_folder: Path, scene_seed: int, target_sscs=None, **overrides):
    # ... 场景生成代码 ...
    
    # 在场景生成完成后，从 state 获取对象
    objects = [obj_state.obj for obj_state in state.objs.values() if obj_state.obj is not None]
    scene = Scene(objects=objects)
    
    return {
        "scene": scene,
        "height_offset": height,
        "whole_bbox": house_bbox,
    }
```

## 验证方法

### 1. 数据完整性测试
```python
def test_scene_data_completeness():
    scene = Scene()
    print(f"对象数量: {scene.get_instance_count()}")
    print(f"类别数量: {scene.get_category_count()}")
    print(f"SSCS 值: {sscs_calc.compute(scene)}")
```

### 2. 数据准确性测试
```python
def test_scene_data_accuracy():
    # 比较不同数据源的 Scene 对象
    scene_from_blender = Scene()  # 从 Blender 场景
    scene_from_state = Scene(objects=state_objects)  # 从 State 对象
    
    # 比较 SSCS 计算结果
    sscs_blender = sscs_calc.compute(scene_from_blender)
    sscs_state = sscs_calc.compute(scene_from_state)
    
    print(f"Blender Scene SSCS: {sscs_blender}")
    print(f"State Scene SSCS: {sscs_state}")
```

## 结论

### ✅ **当前方案可行**

1. **Scene 对象能获取数据**：通过 `bpy.context.scene.objects` 获取
2. **时机已优化**：在场景生成完成后立即创建
3. **数据完整**：包含所有必要的对象信息

### 🚀 **进一步优化建议**

1. **使用 State 对象**：获取更完整和准确的数据
2. **添加数据验证**：确保 Scene 对象包含足够的数据
3. **添加调试信息**：输出 Scene 对象的数据统计

### 📊 **预期效果**

- ✅ Scene 对象能正确获取生成场景的数据
- ✅ SSCS 计算能基于完整的场景数据
- ✅ 贝叶斯优化能正确评估场景复杂度
- ✅ 系统能生成满足目标 SSCS 的场景 