# 候选指标 JSON 契约

当前比较仅使用静态/编译侧指标。先向用户询问优化方向，或引用用户已经明确的目标；取得回答后再创建 `objective.json`。不能依据下面的示例自动设定目标或允许代价。脚本接收目标文件，以及两份指标 JSON：`baseline.json` 和 `candidate.json`。例如用户明确选择同时降低编译器预计推理时间和规划 scratch，并允许模型大小增加最多 5% 时，可以写为：

```json
{
  "primary_metrics": {
    "estimated_inference_ms": {"direction": "minimize", "target": 100},
    "scratch_kib": {"direction": "minimize", "target": 1000}
  },
  "guardrails": {
    "model_bytes": {"direction": "minimize", "max_regression_pct": 5}
  }
}
```

主指标可只有一个，也可有多个。目标值 `target` 可省略，表示只检查是否朝指定方向改善；预设的退化上限 `max_regression_pct` 可用于其他指标。目标文件要在候选生成前定稿，保存创建时间或版本记录；不能看到结果后修改目标。数值方向使用 `minimize`／`maximize`。未声明退化上限的其他指标仍报告变化，但不判定是否可接受。`compare_candidates.py` 要求先传目标文件，再传基线和候选：

```text
python scripts/compare_candidates.py objective.json baseline.json candidate.json
```

基线和候选采用相同的顶层结构：

```json
{
  "identity": {
    "name": "candidate-name",
    "model_sha256": "64-character-sha256",
    "target": "chip-and-npu",
    "toolchain": "compiler-and-runtime-version",
    "measurement": "compiler",
    "input_set": "112x112x3-int8",
    "timing_scope": "compiler-estimated-inference",
    "clock_hz": 400000000
  },
  "metrics": {
    "estimated_inference_ms": 95,
    "scratch_kib": 826,
    "model_bytes": 1048576
  }
}
```

`identity` 各字段必须存在且为非空字符串，唯 `clock_hz` 为正整数。`model_sha256` 表示模型产物；可对不同模型比较，因此允许两边不同，但需要记录。`target`、`toolchain`、`measurement`、`input_set`、`timing_scope` 和 `clock_hz` 必须相同，否则脚本拒绝计算差值。当前 `measurement` 固定为 `compiler`，`input_set` 填相同输入契约标识，`clock_hz` 填估算使用的目标时钟。示例数值仅说明格式，不代表任何已编译模型。

`metrics` 数值可选，但至少有一项。只比较两边共有且有限的数值：

| 字段 | 含义 | 适用记录 |
|---|---|---|
| `estimated_inference_ms` | 编译器预计的模型推理时间 | compiler |
| `compile_elapsed_s` | 实际运行编译命令的墙钟时间 | compiler |
| `scratch_kib`、`peak_ram_kib` | 编译规划工作区与峰值 RAM；使用报告的精确定义 | compiler |
| `cpu_ops`、`npu_ops` | 编译后算子/执行单元数量；两侧需同口径 | compiler |
| `model_bytes` | 指定模型文件的字节数，双方文件类型须一致 | compiler |
| `memory_traffic_bytes`、`macs`、`constant_bytes` | 编译报告的访存量估算、MACs、常量存储；分别使用同一字段定义 | compiler |

缺失指标输出“未比较”。若包含 `compile_elapsed_s`，两侧还必须提供相同的 `identity.compile_host`、`identity.build_state`（例如 clean/warm）和 `identity.compile_timing_scope`；不相同则拒绝计算差值。仅填这些字段不能保证编译工作负载完全一致，仍须人工检查命令与环境。

脚本先输出主目标的变化和达标情况，再输出其他指标的变化及已声明的退化限制是否被突破。缺失指标标为无法判断；达标仅表示满足编译侧目标。脚本不做统计显著性检验，也不判断精度或正确性。它比较已整理的数值，不能从 Vela 日志自动提取数据。
