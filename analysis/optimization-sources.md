# 经验来源与适用范围

查阅日期：2026-10-15。以下是分析依据与方法入口，不是已经移植、实现或板测的功能。保存本地使用版本/提交和对应章节；滚动文档不能替代目标 SDK 的实际能力。

## 最高优先：Arm Vela

[文档](https://arm-software.github.io/CMSIS-Ethos-U/main/vela/index.html)，重点：Feature overview、Select a memory mode、Understand arena cache and spilling、Read the Vela reports。当前页面说明覆盖 Vela 5.1 及以后。

吸收：striping/cascading、常量/arena/cache 映射、工作区预算和暂存取舍。落地分析：对照 schedule、allocation 和流量报告，检查预算变化是否改变整幅物化或权重暂存。不要把 cache 预算当作物理内存自动配置；编译映射必须与链接及驱动一致。U55 与 U65/U85 的可用 memory mode 不相同，按目标版本核对。

## 最高优先：ST Neural-ART

[Primer](https://stedgeai-dc.st.com/assets/embedded-docs/stneuralart_neural_art_compiler.html)，重点：Memory-pools、optimization options、compilation profiles。

吸收：将可用内存、访问权限和性能描述给编译器，比较放置与调度。特别检查合并异质 memory pool 是否丢失快慢差异。其选项及内存优先规则限于 ST；可迁移的是“模型访问需求与真实内存拓扑联合优化”的方法。

## 最高优先：TinyEngine / MCUNet

[仓库](https://github.com/mit-han-lab/tinyengine)，重点：优化技术、code_generator、TinyEngine 内核及 patch-based inference。

吸收：面向全图拓扑的内存调度、patch 推理、in-place depthwise 和融合。先检查目标执行后端能否表达同样的数据依赖；CPU C 内核不等于可替换的 NPU 指令流。分块可能引入 halo 重算和搬运，原地执行需证明没有破坏后续读。仓库示例的收益不能直接用于 WE5 估算。

## 高优先：ExecuTorch

[内存规划](https://docs.pytorch.org/executorch/stable/compiler-memory-planning.html)及[实现](https://github.com/pytorch/executorch/blob/main/exir/memory_planning.py)，重点：MemoryPlanningPass、Algorithms、Method Inputs and Outputs、Custom Memory Plans。

吸收：按存活区间复用、分池规划和 IO 外置以避免复制。判断复用必须同时满足时间不重叠、尺寸/对齐和设备可访问性；文档表述含混时核对实现。delegate 内部 scratch 需从后端补充，不把主图 planner 视为完整 NPU 峰值。API 和内存池编号规则限于相应版本。

## 高优先：TensorRT

[11.4 性能指南](https://docs.nvidia.com/deeplearning/tensorrt/11.4.0/performance/optimization.html)及[融合目录](https://docs.nvidia.com/deeplearning/tensorrt/11.4.0/performance/fusion-catalog.html)，重点：Enabling Layer Fusion、Optimizing Layer Performance。

吸收：用编译后的融合、格式转换和物理形状解释性能；不按原图层数判断收益。其 Tensor Core 对齐、kernel 启动开销和 tactics 规则属于 GPU 后端，不转写为 Ethos-U 约束。

## 补充：onnx2tf

[README](https://github.com/PINTO0309/onnx2tf/blob/main/README.md)，重点搜索：transpose passthrough、affine fold、PReLU、rtpo、accuracy validation。

吸收：跟踪转换产生的冗余 transpose、轴重映射和算子展开；历史 PReLU primitive 替换属于特定兼容性处理，恢复时先排除原问题。当前 README 默认路径已不同于旧 tf_converter，因此必须匹配本地转换器版本与实际参数，不为查资料自动升级工具链。
