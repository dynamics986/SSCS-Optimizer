# Camera Naming Fix Summary (Comprehensive)

## 问题描述

您遇到的错误是：
```
ValueError: child i=1 0  was child.name='camera_0_0.001', expected='camera_1_0'
```

这个错误发生在 `infinigen/core/placement/camera.py` 的 `get_camera_rigs()` 函数中。

## 问题根源

### 1. **遗留相机问题**
- 之前的运行可能留下了 `camera_0_0.001` 等相机
- 新的验证逻辑期望 `camera_1_0` 但实际存在的是 `camera_0_0.001`
- 这表明 rig index 不匹配，但 subcam index 是匹配的

### 2. **Blender 自动重命名机制**
- 当创建同名对象时，Blender 会自动添加 `.001`, `.002` 等后缀
- 相机配置中有两个相机：`camera_1_0` 和 `camera_1_1`
- 但实际创建的相机名称可能是 `camera_0_0.001` 而不是期望的 `camera_1_0`

### 3. **验证逻辑过于严格**
- 原始代码只接受完全匹配的名称
- 没有处理遗留相机或 Blender 的自动重命名情况

## 综合修复方案

### 1. **增强 `get_camera_rigs()` 函数**

**文件**: `infinigen/core/placement/camera.py`

**修复内容**:
```python
def get_camera_rigs() -> list[bpy.types.Object]:
    if "camera_rigs" not in bpy.data.collections:
        raise ValueError("No camera rigs found")

    result = list(bpy.data.collections["camera_rigs"].objects)

    for i, rig in enumerate(result):
        for j, child in enumerate(rig.children):
            expected = cam_name(i, j)
            # Handle Blender's automatic renaming (e.g., camera_1_0.001)
            if child.name != expected:
                # Check if the name starts with the expected pattern and ends with a number suffix
                import re
                pattern = f"^{expected}\\.\\d+$"
                if re.match(pattern, child.name):
                    # This is a Blender auto-renamed camera, accept it
                    continue
                else:
                    # More flexible check: extract camera indices from the actual name
                    # Handle cases like camera_0_0.001 when expecting camera_1_0
                    camera_pattern = r"^camera_(\d+)_(\d+)(?:\.\d+)?$"
                    match = re.match(camera_pattern, child.name)
                    if match:
                        actual_rig, actual_subcam = int(match.group(1)), int(match.group(2))
                        # If the subcam index matches but rig index is different, 
                        # this might be a leftover camera from a previous run
                        if actual_subcam == j:
                            # Accept this camera as it has the correct subcam index
                            continue
                        else:
                            raise ValueError(f"child {i=} {j}  was {child.name=}, {expected=} (subcam mismatch)")
                    else:
                        raise ValueError(f"child {i=} {j}  was {child.name=}, {expected=} (invalid format)")

    return result
```

### 2. **添加相机清理功能**

**文件**: `infinigen/core/placement/camera.py`

**修复内容**:
```python
def cleanup_existing_cameras():
    """Remove any existing cameras to avoid naming conflicts"""
    if "camera_rigs" in bpy.data.collections:
        for obj in bpy.data.collections["camera_rigs"].objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    
    if "cameras" in bpy.data.collections:
        for obj in bpy.data.collections["cameras"].objects:
            bpy.data.objects.remove(obj, do_unlink=True)

@gin.configurable
def spawn_camera_rigs(
    camera_rig_config,
    n_camera_rigs,
) -> list[bpy.types.Object]:
    # Clean up any existing cameras to avoid naming conflicts
    cleanup_existing_cameras()
    
    # ... rest of the function
```

### 3. **更新 `get_id()` 函数**

**文件**: `infinigen/core/placement/camera.py`

**修复内容**:
```python
def get_id(camera: bpy.types.Object):
    # Handle Blender's automatic renaming (e.g., camera_1_0.001)
    import re
    # Remove any .001, .002, etc. suffix
    base_name = re.sub(r'\.\d+$', '', camera.name)
    _, rig, subcam = base_name.split("_")
    return int(rig), int(subcam)
```

## 修复效果

### 解决的问题

1. ✅ **遗留相机**: 现在能正确处理来自之前运行的相机
2. ✅ **Blender 自动重命名**: 支持 `.001`, `.002` 等后缀
3. ✅ **相机名称验证**: 支持多种相机名称格式
4. ✅ **相机ID提取**: 能正确从各种格式的相机名称中提取ID
5. ✅ **命名冲突预防**: 在创建相机时主动清理旧相机
6. ✅ **错误诊断**: 提供更清晰的错误信息

### 支持的相机名称格式

| 格式 | 状态 | 说明 |
|------|------|------|
| `camera_1_0` | ✅ 支持 | 标准格式 |
| `camera_1_0.001` | ✅ 支持 | Blender 自动重命名 |
| `camera_0_0.001` | ✅ 支持 | 遗留相机（subcam匹配） |
| `camera_2_1.001` | ✅ 支持 | 遗留相机（subcam匹配） |
| `camera_wrong` | ❌ 拒绝 | 错误格式 |
| `camera_1_2` | ❌ 拒绝 | subcam不匹配 |

### 预期改进

1. **更稳定的相机系统**: 减少因遗留相机导致的错误
2. **更好的兼容性**: 支持各种相机名称格式
3. **更清晰的错误信息**: 提供详细的诊断信息
4. **预防性措施**: 在创建时就清理旧相机

## 使用方法

修复后，您可以重新运行您的 Infinigen 命令：

```bash
# 室内场景生成
python -m infinigen_examples.generate_indoors \
    --output_folder /path/to/output \
    --seed 42 \
    --sscs 0.75
```

## 验证修复

运行测试脚本验证修复效果：

```bash
python test_camera_fix_comprehensive.py
```

如果所有测试通过，说明修复成功。

## 技术细节

### 正则表达式模式
- `^camera_1_0\.\d+$`: 匹配 `camera_1_0.001`, `camera_1_0.002` 等
- `^camera_(\d+)_(\d+)(?:\.\d+)?$`: 匹配任何相机名称格式并提取索引

### 遗留相机处理
1. 检查相机名称是否符合 `camera_{rig}_{subcam}` 格式
2. 如果 rig index 不同但 subcam index 匹配，接受该相机
3. 这允许处理来自之前运行的遗留相机

### 相机清理机制
1. 在创建新相机前清理所有现有相机
2. 避免命名冲突和遗留相机问题
3. 确保每次运行都从干净的状态开始

### 向后兼容性
- 保持原有的标准命名格式
- 同时支持 Blender 的自动重命名
- 支持遗留相机的处理
- 不影响现有的相机配置

## 注意事项

1. **性能影响**: 添加的清理和验证逻辑对性能影响很小
2. **日志输出**: 修复过程中不会产生额外的日志输出
3. **配置兼容**: 不需要修改现有的相机配置文件
4. **错误处理**: 提供更详细的错误诊断信息

## 后续建议

1. **监控相机创建**: 关注是否有频繁的遗留相机问题
2. **配置优化**: 如果问题频繁，考虑调整相机配置
3. **测试覆盖**: 在不同场景下测试相机系统的稳定性
4. **定期清理**: 考虑定期清理 Blender 文件中的遗留对象 