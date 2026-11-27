# dsh-plugin-balance-badge

DeepSeek Harness 插件：在侧边栏常驻显示 DeepSeek 账户余额，并**每消耗满一个阈值就整屏撒钱 + 金币音效**。

余额直接从 Harness 已登录的账户会话读取（`remote.account.getBalance`），不需要 API key，账户 token 也不会进入浏览器页面。

## 功能

- **余额徽标**：侧边栏底部、设置上方。显示充值余额，悬停看充值+赠金明细；多币种分别显示。
- **点击弹层**：余额明细、更新时间、手动刷新、**查看用量**（直达平台用量页）、隐藏此余额。
- **消耗提醒**：累计消耗每满一个阈值（默认 ¥5，可改 ¥1 或任意值），全屏播放：
  - 红色百元人民币、绿色美元、金币从画面上方落下、翻转、飘散（张数由密度滑块控制）
  - 中央 `−¥5.00` 放大砸入 + 光环 + 暖色光晕
  - 金币音效（两段作者原创素材可切换：收银机 cha-ching / 金币掉落）
  - 一次跨多档时合并成一条（如 `−¥10.00` + 「连续 2 档」）
  - 页面切走期间的消耗，回来时补播一条「离开期间 −¥X」汇总
- **预览按钮**：一键试听/试看，**不消耗任何 token、不产生网络请求**。

## 环境要求

| 项 | 要求 |
| --- | --- |
| DeepSeek Harness | `>= 0.2.2-rc.5`（Desktop 或 Web profile） |
| 账户 | 已在 Harness 中登录 DeepSeek 账户（未登录时徽标显示「未登录」） |
| 包管理器 | 安装时由 Harness 的插件管理器处理（需要 pnpm 可用） |

## 安装

### 从 npm 安装（推荐）

让 agent 调用 `plugin_manager` 的 `install_bundle`，target 填：

```
@speed55/dsh-plugin-balance-badge
```

也可以在侧边栏 **插件** 页里添加同一个包名，由 DSH 从 npm 解析并安装。
之后有新版本时，用同一入口升级即可。

### 从本地目录安装（开发/调试）

- **让 agent 装**：把本目录的绝对路径发给 agent，让它调用 `plugin_manager` 的 `install_bundle`（会以 `link:` 方式接入，改动即时生效）。
- **手动装**：侧边栏 → **插件** → 添加插件 → 选择本目录 → 启用。

装好后在 **设置 → 通用** 会多出三行：`显示账户余额`、`消耗提醒`、`消耗音效`；刷新页面后侧边栏底部出现余额徽标。

## 设置项

所有字段都是 `.volatile()`，改完即时生效，并写入 profile 的 `cordis.patch.yml`。

| 字段 | 默认 | 范围 | 说明 |
| --- | --- | --- | --- |
| `showBalance` | `true` | 布尔 | 侧边栏徽标总开关 |
| `spendNotice` | `true` | 布尔 | 全屏撒钱动画总开关 |
| `noticeStep` | `5` | 0.01–1000 | 累计消耗满多少（按钱包币种）播一次 |
| `rainDensity` | `0` | 0–100 | 撒币密度：0=稀疏（12 张），100=密集（150 张） |
| `soundNotice` | `true` | 布尔 | 音效开关 |
| `soundSample` | `reward` | `reward` \| `drop` | 使用哪段音效素材 |
| `refreshSeconds` | `60` | 15–600 | 余额读取基础间隔（秒） |

## 余额读取与限流

- 仅在页面可见时读取；从后台切回只补一次。
- 读取带 **±15% 抖动**，避免固定周期特征。
- 连续 15 / 30 次读数金额不变时，间隔自动放宽到 1.5× / 2×（最多 3×）。
- 读取失败按 2 的幂退避（最多 8×，封顶 10 分钟），成功即恢复——被限流或拒绝时不会继续撞。
- 硬下限 15 秒，配置再小也不会更频繁。

> 说明：`get_user_summary` 是普通 HTTP GET，不产生模型 token 消耗；但它是账户会话接口，
> 请按自己的风险偏好设置间隔，默认 60 秒是保守值。

## 音效与授权

两段金币音效（收银机 cha-ching / 金币掉落）都是**作者原创**，已裁切、限幅并降采样后以 base64 内嵌在 `client.js`，随本仓库以 [MIT](LICENSE) 分发，详见 [NOTICE.md](NOTICE.md)。仓库和构建产物中不包含任何第三方音频素材。

## 开发

```sh
pnpm install          # 安装 @deepseek-ai/schemastery（Host 侧 Config schema 需要 .volatile()）

# 需要重新生成内嵌音效时（素材自备，见 assets-src/source/README.md）
python assets-src/process_samples.py
node assets-src/embed_samples.mjs

# 语法自检
node --check client.js
```

### 目录结构

```
client.js            浏览器半：徽标、弹层、设置行、撒钱动画、音效播放
index.js             Host 半：Config schema（volatile 偏好）
cordis.patch.yml     插入插件行 + 默认配置
locale/{en,zh}.json  插件列表里的标题/描述
docs/DETAIL.md       插件详情页文档
icon.svg             插件图标
assets-src/          音频处理管线（Python）+ base64 回写脚本，不参与运行时
```

## Roadmap

- [x] 发布到 npm：`@speed55/dsh-plugin-balance-badge@1.0.0`
- [x] 音效替换为作者原创素材，仓库可公开发布
- [ ] 仓库转为 Public（Git 历史里还留着最早那版第三方音频，公开前需先重写历史或重建仓库）

---

### English summary

A DeepSeek Harness plugin that keeps your signed-in account balance in the
sidebar footer and, every time your spending crosses a configurable threshold,
plays a full-frame money-rain animation (CNY / USD notes and coins) with a coin
sound. Balance comes from the harness account session — no API key. Requires
DSH `>= 0.2.2-rc.5` and a signed-in DeepSeek account. The two coin recordings are
the author's own work and ship under the MIT license; see `NOTICE.md`.
