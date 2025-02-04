# LinuxDo 每日签到（每日打卡）

## 项目描述
这个项目用于自动登录 [LinuxDo](https://linux.do/) 网站并随机读取几个帖子。它使用 Python 和 Playwright 自动化库模拟浏览器登录并浏览帖子，以达到自动签到的功能。

## 功能
- 自动登录 LinuxDo
- 自动浏览帖子
- 自动点赞（可选）
- 每天在 GitHub Actions 中自动运行
- WxPusher 通知运行结果

## 如何使用
本节介绍在 GitHub Actions 中如何使用。在进行之前需要先 fork 本项目。

### 设置环境变量
在使用此自动化脚本之前，需要在 GitHub 仓库中配置必要的环境变量：

1. 登录 GitHub，进入你的项目仓库
2. 点击仓库的 `Settings` 选项卡
3. 在左侧菜单中找到 `Secrets and variables` 部分，点击 `Actions`
4. 点击 `New repository secret` 按钮
5. 添加以下变量：
   - `USERNAME`：你的 LinuxDo 用户名或邮箱
   - `PASSWORD`：你的 LinuxDo 密码
   - `WXPUSHER_APP_TOKEN`：WxPusher 的 apptoken（可选，用于推送通知）

- ### Plus Push 通知配置
- 1. 访问 [Plus Push](https://www.pushplus.plus/) 官网
- 2. 登录并获取你的 token
- 3. 将 token 添加到 GitHub Secrets 中的 `PUSH_PLUS_TOKEN`

未配置 PUSH_PLUS_TOKEN 时将自动跳过通知功能，不影响签到。

### GitHub Actions 自动运行
此项目会在以下时间自动运行签到脚本：
- 北京时间 5:00-24:00 每2小时运行一次
- 北京时间 1:00-4:00 每4小时运行一次

第一次使用时，请先手动运行一次以确保配置正确：

1. 进入 GitHub 仓库的 `Actions` 选项卡
2. 选择 `Sync Upstream` 工作流
3. 点击 `Run workflow` 按钮启动并等待完成
4. 然后选择 `Daily Check-in` 工作流
5. 再次点击 `Run workflow` 按钮启动

请确保第一次手动运行成功后，才会开始按照上述时间表自动执行。如果运行失败，请检查 Actions 日志或等待 Plus Push 通知查看具体错误信息。

## 运行结果

### 网页查看
`Actions` -> 最新的 `Daily Check-in` -> `run_script` -> `Execute script`

可看到 `Connect Info`：
（新号可能这里为空，多挂几天就有了）
![image](https://github.com/user-attachments/assets/853549a5-b11d-4d5a-9284-7ad2f8ea698b)

### WxPusher 通知
配置 WXPUSHER_APP_TOKEN 后，每次运行结果都会通过 WxPusher 推送到你的设备上，包括：
- 签到状态
- 浏览帖子数量
- 点赞数量（如果启用）
- 可能遇到的错误信息

## 自动更新
默认每天自动从上游同步更新。第一次需要手动运行一次。
![alt text](/images/image.png)
![alt text](/images/image-1.png)
## 注意事项
1. 请勿滥用，保持合理的使用频率
2. 建议启用自动更新以获得最新功能和修复
3. 如遇到问题，可以查看 Actions 日志或等待 Plus Push 通知

## 致谢
本项目基于 [doveppp/linuxdo-checkin](https://github.com/doveppp/linuxdo-checkin) 开发，感谢原作者的贡献。

主要改进：
- 原作者的代码非常完善且健壮，本项目在此基础上：
  - 简化了配置流程
  - 使用 WxPusher 替代 Telegram 通知
  - 优化了部分代码结构
  - 更新了文档说明

特别感谢 [@doveppp](https://github.com/doveppp) 提供的优秀项目！如果您觉得这个项目对您有帮助，欢迎：
- ⭐ Star 本项目
- 🔄 Fork 并优化代码

注：本项目仅用于学习交流，请勿滥用。如有侵权请联系删除。
