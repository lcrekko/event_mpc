# 新初始参数下的两控制器比较与论文图

## 设置与用户决定

两个控制器都从 `I0=.05 A, slow gain=1.5, ultraslow gain=2` 开始。固定控制器
始终保持这些参数；uniform MPC 在首个半摆使用相同参数，收到第一组完整探测器
反馈后才开始优化。机械和六个神经元的初始状态沿用论文，未重新计算稳态或重置。
两者首个半摆的真实状态、事件和能量记录相同。

本次用户明确将 MPC 搜索范围改为：I0∈[0,.12] A，slow gain∈[1.5,2.5]，
ultraslow gain∈[1,2]。`SearchSettings` 现在支持每次实验独立配置范围；旧实验
的默认范围和已保存结果没有被覆盖。本次参数均位于新范围内。

保持 N=4、50 个事件区间、seed1、每次 uniform 搜索 514 个候选，沿用此前
uniform 对比的采样预算。Uniform shooting 没有 R 轮更新；514 是它的一批
候选数，不能再乘以 R。启动半摆只记录一个固定参数预测，其后每个事件优化。
模型、目标权重和积分精度均保持原设置；没有平滑参数曲线或重选更好种子。

“Nominal Control” 是本次用户指定的固定参数基线，不是旧报告中经过计算的
优秀名义 HCO 参数。旧版 Milestone F 报告仍保留在原目录。

## 关于 1.2 秒与 2 ms 的计时解释

`1.2 s / 512 ≈ 2.34 ms` 的算术成立，原实现还额外评估两个更新均值，因此
M=256/R=2 实际总计 514 次评估，均摊约 2.33 ms。每个候选是完整的 N=4
事件预测序列，不是一个 ODE 步或一个半摆。

这个除法给出的是整批工作按候选数平均后的墙钟时间，即吞吐率口径。已有
代码用四线程并行评估候选，因此不能把 2.33 ms 当成单候选独立执行延迟，
也不能认为 1.2 秒是尚未并行的耗时。候选相互独立，确实适合进一步并行化；
现有结果本身不能证明扩大并行后能达到 50 ms。相对现有约 1.2 秒仍需约
24 倍整体加速，实际缩放还取决于资源与开销。本次没有新增并行性能对照实验。

## 结果

| 指标 | EC-MPC | Nominal Control |
|---|---:|---:|
| 完成半摆区间 | 50/50 | 50/50 |
| 幅值 RMS 误差 | 0.101715° | 2.698446° |
| 过零时间 RMS 误差 | 0.642633 ms | 18.260071 ms |
| 总绝对机械能量交换 | 4.931174 μJ | 2.004081 μJ |

本次 uniform MPC 的跟踪改善，参数也随事件改变。能量交换增加，不能将其
描述为降低能耗；固定控制器的幅值持续衰减，而 MPC 需要做功维持振荡。
这是事先选择的一个 seed1 实验，不构成多种子统计结论。

## 三张图的定义与版式

1. 图1：3行1列，幅值大小、过零时间误差、每个半摆的绝对机械能量交换。
   数据点画在该半摆的结束过零时刻。标签为 `A`、`t_M-t_M*`、`q`；顶部
   一行只有 `EC-MPC` 和 `Nominal Control` 两个图例。灰色点线表示 A=5°
   和时间误差为零。q 是 (19) 的积分，不是电能，也不是累计到当前时刻的值。
2. 图2：3行1列，实际应用的 I0、slow gain、ultraslow gain，保持阶梯曲线。
   不增加图例或标题，也不平滑或隐藏参数跳变。
3. 图3：2行1列，按精确式 (2)/(6) 重建的实际力矩和神经元 A 快电压。
   使用实际应用时间和脉冲切换记录，没有根据参数幅值虚构连续电流。

横轴均为模拟物理时间 t。图1单位依次是 degree、ms、μJ；图2电流为 mA，
图3力矩为 μN m。电压保持模型原单位，未擅自换成 mV。

三图宽度都是 3.5英寸（88.9mm），高度分别为5.5、5.0、3.7英寸；以此单栏
宽度插入论文时，坐标标签12pt、刻度10pt、图例11pt。真正使用 LaTeX 的
Computer Modern 字体，PDF 中字体已嵌入。为适配当前 TeX 安装，使用原生
LaTeX serif（即 Computer Modern Roman），避免额外依赖 EC 编码字体包。

每张图输出 PDF、SVG 和600dpi PNG。推荐论文使用 PDF 矢量版本，避免再将
整图缩得过小。PNG 是从同一个 LaTeX PDF 渲染，确保预览与矢量稿的字体一致。
图形已实际生成并目视检查；数据坐标另存为 performance.csv。

## 复现

Windows PowerShell，从仓库根目录：

```powershell
$env:NUMBA_NUM_THREADS="4"
.\.venv\Scripts\python.exe -m event_mpc.startup_comparison --output outputs/new-comparison
.\.venv\Scripts\python.exe -m event_mpc.paper_figures --comparison outputs/new-comparison
```

只重画已上传的数据，不重新优化：

```powershell
.\.venv\Scripts\python.exe -m event_mpc.paper_figures --comparison results/startup-comparison
```

LaTeX 渲染需要系统中有 `latex` 和 `pdftocairo`：Windows 可使用 MiKTeX 或
TeX Live，以及 Poppler，并将程序加入 PATH。原生 CM 字体、type1cm 和 Courier
相关 TeX 包需要可用。当前云端已验证这些工具可用。若本机没有 LaTeX，可以
显式加 `--mathtext` 使用备用渲染，rendering.json 会如实记录非 LaTeX 模式。
Windows 仍未实机验证。

新的参数范围、初始化、首个半摆策略、图的坐标含义记录在
`configs/startup-comparison.json`；原始轨迹、所有候选、事件、动作和软件/代码
来源保存在 `results/startup-comparison/`。传感延迟因果实现保持不变，优化
计算耗时仍只测量、未加入模拟控制延迟；本次跟踪改善不等同于实时硬件已实现。
