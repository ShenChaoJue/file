# Cloudreve 深色文件管理页 — 单文件静态原型设计

> 日期：2026-05-21
> 状态：已批准，准备实现
> 源文档：docs/cloudreve-replica.md

## 1. 概述

用单个 HTML 文件实现一个深色主题的 Cloudreve 风格网盘文件管理页原型。
无需构建工具，只需浏览器即可运行。包含顶部导航栏、左侧边栏、主内容区（工具栏 + 文件卡片网格），支持文件上传（按钮选择 + 拖拽）后动态渲染文件卡片。

## 2. 技术选型

| 项 | 选择 | 说明 |
|---|---|---|
| 文件结构 | 单文件 `index.html` | CSS + JS 全部内联 |
| 图标库 | Lucide Icons CDN | `<script src="https://unpkg.com/lucide@latest"></script>` |
| 字体 | 系统字体回退 | `"Microsoft YaHei", "Segoe UI", sans-serif`，无外部字体 CDN |
| 上传方式 | 文件选择器 + 拖拽 | 两种都支持 |
| 框架 | 无 | Vanilla JS，零依赖 |

## 3. 文件结构

```
D:\code\test\index.html  ← 唯一产出文件
```

## 4. HTML 骨架

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cloudreve</title>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    /* 全部 CSS 内联 */
  </style>
</head>
<body>
  <!-- Header -->
  <!-- Layout (Sidebar + Main) -->
  <script>
    // 全部 JS 内联
  </script>
</body>
</html>
```

## 5. 布局结构

```
┌─────────────────────────────────────────────────┐
│ Header (92px)                                   │
│ Brand | + 新建 | 搜索框 | 主题 设置 用户         │
├─────────────────┬───────────────────────────────┤
│ Sidebar (392px) │ Main                          │
│                 │                               │
│ 空间项           │ Toolbar (breadcrumb + actions)│
│ 导航菜单         │ FilePanel (文件标题 + grid)    │
│ 存储卡片         │                               │
│                 │                               │
└─────────────────┴───────────────────────────────┘
```

## 6. 设计系统

### 6.1 CSS 变量

```css
:root {
  --page-bg: #202020;
  --sidebar-bg: #242424;
  --panel-bg: #101010;
  --surface-bg: #151515;
  --surface-raised: #202020;
  --card-bg: #242424;
  --card-preview-bg: #111111;

  --border-subtle: #303030;
  --border-strong: #3a3a3a;

  --text-primary: #ffffff;
  --text-secondary: #d8d8d8;
  --text-muted: #9a9a9a;

  --brand-blue: #0d73bd;
  --active-nav-bg: #2f4859;
  --button-blue: #9fd3ff;
  --button-blue-hover: #b8ddff;

  --file-zip: #ffad26;
  --file-image: #4aa3ff;
  --file-video: #b16cff;
  --file-audio: #35d07f;
  --file-doc: #6aa8ff;
  --file-default: #c7c7c7;

  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 20px;
  --radius-xl: 24px;
  --radius-pill: 999px;
}
```

### 6.2 字体

```css
font-family: "Microsoft YaHei", "Segoe UI", "PingFang SC", sans-serif;
```

| 用途 | 字号 | 字重 |
|---|---:|---:|
| 品牌 Cloudreve | 32px | 700 |
| 顶部按钮 | 24px | 600 |
| 导航文字 | 24px | 600 |
| 面包屑文字 | 22px | 700 |
| 内容标题 | 24px | 700 |
| 文件名 | 22px | 600 |
| 辅助文字 | 18px | 400 |

### 6.3 圆角

`--radius-sm: 10px` / `--radius-md: 16px` / `--radius-lg: 20px` / `--radius-xl: 24px` / `--radius-pill: 999px`

## 7. 组件规范

### 7.1 Header

- 背景 `--page-bg`，高度 `92px`，flex 横向布局，垂直居中
- Brand: 圆形图标 (56px) + "Cloudreve" 文字
- 新建按钮: 背景 `--button-blue`，高 68px，宽 140px，圆角 18px，hover 变亮
- 搜索框: 背景 `#111`，边框 `1px solid --border-strong`，高 68px，宽 350px，圆角 18px
- 右侧: 主题、设置、用户图标按钮

### 7.2 Sidebar

- 宽度 `392px`，背景 `--sidebar-bg`，从 Header 下方延伸至底部
- 空间项: 胶囊形，背景 `--active-nav-bg`，左侧蓝色圆形 badge + "SKLL"
- 导航项: 图标 (26px) + 文字，行高 52px
- 存储卡片: 背景 `#111`，圆角 18px，进度条 + "26.8 MB / 1.0 TB"

### 7.3 Toolbar

- 面包屑: 背景 `#111`，高 66px，圆角 18px，与 Sidebar 空间项 badge 一致
- 操作按钮组: 背景 `#111`，边框 `1px solid --border-strong`，圆角 18px，高 66px
- 按钮: 刷新、更多、视图、排序，竖线分隔

### 7.4 FilePanel

- 背景 `--panel-bg`，边框 `1px solid --border-subtle`，圆角 `20px`，内边距 `28px`
- 标题 "文件"，24px 700，白色
- 与 Toolbar 间距 16px

### 7.5 FileGrid

```css
display: grid;
grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
gap: 26px;
```

### 7.6 FileCard

- 尺寸: 约 395px × 394px，背景 `--card-bg`，圆角 18px
- Header: 高 78px，图标 28px + 文件名（单行，溢出省略）
- Preview: 背景 `--card-preview-bg`，圆角 12px，高 300px，居中显示图标/缩略图
- Hover: `background: #2a2a2a`, `transform: translateY(-2px)`, `border-color: #3d3d3d`, `transition: 150ms`

### 7.7 空状态

无文件时居中显示：空文件夹图标 + "还没有文件" + "点击'新建'或拖拽文件到此处上传"

## 8. JavaScript 逻辑

### 8.1 数据模型

```ts
type UploadedFile = {
  id: string;
  name: string;
  type: "zip" | "image" | "video" | "audio" | "document" | "folder" | "unknown";
  size?: string;
  thumbnailUrl?: string;
  uploadedAt?: string;
};
```

### 8.2 核心函数

| 函数 | 职责 |
|---|---|
| `inferFileType(name, mime)` | 扩展名/MIME → 类型枚举 |
| `formatSize(bytes)` | 字节数 → 可读大小字符串 |
| `handleFileUpload(FileList)` | 生成 `UploadedFile[]`，图片生成 `objectURL` |
| `renderFileCards()` | 清空 grid → 遍历 files 数组 → 插入 FileCard HTML |
| `renderEmptyState()` | 插入空状态 HTML |
| `setupDragAndDrop()` | 主区域 dragover/drop 事件绑定 |
| `lucide.createIcons()` | DOM 更新后重新初始化图标 |

### 8.3 类型推断逻辑

```js
function inferFileType(name, mime) {
  const ext = name.split(".").pop()?.toLowerCase();
  if (["zip", "rar", "7z", "tar", "gz"].includes(ext)) return "zip";
  if (mime?.startsWith("image/")) return "image";
  if (mime?.startsWith("video/")) return "video";
  if (mime?.startsWith("audio/")) return "audio";
  if (["pdf", "doc", "docx", "txt", "md", "xls", "xlsx", "ppt", "pptx"].includes(ext)) return "document";
  return "unknown";
}
```

### 8.4 上传流程

1. 用户点击 "+ 新建" 或拖拽文件
2. 调用 `handleFileUpload()` 处理 FileList
3. 推入全局 `files` 数组
4. 调用 `renderFileCards()` 重新渲染
5. 调用 `lucide.createIcons()` 初始化新图标

## 9. 交互状态

| 元素 | Hover | Active | Focus |
|---|---|---|---|
| 新建按钮 | 背景 `--button-blue-hover` | 轻微下压 | — |
| 搜索框 | — | — | 边框变蓝 `--brand-blue` |
| 文件卡片 | `background: #2a2a2a`, `translateY(-2px)` | — | — |
| 工具按钮 | 背景 `#1c1c1c` | 背景 `#252525` | — |
| 导航项 | 背景 `#2a2a2a` | — | — |

## 10. 验收标准

1. 页面整体为深色 Cloudreve 风格
2. 左侧栏、顶部栏、主内容区比例正确
3. 文件卡片视觉效果接近深色网盘风格
4. 文件卡片数据来自用户上传结果，不写死示例
5. 图片显示缩略图，非图片显示对应大图标
6. 无文件时显示空状态
7. Hover/Focus 状态完整
8. 文件名超长时正确省略
9. 多文件时网格排列整齐
