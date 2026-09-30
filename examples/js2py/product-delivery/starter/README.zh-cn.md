# 学习者产品启动包

这是 js2py 贯穿产品的故意空白 V0 启动包。它没有业务实现、参考答案、锁文件，也不声称测试通过。

## 开始

```bash
uv python install 3.13.15
uv lock
uv sync --locked
```

此时 `pytest` 不会发现测试；这不是验收。继续写自己的产品合同和第一批业务规则。

## 必须由学习者创建的文件

自己创建这些文件：

- `docs/product-contract.md`
- `docs/integration-record.json`
- 自己的 `src/product/` 模块
- 业务与失败测试
- 之后：API 入口
- 之后：迁移与数据库测试
- 之后：发布与恢复运行入口

从交付包中把 `templates/product-contract.md` 复制为 `docs/product-contract.md` 并填写；把 `templates/integration-record.json` 复制为 `docs/integration-record.json`。两者都要提交；它们是产品文档，不是生成缓存。

生成的 `uv.lock` 属于你自己的产品。不要复制章节实验的锁文件或已安装环境；每次有意变更依赖时再更新它。

## 边界

这个启动包只固定初始责任布局，不实现任务、API、PostgreSQL、授权、异步、部署或恢复；这些都是学习者 V0—V5 的工作。
