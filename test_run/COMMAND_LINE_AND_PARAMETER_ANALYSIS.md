# 命令行参数传递和参数定义分析

## 问题分析

你询问了三个关键问题：
1. 命令行的 `--sscs` 参数是否能被正确传入 `target_sscs`
2. `target_sscs` 参数是否能被正确传递
3. `category_diversity_target` 等参数是否被正确定义（IDE 显示白色字体）

## 分析结果

### 1. 命令行 `--sscs` 参数传递 ✅

**答案：是的，命令行参数能正确传递**

**证据：**
- 在 `infinigen_examples/generate_indoors.py` 第 847 行定义了 `--sscs` 参数：
```python
parser.add_argument("--sscs", type=float, default=None, help="Target SSCS score (0~1)")
```

- 在 `main` 函数中正确处理：
```python
def main(args):
    # ...
    if args.sscs is not None:
        scene = generate_with_sscs_target(args.sscs, scene_seed, args.output_folder)
    else:
        params = home_constraints.sample_home_constraint_params()
        scene = compose_indoors(args.output_folder, scene_seed, target_sscs=None, **params)
```

**测试验证：**
```bash
# 测试命令
python infinigen_examples/generate_indoors.py --output_folder ./output --sscs 0.6
```

### 2. `target_sscs` 参数传递 ✅

**答案：是的，`target_sscs` 参数能正确传递**

**传递链：**
1. 命令行 `--sscs 0.6` → `args.sscs = 0.6`
2. `generate_with_sscs_target(args.sscs, ...)` → `target_sscs=0.6`
3. `compose_indoors(..., target_sscs=0.6, ...)` → 传递给约束函数
4. `home_furniture_constraints(target_sscs=0.6)` → 传递给参数采样
5. `sample_home_constraint_params(target_sscs=0.6)` → 生成目标参数

**代码证据：**
```python
# generate_indoors.py line 152
def compose_indoors(output_folder: Path, scene_seed: int, target_sscs=None, **overrides):

# home.py line 700
def home_furniture_constraints(target_sscs=None):

# home.py line 86
def sample_home_constraint_params(target_sscs=None):
```

### 3. `category_diversity_target` 参数定义 ✅

**答案：是的，参数被正确定义，IDE 白色字体可能是显示问题**

**参数定义位置：**

1. **在 `home.py` 第 104 行**：
```python
def _random_sample_params():
    return dict(
        category_diversity_target=np.random.uniform(0.1, 0.8),
        instance_density_target=np.random.uniform(0.2, 1.0),
        # ... 其他参数
    )
```

2. **在 `home.py` 第 145 行**：
```python
def linear_interpolation(target_sscs):
    return dict(
        category_diversity_target=interp(0.1, 0.8, alpha_final),
        instance_density_target=interp(0.2, 1.0, alpha_final),
        # ... 其他参数
    )
```

3. **在 `home.py` 第 179 行**：
```python
def _bayesian_optimization_sample(target_sscs):
    param_dict = {
        'category_diversity_target': np.random.uniform(0.1, 0.8),
        'instance_density_target': np.random.uniform(0.2, 1.0),
        # ... 其他参数
    }
```

4. **在 `home.py` 第 813 行使用**：
```python
if 'category_diversity_target' in params:
    adjusted_furniture_fullness = params["furniture_fullness_pct"] * (1 + params["category_diversity_target"] * 0.3)
```

**IDE 白色字体问题分析：**

IDE 显示白色字体可能的原因：
1. **导入路径问题**：IDE 可能没有正确识别模块路径
2. **缓存问题**：IDE 的语法高亮缓存需要刷新
3. **项目配置问题**：IDE 的项目设置可能需要调整

**解决方案：**
1. 重启 IDE
2. 重新加载项目
3. 清除 IDE 缓存
4. 检查 Python 解释器设置

## 测试验证结果

我们创建了测试脚本验证所有功能：

```bash
python test_run/test_parameter_definitions_simple.py
```

**测试结果：**
- ✅ 命令行参数解析正确
- ✅ `target_sscs` 参数传递正确
- ✅ `category_diversity_target` 等参数定义正确
- ✅ 参数使用逻辑正确

## 完整的工作流程

1. **命令行输入**：
   ```bash
   python generate_indoors.py --output_folder ./output --sscs 0.6
   ```

2. **参数解析**：
   ```python
   args.sscs = 0.6  # 从命令行解析
   ```

3. **参数传递**：
   ```python
   generate_with_sscs_target(args.sscs, scene_seed, output_folder)
   ↓
   compose_indoors(output_folder, scene_seed, target_sscs=0.6, **params)
   ↓
   home_furniture_constraints(target_sscs=0.6)
   ↓
   sample_home_constraint_params(target_sscs=0.6)
   ```

4. **参数生成**：
   ```python
   params = {
       'category_diversity_target': 0.47678847787393663,
       'instance_density_target': 0.7333333333333332,
       'interactive_category_ratio': 0.6333333333333332,
       # ... 其他参数
   }
   ```

5. **参数使用**：
   ```python
   if 'category_diversity_target' in params:
       adjusted_furniture_fullness = params["furniture_fullness_pct"] * (1 + params["category_diversity_target"] * 0.3)
   ```

## 结论

1. **命令行 `--sscs` 参数**：✅ 能正确传入 `target_sscs`
2. **`target_sscs` 参数传递**：✅ 能正确传递到所有相关函数
3. **`category_diversity_target` 参数定义**：✅ 已正确定义，IDE 白色字体是显示问题

**建议：**
- 重启 IDE 或重新加载项目来解决白色字体问题
- 参数定义和传递逻辑都是正确的
- 可以放心使用 `--sscs` 命令行参数 