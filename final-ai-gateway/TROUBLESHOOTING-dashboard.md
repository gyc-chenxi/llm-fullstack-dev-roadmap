# Troubleshooting: Dashboard 前端问题

## 症状

```
npm install 失败
npm run dev 报错
Dashboard 页面空白
API 请求 404 / CORS 错误
```

## 原因

1. Node.js 版本不兼容
2. 依赖安装不完整
3. Vite 代理配置错误
4. 后端 API 未启动
5. CORS 未正确配置

## 解决步骤

### 1. 检查 Node.js 版本

```bash
node -v
# 需要 >= 18.0

npm -v
# 需要 >= 9.0
```

如果版本太低：
```bash
# 使用 nvm 管理 Node 版本
nvm install 18
nvm use 18
```

### 2. 清理重装依赖

```bash
cd frontend

# 清理
rm -rf node_modules package-lock.json

# 重新安装
npm install

# 如果 npm 慢，用国内镜像
npm install --registry=https://registry.npmmirror.com
```

### 3. 检查 Vite 代理配置

`frontend/vite.config.js`:
```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 确认后端端口
        changeOrigin: true,
      },
    },
  },
})
```

验证后端是否在运行：
```bash
curl http://127.0.0.1:8000/api/v1/admin/health
```

### 4. 直接启动调试

```bash
cd frontend
npx vite --debug
```

查看控制台输出，确认：
- Vite 启动在正确的端口
- 代理规则已加载
- 没有模块解析错误

### 5. CORS 问题

后端 `main.py` 中已配置 CORS：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

如果仍有 CORS 问题，检查是否：
- 中间件添加顺序（CORS 应在其他中间件之前）
- 使用了自定义 headers

### 6. 浏览器调试

打开浏览器开发者工具 (F12)：
- **Network 标签**：查看 API 请求状态码和响应
- **Console 标签**：查看 JavaScript 错误
- **Application 标签**：查看 Pinia store 状态

常见问题：
- 404：路由路径错误或后端路由未注册
- CORS：中间件配置问题
- 白屏：Vue 组件加载失败（检查 import 路径）

### 7. 验证 Pinia Store

在浏览器 Console 中：
```javascript
// 访问 Pinia store
const app = document.querySelector('#app').__vue_app__
const pinia = app.config.globalProperties.$pinia
```

### 8. 生产构建

如果开发模式正常但生产构建有问题：
```bash
cd frontend
npm run build

# 检查 dist/ 目录
ls dist/

# 本地预览
npm run preview
```

## 预防措施

- 使用 `.nvmrc` 锁定 Node 版本
- 在 `package.json` 中固定依赖版本
- 配置 `vite.config.js` 的代理规则
- 在 CI 中运行 `npm run build` 防止构建失败
