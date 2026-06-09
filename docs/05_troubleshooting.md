# 常见问题与解决方案

> 环境配置、模型下载、推理部署中的高频报错

---

## Conda / 环境类

### conda create 报 "CondaHTTPError"
```
原因：网络问题或镜像源失效
解决：换清华镜像源
  conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
```

### pip install 报 "No matching distribution"
```
原因：Python 版本不匹配（如用 Python 3.12 装只有 3.11 wheel 的包）
解决：确认 Python 3.11
  python --version
  conda create -n llm python=3.11
```

### "command not found: conda"
```
原因：conda 未初始化到 shell
解决：conda init zsh 后重启终端
```

---

## PyTorch / MLX 类

### MPS 报 "Placeholder storage hasn't been allocated"
```
原因：Apple Silicon MPS 后端 bug
解决：设置环境变量
  export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
```

### MLX 报 "framework not found Metal"
```
原因：macOS 版本太低（需要 14.0+）
解决：升级 macOS 到 Sonoma 或更高
```

---

## 模型下载类

### HuggingFace 下载慢 / 断连
```
解决 1：使用镜像
  export HF_ENDPOINT=https://hf-mirror.com

解决 2：使用 hf 命令断点续传
  hf download model/name --resume-download

解决 3：使用 modelscope（国内源）
  pip install modelscope
```

### GGUF 分片文件合并报错
```
原因：llama-gguf-split 路径不对或未编译
解决：
  cd third_party/llama.cpp/build
  cmake .. -DGGML_METAL=ON
  make -j4 llama-gguf-split
```

### "File not found" 下载 GGUF 模型
```
原因：GGUF 模型可能已拆分为多个分片文件
解决：在 HuggingFace 页面查看文件列表，分别下载分片后合并
```

---

## Docker 类

### Docker 容器无法访问 GPU
```
原因：Docker Desktop for Mac 不支持 GPU 直通
解决：在宿主机（Mac）上直接运行模型，Docker 只用于 API 服务和中间件
```

### docker-compose up 报端口占用
```
原因：8000/6379/5432 端口已被占用
解决：
  lsof -i :8000  # 找到占用进程
  kill -9 <PID>   # 终止进程
```

---

## 前端类

### Vite 启动报 "Cannot find module"
```
原因：未安装 node_modules
解决：
  cd frontend && npm install
```

### SSE 流式输出不显示
```
原因 1：Vite proxy 未正确转发
解决：检查 vite.config.ts 中 proxy 配置是否指向 Gateway 地址

原因 2：后端未设置 CORS
解决：FastAPI 添加 CORSMiddleware
```

---

> 更多问题请在各 Phase 目录的 `learning-issues.md` 中查找和记录
