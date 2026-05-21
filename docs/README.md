# PartPipeline 文档

这里是 PartPipeline 的中文项目文档。文档按长期维护价值整理，删除了早期 phase 备忘和重复的英文说明。

## 文档列表

- [架构说明](ARCHITECTURE.md)：代码模块、外部系统边界和数据流。
- [使用指南](USAGE.md)：CLI 命令和常见工作流。
- [配置说明](CONFIGURATION.md)：profile、pipeline 参数、bridge 参数和动画参数。
- [产物说明](ARTIFACTS.md)：run、batch、bridge、presentation、animation 的输出文件。
- [环境与服务器](ENVIRONMENT.md)：SAMPart3D/HoloPart 环境策略、CUDA loader 处理和服务器运行约定。

## 推荐阅读顺序

1. 先看 [架构说明](ARCHITECTURE.md)，理解 PartPipeline 负责什么、不负责什么。
2. 再看 [使用指南](USAGE.md)，了解怎么运行单资产、批处理、打包和动画。
3. 运行前看 [配置说明](CONFIGURATION.md) 与 [环境与服务器](ENVIRONMENT.md)。
4. 调试输出时看 [产物说明](ARTIFACTS.md)。
