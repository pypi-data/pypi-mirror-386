# IP 查询 MCP 服务

一个用于查询本机 IP 地址的 MCP 服务，支持：
- 内网 IP 查询
- 公网 IP 查询
- VPN 代理检测（自动区分真实 IP 和 VPN IP）

## 功能特点

### 智能 VPN 检测
- 同时查询国内和国际 IP 服务
- 如果两个服务返回的 IP 不同，说明使用了 VPN
- 自动区分真实 IP 和 VPN 代理后的 IP

### 快速响应
- 并发查询多个 IP 服务
- 返回最快响应的结果
- 超时保护（5秒）

## 安装

```bash
cd python/我的IP
pip install -e .
```

## 配置 MCP

在 Kiro 的 MCP 配置文件中添加：

### 方式 1: 使用 Python 模块
```json
{
  "mcpServers": {
    "ip-query": {
      "command": "python",
      "args": ["-m", "ip_query_mcp"],
      "disabled": false
    }
  }
}
```

### 方式 2: 使用 uvx（推荐）
如果发布到 PyPI 后：
```json
{
  "mcpServers": {
    "ip-query": {
      "command": "uvx",
      "args": ["ip-query-mcp"],
      "disabled": false
    }
  }
}
```

## 可用工具

### 1. get_ip_info
查询完整的 IP 信息，包括内网 IP、公网 IP，并自动检测 VPN。

**示例输出（未使用 VPN）：**
```
内网 IP: 192.168.1.100
公网 IP: 123.45.67.89

✓ 未检测到 VPN 代理
```

**示例输出（使用 VPN）：**
```
内网 IP: 192.168.1.100
公网 IP: 123.45.67.89

🔒 检测到 VPN 代理:
  真实 IP: 123.45.67.89
  VPN IP: 104.28.15.200
```

### 2. get_local_ip
仅查询内网 IP 地址。

### 3. get_public_ip
仅查询公网 IP 地址（不区分是否使用 VPN）。

## 工作原理

1. **内网 IP**: 通过创建 UDP socket 连接到外部地址获取本机网络接口 IP
2. **真实 IP**: 查询国内或响应快的 IP 服务（如 ipify.org）
3. **VPN IP**: 查询国际服务（如 Cloudflare CDN）
4. **VPN 检测**: 比较两个服务返回的 IP，如果不同则判定为使用了 VPN

## 技术细节

- 使用 `httpx` 进行异步 HTTP 请求
- 并发查询多个服务，返回最快的结果
- 支持多种 IP 服务响应格式（JSON、纯文本、Cloudflare trace）
- 完善的错误处理和超时保护

## 依赖

- Python >= 3.10
- mcp >= 1.0.0
- httpx >= 0.27.0

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## License

MIT
