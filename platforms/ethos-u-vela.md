# Ethos-U / Vela 分析适配

适用 Ethos-U 系列；先从 SDK 确认型号、MAC 配置、Vela 版本/厂商补丁、system-config、memory-mode、优化选项和内存目标。不将某次 WE5 的通道粒度或 832 KiB 目标当作系列通用参数。

提取顺序：编译器实际帮助与配置 → 算子支持/CPU 放置报告 → 编译子图与调度 → scratch/常量内存 → TFLM allocator 和链接图 → 驱动路径。

重点检查原生 PReLU 实际降低成什么、量化重定标、group Conv 拆分、通道补齐、条带级联和权重缓存。选项/报告字段依版本变化，以本地工具为准，不能保证所有版本提供逐层时间或张量存活导出。

依据已查阅的文档，候选入口可包括 `--optimise`、`--arena-cache-size`、memory-mode 和 tensor allocator；先用本地 help 验证存在。用 schedule、allocation 和 performance 报告解释变化，不能只扫目标容量找最小估算值。当前文档针对 5.1+，不能直接作为旧 SDK 的支持证明。

内存模式需核对型号：U55 的读写与只读访问路径不同，不能照搬 U65/U85 的 Dedicated_Sram spilling。arena/cache 同属相同内存类型时也未必是两块独立分配。真正放置需同时验证链接和驱动，不能只改 ini。

Vela 估算用于筛选候选，不按总时间比例外推原始层板测。报告应分别记录 Vela 预计推理时间、实际运行 Vela 的编译耗时、编译规划 scratch、模型产物大小和目标配置；基线与候选按同一指标逐项比较。TFLM Arena 可能包含 Vela scratch 和管理对象，二者不必相等。

约束来源：

- [Arm Vela 集成文档](https://arm-software.github.io/CMSIS-Ethos-U/main/vela/index.html)
- 本地 SDK 的 Ethos-U 内核、驱动缓存回调、链接脚本及实际编译配置。

此页提供分析路径，不声称完成了任一具体 SDK 版本的支持矩阵审计。
