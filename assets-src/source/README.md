# 源素材放这里

音频处理管线（`../process_samples.py`）从**你自己合法获得的**素材重新生成内嵌音频，
本仓库不包含、也不分发这些素材。

## 步骤

1. 把你的两段金币音效放进这个目录，命名为：

   | 文件名 | 用途 | 本仓库使用的原创原始文件 |
   | --- | --- | --- |
   | `reward.wav`（或 `.mp3` / `.m4a` / `.ogg` / `.mp4`） | 收银机 cha-ching | `cash-register-cha-ching.mp3` |
   | `drop.wav` | 金币掉落 | `原创金币掉落_短版.mp3` |

   原始文件可以是视频容器（`.mp4`），管线会用 ffmpeg 抽音轨。仓库自身使用的两段素材
   都是作者原创，见根目录 `NOTICE.md`。

2. 抽出音轨为 WAV（16-bit 单声道 44.1 kHz）：

   ```sh
   ffmpeg -y -i source/reward.mp4 -vn -ac 1 -ar 44100 -c:a pcm_s16le ../src-reward.wav
   ffmpeg -y -i source/drop.mp4   -vn -ac 1 -ar 44100 -c:a pcm_s16le ../src-drop.wav
   ```

3. 裁切、归一化、降采样并生成 base64：

   ```sh
   python ../process_samples.py
   ```

   输出 `../coin-reward.wav|.b64` 和 `../coin-drop.wav|.b64`。

4. 把 base64 写回客户端包：

   ```sh
   node ../embed_samples.mjs
   ```

5. 校验：`client.js` 里的 `COIN_SAMPLES` 两个值与 `.b64` 文件解码后的内容应逐字节一致。

> 授权提示：如果你的素材来自素材站，请先确认其条款允许你随插件分发；
> 详见仓库根目录的 `NOTICE.md`。
