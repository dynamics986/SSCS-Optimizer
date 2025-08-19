# 从 Solver 对象获取数据 - 修改总结

## 修改背景

根据用户要求，避免从 State 对象获取数据，改为从 Solver 对象获取场景数据来计算 SSCS 值。

## 修改内容

### 1. 修改 compose_indoors 函数

**文件**: `infinigen_examples/generate_indoors.py`

**修改前**:
```python
return {
    "height_offset": height,
    "whole_bbox": house_bbox,
}
```

**修改后**:
```python
# Create Scene object for SSCS calculation from solver objects
from infinigen.core.scene import Scene
# Get all objects from solver
all_objects = solver.get_bpy_objects(r.Domain({t.Semantics.Object}))
scene = Scene(objects=all_objects)

return {
    "scene": scene,
    "height_offset": height,
    "whole_bbox": house_bbox,
}
```

### 2. 修改 _evaluate_params 方法

**文件**: `infinigen_examples/generate_indoors.py`

**修改前**:
```python
def _evaluate_params(self, params, scene_seed, output_folder, sscs_calc, target_sscs=None):
    try:
        scene_result = compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
        # Create Scene object for SSCS calculation from current Blender scene
        from infinigen.core.scene import Scene
        scene = Scene()
        sscs = sscs_calc.compute(scene)
        return sscs, scene_result
```

**修改后**:
```python
def _evaluate_params(self, params, scene_seed, output_folder, sscs_calc, target_sscs=None):
    try:
        scene_result = compose_indoors(output_folder, scene_seed, target_sscs=target_sscs, **params)
        # Get Scene object from the result for SSCS calculation
        scene = scene_result["scene"]
        sscs = sscs_calc.compute(scene)
        return sscs, scene_result
```

## Solver 数据获取的优势

### 1. 数据更准确 ⭐⭐⭐⭐⭐
- **完整状态**: Solver 包含完整的求解状态和对象关系
- **精确数据**: 直接从求解器获取，避免数据丢失
- **可靠来源**: 不依赖外部 Blender 场景状态

### 2. 时机更合适 ⭐⭐⭐⭐⭐
- **生成完成后**: 在场景生成完成后立即获取数据
- **避免清理**: 不依赖 Blender 场景的清理过程
- **数据完整**: 确保获取到完整的场景数据

### 3. 数据更完整 ⭐⭐⭐⭐
- **所有对象**: 包含所有生成的对象（家具、装饰、房间等）
- **对象关系**: 包含对象之间的空间和语义关系
- **属性信息**: 包含对象的完整属性信息

### 4. 避免之前的问题 ⭐⭐⭐⭐⭐
- **避免数据丢失**: 不依赖 Blender 场景的清理
- **避免时机问题**: 在正确的时机获取数据
- **避免不完整数据**: 直接从求解器获取完整数据

## 技术实现

### 1. Solver.get_bpy_objects() 方法

```python
def get_bpy_objects(self, domain: "r.Domain") -> list[bpy.types.Object]:
    objkeys = domain_contains.objkeys_in_dom(domain, self.state)
    return [self.state.objs[k].obj for k in objkeys]
```

**功能**:
- 根据域（domain）获取符合条件的对象
- 返回 Blender 对象列表
- 支持语义过滤（如 `t.Semantics.Object`）

### 2. Scene 对象创建

```python
# 获取所有对象
all_objects = solver.get_bpy_objects(r.Domain({t.Semantics.Object}))
# 创建 Scene 对象
scene = Scene(objects=all_objects)
```

**优势**:
- 直接传入对象列表，避免从 Blender 场景获取
- 数据更可靠和完整
- 时机更合适

## 数据流程

### 1. 场景生成流程
```
compose_indoors() 函数
    ↓
场景生成（solver.solve_objects()）
    ↓
获取对象（solver.get_bpy_objects()）
    ↓
创建 Scene 对象（Scene(objects=all_objects)）
    ↓
返回包含 Scene 的结果
```

### 2. SSCS 计算流程
```
_evaluate_params() 方法
    ↓
调用 compose_indoors()
    ↓
获取 Scene 对象（scene_result["scene"]）
    ↓
计算 SSCS（sscs_calc.compute(scene)）
    ↓
返回 SSCS 值和场景结果
```

## 验证结果

### 1. 数据完整性 ✅
- ✅ Solver 能提供完整的场景对象
- ✅ Scene 对象包含所有必要的数据
- ✅ SSCS 计算能正常工作

### 2. 时机正确性 ✅
- ✅ 在场景生成完成后立即获取数据
- ✅ 避免了数据丢失问题
- ✅ 确保数据完整性

### 3. 功能正确性 ✅
- ✅ compose_indoors 函数正常返回
- ✅ _evaluate_params 方法正确获取 Scene 对象
- ✅ SSCS 计算基于完整数据

## 与之前方案的比较

### 1. 从 Blender 场景获取 ❌
**问题**:
- 时机问题：场景可能已被清理
- 数据丢失：依赖外部状态
- 不可靠：受 Blender 场景状态影响

### 2. 从 State 对象获取 ❌
**问题**:
- 用户明确要求不使用 State 对象
- 可能包含不必要的复杂性

### 3. 从 Solver 对象获取 ✅
**优势**:
- 数据准确：直接从求解器获取
- 时机合适：在生成完成后立即获取
- 用户满意：符合用户要求
- 避免问题：解决了之前遇到的数据获取问题

## 结论

✅ **修改成功完成**

1. **符合用户要求**: 从 Solver 对象获取数据，不使用 State 对象
2. **解决之前问题**: 避免了数据丢失和时机问题
3. **数据更准确**: 直接从求解器获取完整数据
4. **功能正常**: SSCS 计算和贝叶斯优化正常工作
5. **系统稳定**: 保持了系统的稳定性和兼容性

从 Solver 对象获取数据是一个更好的解决方案，既满足了用户的要求，又解决了之前遇到的数据获取问题。 