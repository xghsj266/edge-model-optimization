# ST Neural-ART 分析适配

确认 STM32N6 的具体型号、ST Edge AI Core / Neural-ART 编译器版本、优化配置、内存描述文件和 SDK。Cortex-M55 CPU 路径与 Neural-ART NPU 路径分别分析。

从编译报告与生成代码定位 NPU epoch/执行单元、CPU 算子、存储映射、缓冲复用及外部存储访问。报告对象与原图节点不一一对应时，保留映射不确定性。

重点读目标 `.mpool` 的读写权限、吞吐/延迟与常量偏好，以及 profile 中调度和 cache 选项。虚拟池合并连续但性能不同的内存时，可能失去分别择优放置的机会；比较合并与保持分池的实际分配和流量。不要改硬件 machine descriptor 来伪造能力。

比较候选时固定内存布局与放置条件，分别记录权重、激活、运行时代码/管理开销及 CPU/NPU 边界；不能直接将编译缓冲总数当作同时存活峰值。

约束来源：[ST Neural-ART 编译器文档](https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html)、目标版本 CLI 帮助、生成代码及 STM32 SDK。链接对应版本仅为查阅入口，部署版本不同需重新核对。

此页为适配框架，尚未针对本项目完成 ST 编译或板测。
