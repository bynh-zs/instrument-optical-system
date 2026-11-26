# 参考文献链接核验记录

- 核验时间：2026-11-15 18:40–18:50（GMT+8）
- 核验范围：参考文献清单（`docs/references.txt`）中的四条网络来源，即 [3]、[4]、[6]、[9]。
- 核验方式：HTTP 取回状态码与内容类型；网页类逐字比对标题、发布日期与责任者，PDF 类确认返回 application/pdf 且字节数非零。

| 编号 | URL | 状态码 | 内容类型 / 大小 | 与著录是否一致 |
|---|---|---|---|---|
| [3] | https://www.lighttrans.com/fileadmin/inhalte/version_history/221222_Release_Notes_VLF_2023.1_Final_FW.pdf | 200 | application/pdf / 8,447,278 B | 可访问；与“2023.1 Release Notes (Build 1.556)，2022-12-22”著录一致 |
| [4] | http://www.infotek.com.cn/html/4/202212291899_2.html | 200 | text/html / 30,472 B | 可访问；标题“VirtualLab Fusion 2023新版本更新内容（二）”、发布 2022-12-30、责任者讯技光电，与著录一致 |
| [6] | https://www.lighttrans.com/trial-software.html | 200 | text/html / 76,910 B | 可访问；页面原文“Saving functionality of created documents … is disabled.”，与 `software-limits.md` 所述试用版禁用保存一致 |
| [9] | https://www.wyrowski-photonics.com/fileadmin/inhalte/version_history/2020_Release%20Notes.pdf | 200 | application/pdf / 1,700,366 B | 可访问；与“2020.1 Release Notes (Build 1.238)”著录一致 |

补充说明两点：

1. [4] 的域名曾误记为 infotech.com.cn，该地址返回 301 且无正文；实际可访问的是 infotek.com.cn，30,472 字节，页面标题与发布信息均与著录吻合。参考文献 [4] 的 URL 已按此更正。
2. 试用版页面上的启动次数说明与 7.6.1.18 的 About 面板不完全对应（About 显示剩余启动次数并以每次启动递减），故 [6] 只引其“禁用保存新建文档”这一条，启动次数以软件界面显示为准。

其余文献：[1]、[2]、[5]、[7]、[8] 为厂商官网公开文件，著录信息在对应页面可直接核对；[10]–[12] 为课程内部资料，不公开检索，已按内部资料标注性质。

结论：四条网络来源在核验时均可访问，内容与著录一致，无失效链接。
