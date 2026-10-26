# 招聘命令参考

下文 `boss` 均替换为 `python 本Skill绝对路径/scripts/boss.py`。这些是调用示例，参数最终以实际 `schema` 和相应 `--help` 为准。尖括号字段需替换为前序接口返回的真实值，不能原样执行。

## 能力与身份

```bash
boss --json --role recruiter --platform zhipin schema
boss status
boss hr whoami
boss hr jobs list --page 1
boss hr jobs detail <encJobId>
```

`--platform` 使用 `zhipin`；schema 内的招聘者适配器名 `zhipin-recruiter` 不是这个全局选项的值。`hr` 自动设置 recruiter 角色；其他共享命令可显式传 `--role recruiter`。

复用用户指定的 Chrome 示例：`boss --cdp-url http://localhost:9222 hr whoami`。实际地址以用户环境为准，不主动启动新调试端口或改变浏览器配置。

## 候选人搜索和简历

```bash
boss hr candidates "Python" --city 101010100 --page 1
boss hr candidates "Python" --job-id <职位ID> --page 1
boss hr recommendations --job-id <encJobId> --page 1
boss hr applications --job-id <职位ID> --page 1
boss hr resume <encryptGeekId> --job-id <encryptJobId> --security-id <securityId>
```

城市需平台城市编码，经验、学历和薪资筛选值也有平台编码，不把自然语言范围直接传成枚举。没有可靠值时先读 `boss cities --help`、`boss hr candidates --help` 和 schema。岗位与候选人 ID 保留原样，不截短、不自造、不在不同返回记录之间拼接。

## 沟通读取

```bash
boss hr chat --job-id <职位ID> --page 1
boss hr chatmsg <friend_id> --count 20
boss hr last-messages --friend-id <friend_id> --count 5
```

会话 `friend_id` 是数字，与 `encryptGeekId` 含义不同。`hr last-messages` 可重复传入 `--friend-id`。需要更早记录时按帮助中的分页参数推进。

## 首次招呼与回复

先从同一条 `hr recommendations` 卡片提取所有参数，按用户的具体候选人和话术授权预览：

```bash
boss hr greet --geek-id <encryptGeekId> --job-id <encryptJobId> --expect-id <expectId> --lid <lid> --security-id <securityId> --message "待核对的完整话术" --dry-run
```

预览不验证真实发送是否可用。获得明确批准后，保持目标参数和话术一致，将 `--dry-run` 替换为 `--yes`；卡片含有需要传递的 `suid` 时使用 `--suid`。命中 `ALREADY_GREETED`、`GREET_LIMIT` 或结果不确定即停止，不另开身份或绕过防重记录。

回复对应会话前读 `hr chatmsg`，在已有授权范围内调用：

```bash
boss hr reply <friend_id> "已获授权的回复正文"
```

## 附件简历与联系方式

```bash
# 主动索要简历，会发送平台请求，需要相应授权
boss hr request-resume <friend_id>

# 预览候选人发来的附件简历请求
boss hr accept-resume <friend_id> --message-id <请求消息mid> --dry-run

# 用户明确批准对应请求后执行
boss hr accept-resume <friend_id> --message-id <请求消息mid> --yes

# 附件已收到后，使用附件消息mid下载；输出目录先确保存在
boss hr download-resume <friend_id> --message-id <附件消息mid> --output "运行目录/候选人简历.pdf"

# 请求交换联系方式，会发送平台请求，需要相应授权
boss hr resume --exchange --type wechat --friend-id <friend_id>
```

消息 `mid` 从 `hr chatmsg` 的对应消息中提取。请求消息与附件消息不能互换；简历下载不等于索要或同意接收。文件后缀按实际附件类型指定。

## 现有职位管理

```bash
boss hr jobs list
boss hr jobs detail <encJobId>
# 用户明确授权上下线相应职位后才执行
boss hr jobs offline <job_id>
boss hr jobs online <job_id>
```

当前命令提供现有职位的列表、详情和上下线；发布、编辑等能力须另行核实 schema，不推测存在。
