## 首次初始化

在codex中输入一下提示词:

```markdown

```

## 常见问题与修复

问题:
```
OPENAI_API_BASE 指向真正支持 /v1/images/generations 的兼容端点，并且 key 匹配这个端点；
或者网络能访问 https://api.openai.com/v1，并使用有效 OpenAI API key；
或者启动本地兼容网关，让它监听并支持 Image API。
```

原因用户目录下的`.codex/.env` 文件缺失导致缺少