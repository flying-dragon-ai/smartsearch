# Project brand icon

使用用户提供的人物插画作为 Smart Search 的项目图标，保留白发、蓝眼睛、发饰、放大镜配件、两颗星星及原有构图。源图片若缺失 alpha，先移除背景并检查透明边界，不新增造型、文字、底色或投影。之后只进行现有图标脚本的透明裁边、留白和尺寸转换。

### Scenario: Transparent artwork

源 PNG 与最终 PNG 有真实透明像素和不透明主体，深色背景被移除，人物和两颗星星保留；原有深色配饰不应误删。预览检查透明边缘，不把黑色/白色底图当透明通道。图标按现有脚本保持方形、等比缩放及透明留白，不拉伸或补画原图裁掉的下半部。

### Scenario: Existing icon consumers stay consistent

品牌 PNG 与 Windows PNG 字节相同；Windows ICO 含原有九种尺寸，macOS ICNS 含原有四种尺寸，共享尺寸帧相同。Web favicon/标题图标与 ICO 64px 帧一致。Windows 程序、标题/托盘、安装器、macOS Info.plist/打包和 README 继续使用已存在的文件入口。运行现有资源一致性检查，重复生成不产生变化；最终差异不包含无关业务或签名代码。
