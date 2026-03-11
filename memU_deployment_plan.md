# MemU 完整部署方案C

**目标**：完整部署 memU 框架，替换/增强 OpenClaw 现有记忆系统  
**时间**：2026-03-02  
**负责人**：小虾米 (James Dong 的 AI 助手)

## 📋 部署概览

### 1. 当前状态评估
- ✅ memU 源码已下载到 `/tmp/memU_test/` (最新版本 1.4.0)
- ✅ Python 环境：Python 3.13+ (需要确认)
- ⚠️ Rust 工具链：未安装
- ⚠️ memU Python 包：未安装
- ⚠️ 编译工具：部分安装 (gcc, make)
- ✅ 现有记忆系统：OpenClaw workspace 记忆文件完整

### 2. 完整部署步骤

#### 阶段1：环境准备与依赖安装 (预计 10-15 分钟)
1. 安装 Python 开发头文件
2. 安装 Rust 工具链 (rustup + cargo)
3. 安装 maturin (Rust-Python 构建工具)
4. 安装其他系统依赖

#### 阶段2：memU 核心编译与安装 (预计 5-10 分钟)
1. 编译 `memu._core` Rust 扩展
2. 安装 memU Python 包
3. 验证编译成功

#### 阶段3：数据库与嵌入器配置 (预计 5-10 分钟)
1. 配置 SQLite 数据库
2. 配置 Ollama 嵌入器 (nomic-embed-text)
3. 验证连接

#### 阶段4：记忆数据迁移 (预计 5-10 分钟)
1. 备份现有记忆文件
2. 运行 `import_memory_to_memu.py`
3. 验证数据导入

#### 阶段5：OpenClaw 集成 (预计 10-15 分钟)
1. 修改 OpenClaw 配置文件
2. 测试记忆检索功能
3. 配置自动记忆更新

### 3. 风险评估与回退方案

#### 高风险点
1. **Rust 编译失败**
   - 原因：依赖缺失、版本冲突
   - 应对：使用预编译包 (方案B)，手动安装 `memu-py`

2. **Ollama 连接失败**
   - 原因：服务未运行、模型未下载
   - 应对：使用本地嵌入器或临时禁用

3. **数据迁移失败**
   - 原因：格式不兼容、权限问题
   - 应对：保留现有记忆系统，memU 作为辅助

#### 回退方案
- **完整回退**：保留现有 `AGENTS.md`/`MEMORY.md` 系统
- **渐进迁移**：新旧系统并行运行一段时间
- **数据备份**：部署前创建完整工作空间快照

### 4. 资源需求

#### 硬件要求
- 内存：≥ 2GB (Rust 编译需要)
- 磁盘：≥ 1GB (memU 数据库 + 模型)
- CPU：支持 SSE4.2 (现代 x86-64)

#### 软件要求
- Python 3.13+ (memU 要求)
- Rust 1.75+ (Cargo)
- SQLite 3.35+
- Ollama 0.5+ (可选，推荐)

### 5. 验证测试清单

部署完成后验证：
- [ ] `python3 -c "import memu._core"` 无错误
- [ ] `python3 -c "from memu.app import MemoryService"` 成功
- [ ] SQLite 数据库文件创建成功
- [ ] 记忆导入脚本能读取现有文件
- [ ] 基本记忆存储/检索功能正常
- [ ] OpenClaw 能通过 memU 查询记忆

### 6. 时间规划

| 阶段 | 预计时间 | 状态 |
|------|----------|------|
| 1. 环境准备 | 10-15 分钟 | ⏳ 待开始 |
| 2. 核心编译 | 5-10 分钟 | ⏳ 待开始 |
| 3. 数据库配置 | 5-10 分钟 | ⏳ 待开始 |
| 4. 数据迁移 | 5-10 分钟 | ⏳ 待开始 |
| 5. OpenClaw 集成 | 10-15 分钟 | ⏳ 待开始 |
| **总计** | **35-60 分钟** | |

### 7. 开始部署

准备好后，按顺序执行以下步骤。

---

## 🔧 阶段1：环境准备与依赖安装

### 步骤 1.1：检查并安装 Python 开发依赖

```bash
# 检查 Python 版本
python3 --version

# 安装 Python 开发头文件
apt update && apt install -y python3-dev python3-pip python3-venv

# 检查 python3-config
which python3-config
```

### 步骤 1.2：安装 Rust 工具链

```bash
# 安装 rustup (官方推荐方式)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# 配置环境变量
source $HOME/.cargo/env

# 验证安装
rustc --version
cargo --version
```

### 步骤 1.3：安装 maturin 和构建工具

```bash
# 安装 maturin
pip install maturin

# 安装其他构建依赖
apt install -y build-essential pkg-config libssl-dev
```

### 步骤 1.4：检查系统资源

```bash
# 检查内存和磁盘
free -h
df -h /
```

---

## 🛠️ 阶段2：memU 核心编译与安装

### 步骤 2.1：编译 memu._core

```bash
cd /tmp/memU_test

# 开发模式编译安装 (推荐测试)
maturin develop

# 或构建 release 版本
maturin build --release

# 安装生成的 wheel 包
pip install target/wheels/memu_py-*.whl
```

### 步骤 2.2：验证安装

```bash
# 测试导入
python3 -c "import memu; print('✅ memu 导入成功')"

# 测试核心模块
python3 -c "import memu._core; print('✅ _core 导入成功')"

# 测试完整功能
python3 -c "
from memu.app import MemoryService
print('✅ MemoryService 导入成功')
"
```

---

## 🗄️ 阶段3：数据库与嵌入器配置

### 步骤 3.1：配置 SQLite 数据库

```bash
# 创建数据库目录
mkdir -p /root/.openclaw/workspace/memu_data
```

配置代码 (在 `memu_config.py` 中)：
```python
config = {
    "storage": {
        "type": "sqlite",
        "path": "/root/.openclaw/workspace/memu_data/memu.db"
    },
    "embedder": {
        "type": "ollama",
        "model": "nomic-embed-text:latest",
        "base_url": "http://localhost:11434"
    },
    "auto_classify": True,
    "auto_cross_reference": True
}
```

### 步骤 3.2：安装和配置 Ollama (可选但推荐)

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 启动 Ollama 服务
ollama serve &

# 下载嵌入模型
ollama pull nomic-embed-text:latest
```

如果 Ollama 不可用，可使用本地嵌入器：
```python
config["embedder"] = {
    "type": "local",  # 或使用其他支持的嵌入器
    "model": "local_mini"
}
```

---

## 📦 阶段4：记忆数据迁移

### 步骤 4.1：备份现有记忆系统

```bash
# 创建完整备份
cd /root/.openclaw/workspace
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    AGENTS.md SOUL.md USER.md MEMORY.md TOOLS.md \
    memory/ tasks/ skills/ .learnings/
```

### 步骤 4.2：运行记忆导入脚本

```bash
cd /root/.openclaw/workspace
python3 import_memory_to_memu.py
```

### 步骤 4.3：验证数据导入

```bash
# 检查导入日志
ls -la memory_import_plan/
cat memory_import_plan/import_log.json | jq .
```

---

## 🔗 阶段5：OpenClaw 集成

### 步骤 5.1：创建 memU 集成模块

创建 `/root/.openclaw/workspace/memU_integration.py`：
```python
"""
MemU 与 OpenClaw 集成模块
"""

import os
from pathlib import Path
from memu.app import MemoryService

class OpenClawMemUIntegration:
    """OpenClaw 记忆系统集成"""
    
    def __init__(self):
        self.workspace_path = Path("/root/.openclaw/workspace")
        self.config = self._load_config()
        self.memory_service = None
        
    def _load_config(self):
        """加载 memU 配置"""
        return {
            "storage": {
                "type": "sqlite",
                "path": str(self.workspace_path / "memu_data" / "memu.db")
            },
            "embedder": {
                "type": "ollama",
                "model": "nomic-embed-text:latest",
                "base_url": "http://localhost:11434"
            },
            "auto_classify": True,
            "auto_cross_reference": True
        }
    
    async def initialize(self):
        """初始化 memU 服务"""
        self.memory_service = MemoryService(config=self.config)
        return True
    
    async def query_memory(self, query: str, limit: int = 5):
        """查询记忆"""
        if not self.memory_service:
            await self.initialize()
        
        results = await self.memory_service.recall(query, limit=limit)
        return results
    
    async def store_memory(self, content: str, metadata: dict = None):
        """存储新记忆"""
        if not self.memory_service:
            await self.initialize()
        
        if metadata is None:
            metadata = {"source": "openclaw_agent"}
        
        memory_id = await self.memory_service.memorize(content, metadata=metadata)
        return memory_id
```

### 步骤 5.2：修改 OpenClaw 配置文件

更新 `AGENTS.md` 添加 memU 集成部分。

### 步骤 5.3：测试集成功能

创建测试脚本验证功能。

---

## 🧪 验证与测试

### 功能测试清单
- [ ] 编译成功：`import memu._core`
- [ ] 服务初始化：`MemoryService` 可创建
- [ ] 数据库连接：SQLite 文件创建成功
- [ ] 嵌入器工作：Ollama 响应正常
- [ ] 记忆存储：能保存新记忆
- [ ] 记忆检索：能查询相关记忆
- [ ] 数据迁移：现有记忆导入成功
- [ ] 集成测试：OpenClaw 能使用 memU

### 性能测试
- 查询响应时间：< 1秒
- 存储吞吐量：> 10条/秒
- 内存占用：< 500MB

---

## 🚨 故障排除

### 常见问题

1. **Rust 编译失败**
   ```
   error: linking with `cc` failed
   ```
   解决：`apt install build-essential`

2. **Python 头文件缺失**
   ```
   fatal error: Python.h: No such file or directory
   ```
   解决：`apt install python3-dev`

3. **Ollama 连接失败**
   ```
   Connection refused
   ```
   解决：`ollama serve` 或使用本地嵌入器

4. **SQLite 权限问题**
   ```
   unable to open database file
   ```
   解决：确保目录可写权限

### 紧急回退

如果部署失败，恢复原有系统：
```bash
# 恢复备份
cd /root/.openclaw/workspace
tar -xzf backup_*.tar.gz

# 移除 memU 相关文件
rm -rf memu_data/ memory_import_plan/
```

---

## 📈 后续优化

### 短期优化 (1周内)
1. 性能调优：查询缓存、批量操作
2. 监控集成：健康检查、指标收集
3. 自动化：定时记忆整理、垃圾回收

### 中期规划 (1个月内)
1. 高级功能：记忆关联分析、意图预测
2. 多模态：支持图片、文档记忆
3. 分布式：多节点记忆同步

### 长期愿景 (3个月内)
1. 完全替换：memU 成为主记忆系统
2. 智能代理：基于记忆的主动建议
3. 生态系统：插件化扩展接口

---

## 📝 部署日志

### 开始时间
2026-03-02 08:30 UTC

### 阶段完成记录

#### ✅ 阶段1：环境准备 (完成时间: 08:45)
- [x] 检查系统环境：OpenCloudOS 9.4, Python 3.11.6
- [x] 安装开发依赖：python3-devel, openssl-devel, gcc, make
- [x] 安装 Rust 工具链：rustc 1.93.1, cargo 1.93.1
- [x] 安装 maturin：1.12.6

#### ⚠️ 阶段2：核心编译 (部分完成)
- [x] 编译成功：生成 wheel 包 `memu_py-1.4.0-cp311-cp311-manylinux_2_34_x86_64.whl`
- [x] 修改 Python 版本要求：`>=3.13` → `>=3.11`
- [x] 重新编译成功
- [x] 安装 wheel 包（跳过依赖）
- [ ] **遇到问题**：导入失败，未定义符号 `PyErr_SetRaisedException`
  - **原因**：memU 使用了 Python 3.13 特有的 API
  - **影响**：无法在 Python 3.11 上运行 memU
- [ ] **解决方案**：使用 pyenv 安装 Python 3.13

#### ✅ 阶段2.1：pyenv 环境准备 (完成时间: 09:15)
- [x] 安装编译依赖：gcc, make, zlib-devel, bzip2-devel, readline-devel, sqlite-devel, libffi-devel, ncurses-devel
- [x] 安装 pyenv：2.6.23
- [x] 安装 Python 3.13.0：成功编译安装
- [x] 创建虚拟环境：memu_env (Python 3.13.0)
- [x] 安装基础依赖：maturin, numpy, httpx, pydantic, sqlmodel
- [x] 重新编译 memU：成功生成 wheel 包 `memu_py-1.4.0-cp313-abi3-manylinux_2_34_x86_64.whl`

#### ✅ 阶段2.2：memU 安装与验证 (完成时间: 10:30)
- [x] 安装 memU 完整包：pip install wheel包成功
- [x] 验证核心导入：`import memu` ✅
- [x] 验证核心模块：`import memu._core` ✅
- [x] 验证服务类：`from memu.app import MemoryService` ✅
- [x] **Python 3.13兼容性问题已解决**：pyenv环境运行正常

#### ✅ 阶段3：数据库与嵌入器配置 (完成时间: 10:40)
- [x] SQLite 数据库配置：`/root/.openclaw/workspace/memu_data/memu.db`
- [x] Ollama 嵌入器配置：nomic-embed-text:latest 模型可用
- [x] 配置文件生成：`memu_config.py`
- [x] **API探索**：发现正确的memory_type值：'profile', 'event', 'knowledge', 'behavior', 'skill', 'tool'
- [ ] **数据库文件尚未创建**：等待成功创建第一个记忆项

### 遇到的问题与解决

#### 问题1：Python 版本不兼容
**详情**：
- memU 要求 Python ≥3.13，系统为 Python 3.11.6
- 修改版本要求后编译成功，但运行时出现未定义符号错误
- `PyErr_SetRaisedException` 是 Python 3.13 引入的 API

**可能的解决方案**：
1. **升级 Python 到 3.13+**：使用 pyenv 从源码编译（耗时 30-60 分钟）
2. **使用 Docker 容器**：在容器中运行 memU，通过 API 交互（需要网络配置）
3. **寻找兼容版本**：尝试 memU 早期版本（如 1.3.0），可能支持 Python 3.11
4. **修改 memU 源码**：替换不兼容的 API 调用（高风险，可能引入错误）

**建议**：方案1（pyenv）最直接，但耗时较长。

### 当前状态 (更新时间: 2026-03-02 10:30 UTC)
- ✅ 编译环境准备就绪
- ✅ memU 核心编译成功  
- ✅ Python 3.13 环境配置完成 (pyenv + memu_env)
- ✅ memU 包安装与验证成功
- 🔄 准备进入阶段3：数据库与嵌入器配置

### 遇到的问题与解决

（待填写）

### 结束时间
2026-03-02 TBD

---

**备注**：部署期间如需中断，请先备份当前状态。  
**支持**：部署问题请参考 [MemU GitHub Issues](https://github.com/NevaMind-AI/MemU/issues)