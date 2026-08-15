---
name: audit-base
description: 网站审计基础技能, 侦察, 端口扫描, http信息探测, 安全审计的流程,方法,和技巧.
---


# 背景

本机通常已经预先安装了相关命令, 可以使用`go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest`类似的命令安装相关软件包.

# 数据和文档

数据文档是随着每一次任务迭代不断修正和叠加的数据文档,表示整体的工作进度和结果.

- [资产文档](./data_assets.md)
- [侦察文档](./data_recon.md)
- [端口扫描文档](./data_port-scan.md)
- [笔记文档](./data_notes.md) 笔记用于记录综合信息,所有其他未分类的数据都记录在这里.
- [todo文档](./todo.md) todo用于记录待办事项,所有未完成的任务都记录在这里.

# 侦察的阶段以及步骤

一般按以下步骤进行, 根据实际情况决定具体决定顺序

1. [子域名信息发现] - 使用`subfinder`
2. [dns信息查询] - 使用`dnsx`命令
3. [端口扫描] - `naabu`, 例子 `naabu -host hackerone.com`
4. [http信息探测] - [`httpx`](https://github.com/projectdiscovery/httpx)

# 环境和工具

允许使用的工具包括(但不限于)

- `nuclei`
- `subfinder`
- `dnsx`
- `naabu`
- `httpx`

# 动态脚本执行

推荐通过 python, bash, js 等动态脚本的方式来完成组合任务, 将程序运行的结果最终保存到约定的数据文档中.

# 工具安装

```
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
```

https://github.com/adysec/nuclei_poc 自动收录全网 nuclei 模板文件，目前已经 19 万了.



## 自动化渗透流程和提示词模板

[Nuclei-AI-Prompts](https://github.com/reewardius/Nuclei-AI-Prompts)


## 网络空间搜索提供商

- fofa.info