# 从技术报告看On-Policy Distillation的崛起: 大模型后训练新范式

> 作者：潜龙勿用​
> 发布时间：2026-04-24 00:00:00
> 原文链接：https://zhuanlan.zhihu.com/p/2031101471563962191

过去一年，大模型后训练路线出现了一个清晰变化：**On-Policy Distillation 正在成为事实上的后训练新范式**。从 Qwen3 用 OPD 高效训练轻量模型，到 GLM-5 用它修复多阶段 RL 后的能力遗忘；从小米 MiMo-V2 通过多教师 OPD 整合数学、代码、搜索等专家能力，再到 DeepSeek-V4（[DeepSeek-V4技术报告解读: 从架构到 Infra 的全栈重构](https://zhuanlan.zhihu.com/p/2030982954617414764)） 直接以 OPD 替代 mixed RL，各家技术报告都指向同一个趋势：后训练不再只是依赖昂贵的 RL 探索，而是越来越重视如何稳定、高效地把已有强模型的能力迁移到目标模型中。

25年12月，我曾发表过OPD解读：[On-Policy Distillation](https://zhuanlan.zhihu.com/p/1988199307237680586)

OPD 的吸引力在于它同时继承了 RL 和蒸馏的优点：学生从自身分布中采样，避免了 off-policy 蒸馏的分布错位；教师则对每个 token 提供密集反馈，显著提升了训练信号密度。更关键的是，OPD 把能力整合从参数空间转移到 logit 空间，绕开了 weight merge 和 mixed RL 中常见的能力干扰问题。因此，理解 OPD 的原理与各家实现差异，已经成为理解新一代大模型后训练方法的关键入口

小米 MiMo-V2 后训练流程图：

![image](https://picx.zhimg.com/v2-7f0d721db23f2f9de262bb2584e201b9_1440w.jpg)

一、什么是 On-Policy Distillation？
-----------------------------

要理解它为什么重要，需要先清楚它解决了什么问题

### 三种路线的对比

训练一个强大的语言模型，后训练阶段通常面临三条路：

**纯 RL（Reinforcement Learning）**：让模型自己生成轨迹，对完整序列打一个结果奖励（sparse reward），用 PPO 或 GRPO 更新参数。这条路有效，DeepSeek-R1 和 Qwen3 旗舰都走过它。但问题在于信号密度极低——无论一条轨迹有多少 token，总共就得到一个 reward 信号。thinkingmachines.ai 的分析估计，OPD 的信号密度约为纯 RL 的 50-100 倍。

**Off-Policy 蒸馏（静态数据集蒸馏）**：用一个强教师模型生成高质量轨迹，收集成静态数据集，对学生做 SFT 或 logit 对齐。这是 DeepSeek-R1-Distill 系列的路线。问题是经典的 exposure bias：学生在测试时生成的 token 序列与训练时接受监督的教师轨迹分布是错位的。一旦学生偏离教师轨迹，后续 token 的监督信号就失真了，泛化能力因此受限。

**On-Policy Distillation**：两者取长补短——像 RL 一样，让学生从**自己当前的分布**采样轨迹（on-policy）；像蒸馏一样，由教师模型对每一个采样 token 给出 per-token 的 dense 反馈，具体形式是教师在该 token 上的 log 概率。学生通过最小化与教师之间的 **reverse KL 散度**来更新：

\mathcal{L}\_{OPD} = -\mathbb{E}\_{y \sim \pi\_\theta} \left[ \log \frac{\pi\_\text{teacher}(y|x)}{\pi\_\theta(y|x)} \right] = D\_{KL}(\pi\_\theta | \pi\_\text{teacher}) \\

这个公式的梯度方向，是让学生在自己已经采样出的 token 上，向教师的概率靠近。因为轨迹来自学生自身，不存在 distribution shift；因为教师给出 per-token 信号，每次更新的信息量远超稀疏 RL。

### Reverse KL 的 Mode-Seeking 性质

选择 reverse KL 而非 forward KL 不是随意的。Reverse KL 具有 **mode-seeking** 性质：当学生概率为零的地方，KL 项也为零，梯度消失；因此学生会集中学习教师的某一个高概率 " 模式 "，而不是平均覆盖教师所有可能的输出。

这对推理任务恰恰合适。数学推理题有正确解题路径，不需要模型均匀地模仿所有可能的推导风格。Mode-seeking 的 OPD 让学生 " 找到一条教师认可的路并坚定地走下去 "，比 forward KL（试图覆盖教师所有输出）的效果更好。

此外，thinkingmachines.ai 博客指出 OPD 天然 **unhackable**：低 KL 总是对应着学生在模仿教师的好行为，不像 RL 的 reward function 可以被模型找到捷径绕过。

### 工程实现极简

在已有 RL 训练框架（如 GRPO）之上接入 OPD，改动极小：只需把原来的 group-normalized advantage 替换为教师与学生的 log ratio： $$\hat{A}\_{i,t} = \text{sg}\left[\log \frac{\pi\_\text{teacher}(y\_{i,t}|x, y\_{i,<t})}{\pi\_\theta(y\_{i,t}|x, y\_{i,<t})}\right]$$

其中 `sg` 是 stop-gradient 算子，防止梯度流回教师分布。博客将其描述为 "a one-line change on top of RL implementations"。GLM-5 和 MiMo 的论文都可以印证这一说法，二者都显式复用了自己的 RL 优化框架。

### 实验验证效率优势

thinkingmachines.ai 博客给出了迄今最清晰的对比数据（AIME'24 数学推理基准，从同一个 off-policy 蒸馏 checkpoint 出发）：

| 方法 | 得分 | 相对计算量 |
| --- | --- | --- |
| Off-policy 蒸馏（基线） | 60% | 1× |
| 纯 RL | 67.6% | 10× |
| On-Policy 蒸馏 | 74.4% | 1× |

OPD 以远低于纯 RL 的算力，实现了远超 off-policy 蒸馏、且优于纯 RL 的效果。Qwen3 在旗舰模型层面印证了这一结论，并将效率优势定量为 " 仅需完整 4 阶段 RL 训练的 1/10 GPU 时间 "。

---

二、OPD 的变种：各家实现的技术分歧
-------------------

Qwen3（2025 年 5 月）是主要头部实验室中最早在技术报告中系统阐述 OPD 的。随后数月内，GLM-5（2026 年 2 月）、MiMo-V2-Flash（2026 年 1 月）、DeepSeek V4 相继跟进。但四家的实现在关键技术维度上存在显著分歧，形成了事实上的 "OPD 变种谱系 "。

### 2.1 KL 计算粒度：Token-Level vs Full-Vocabulary

这是最根本的技术分歧。

**Token-level KL（多数团队）**：只计算教师在实际被采样的那个 token 上的概率，即 `log π_teacher(y_t|x, y_{<t})`。这是对真实 KL 散度的蒙特卡洛近似——完整的 KL 需要对整个词表求积分，但近似版只需要教师在单个 token 上的 forward pass，计算量和显存需求极小。

GLM-5（Section 3.5，Eq. 2）、MiMo（Section 4.4，Eq. 5-8）和 Qwen3（Section 4.5）都采用这一方案。区别在于细节：

* **GLM-5** 将 GRPO 的 group size 从 32 降至 1，因为教师 log ratio 直接充当 advantage，不再需要组内对比来估计基线
* **MiMo** 额外引入重要性采样截断权重 w\_t，当训练策略和推理策略的比值超出 [\epsilon\_\text{low}, \epsilon\_\text{high}] 时丢弃该 token，增强训练稳定性

**Full-Vocabulary Logit Distillation（DeepSeek V4，Section 5.1.2）**：保留完整词表上的 KL，即 $$D\_{KL}(\pi\_0^i | \pi\_\theta^i) = \sum\_{v \in \mathcal{V}} \pi\_\text{teacher}(v|x,y\_{<t}) \log \frac{\pi\_\text{teacher}(v|x,y\_{<t})}{\pi\_\theta(v|x,y\_{<t})}$$

DeepSeek V4 原文明确批评 token-level 近似："prior works typically simplify the full-vocabulary KL loss into token-level KL estimates... this approach leads to **high variance in gradient estimation** and often causes **training instability**"。全词表 KL 给出每一步的精确梯度，训练更稳定，但代价是巨大的工程挑战：词表尺寸 × 序列长度 × 专家数 的显存消耗。

DeepSeek V4 为此专门开发了三层工程解决方案：

1. **Teacher weight scheduling**：教师权重卸载到分布式存储，ZeRO-like 参数共享，按需加载，不长驻显存
2. **Cached hidden states**：只缓存教师最后一层的 hidden state（而非词表维度的完整 logits），需要 logit 时临时经过 prediction head 重建，从根本上消除词表维度的显存瓶颈
3. **专用 TileLang kernel**：加速精确 KL 计算并压制动态内存分配

### 2.2 额外奖励信号：纯蒸馏 vs OPD + ORM

**纯蒸馏路线**（GLM-5、DeepSeek V4）：OPD 阶段只使用 KL 散度作为信号，完全不叠加 outcome reward。

GLM-5 的逻辑是：OPD 是最终收尾阶段，目标纯粹是 " 恢复能力 "，不需要再探索新的行为空间，只需高效对齐前序 RL checkpoint。DeepSeek V4 则是用 OPD 完全替代了 V3.2 中的 mixed RL 阶段，整个统一化过程只有 KL 信号驱动。

**OPD + ORM 混合路线**（MiMo MOPD，Section 4.4，Eq. 9）：

$$\hat{A}\_{\text{MOPD},t} = \text{sg}\left[\log \frac{\pi\_\text{teacher}(y\_t|x,y\_{<t})}{\pi\_\theta(y\_t|x,y\_{<t})}\right] + \alpha \cdot \hat{A}\_{\text{ORM}}$$

KL 项提供 token 级别的 dense 局部信号，ORM（Outcome Reward Model）项提供序列级别的 sparse 全局信号，二者通过系数 α 调和。

MiMo 的 ablation（Figure 6）给出了清晰的层级关系：纯 ORM RL < MOPD w/o ORM < **MOPD（ORM + KL）**。KL 信号显著加速收敛，ORM 信号则保持与可验证结果的对齐，缺一不可。

### 2.3 教师选取策略：同架构 checkpoint vs 异构多专家

**同架构前序 checkpoint（GLM-5）**：教师是同一个模型在 Reasoning RL 和 General RL 两个前序阶段训练完毕的 checkpoint。教师与学生共享完全相同的架构和词表，logit 空间天然对齐，实现最简单，信号质量最有保障。代价是教师的多样性受限——只有两个来自不同 RL 阶段的版本。

**多领域专家混合路由（MiMo）**：教师集合包括各领域 RL 专家（代码、数学、搜索、通用等）、SFT 模型，以及学生模型自身（用于 self-distillation，防止现有能力退化）。哪个任务路由到哪个教师由任务域标签决定。论文特别强调这种 "decoupled design enables easy integration of new teachers without restructuring the entire pipeline"——教师集合可以随时增减，无需重训流水线。

**10+ 万亿参数异构专家（DeepSeek V4）**：规模最大的多教师方案，独立训练 10 个以上专家模型，每个覆盖一个领域（数学、代码、Agent、指令跟随），每个领域还有三种推理强度变体（Non-think / Think High / Think Max）。各专家以 per-expert 权重 w\_i 加权贡献：

\mathcal{L}\_{OPD}(\theta) = \sum\_{i=1}^{N} w\_i \cdot D\_{KL}(\pi\_0^i | \pi\_\theta^i) \\

系统在任何给定提示上，自动路由到对应领域的专家获取监督信号。

**大→小跨尺度蒸馏（Qwen3）**：教师固定为旗舰模型（Qwen3-235B-A22B 或 Qwen3-32B），学生是 0.6B 到 30B 的 6 个轻量模型。这是四家中尺度跨度最大的 OPD 应用，旨在将旗舰模型的 thinking/non-thinking 双模式能力整体迁移到边缘侧模型。

### 2.4 OPD 在 Pipeline 中的位置

| 模型 | OPD 在 pipeline 中的位置 | 核心功能定位 |
| --- | --- | --- |
| Qwen3 | 轻量模型独立子流水线 | 替代完整 RL，效率优先 |
| GLM-5 | 最终收尾阶段 | 防灾难性遗忘，能力恢复 |
| MiMo | 主体第三阶段 | 多专家能力整合 |
| DeepSeek V4 | 统一化阶段（替代 mixed RL） | 10+ 专家知识压缩入单模型 |

---

三、各家的动机、实现与效果
-------------

### 3.1 Qwen3：效率革命，OPD 最早的系统性应用（2025 年 5 月）

Qwen3 是这轮 OPD 浪潮的先行者，但其使用场景颇为务实：旗舰模型（Qwen3-235B-A22B 和 Qwen3-32B）走完了完整的四阶段 RL 流水线（Long-CoT Cold Start → Reasoning RL → Thinking Mode Fusion → General RL），OPD 专门用于降低**轻量模型**的训练成本。

Qwen3 的 Strong-to-Weak Distillation 分两步走。第一步是 off-policy 蒸馏：收集教师（旗舰模型）在 `/think` 和 `/no_think` 两种模式下的输出，做标准 SFT，让学生建立基础的双模式切换能力。第二步才是 on-policy 蒸馏：学生从自身分布采样轨迹，对齐教师 logit，最小化 KL 散度。两阶段串行设计的思路是：off-policy 先为学生 " 打好底 "，避免 on-policy 阶段一开始因为学生输出质量太差导致教师信号噪声过大。

效果是戏剧性的。Qwen3-30B-A3B（总参数 30B，激活 3B）通过 OPD 获得的推理能力，可以与 QwQ-32B（32B 全激活）相当；Qwen3-0.6B 也明显超越 Qwen2.5-1.5B 同规模对手。整个轻量模型系列的训练只需要旗舰四阶段 RL 的 **1/10 GPU 时间**。

这个数字值得停下来想一想：为 6 个不同规模的轻量模型做完整 RL，本来需要 6 倍的旗舰训练成本；通过 OPD，总代价压缩到旗舰成本的 1/10。这是量产强推理小模型的关键使能技术。

### 3.2 GLM-5：修复多阶段 RL 的灾难性遗忘

GLM-5（智谱 AI & 清华大学）的后训练设计了一条雄心勃勃的四阶段 RL 流水线：Overall SFT → Reasoning RL → Agentic RL → General RL。每个阶段针对不同的能力维度：Reasoning RL 覆盖数学、科学、代码、工具集成推理（TIR）四个领域；Agentic RL 覆盖 SWE、终端任务、多步搜索；General RL 针对教学正确性、情感智能、任务专项质量三个维度。

问题随之而来：顺序优化多个目标，天然存在**灾难性遗忘（catastrophic forgetting）**。General RL 阶段的偏好对齐训练会侵蚀 Reasoning RL 积累的推理能力；Agentic RL 对长轨迹的强化会改变模型的输出风格，影响 General RL 后来想建立的自然语言质量。

GLM-5 的解法是将 OPD 作为**最终收尾阶段**（Section 3.5，"On-Policy Cross-Stage Distillation"）：把 Reasoning RL 和 General RL 两个阶段的最终 checkpoint 同时作为教师，学生从自身分布采样，优化 reverse KL。由于教师就是同一个模型的前序版本，架构和词表完全对齐，logit 信号直接可用。

一个精巧的实现细节：GRPO 在 RL 训练时，group size 通常设置为 32，目的是通过组内对比来估计 advantage 的基线。但在 OPD 阶段，advantage 直接由教师 log ratio 给出，无需组内对比，因此 group size 可以降至 **1**，batch size 则从 32 扩大到 1024，大幅提升数据吞吐。

OPD 让 GLM-5 在最终评测上实现了各项能力的同时在线：在 LMArena 中文本和代码双排行榜登顶，Humanity's Last Exam 达 50.4，SWE-bench Verified 77.8，Terminal-Bench 2.0 56.2，均优于或持平 Claude Opus 4.5。

### 3.3 MiMo-V2-Flash：能力不平衡的系统性解法

小米 MiMo-V2-Flash 将 OPD（以 MOPD，Multi-Teacher On-Policy Distillation 命名）放在了后训练流水线的**核心位置**，而非收尾步骤。

背景问题是 AI 后训练中普遍存在的 **see-saw effect**：同时提升数学推理会压制代码能力，提升代码能力又会损害通用对话质量。这是因为在一个统一参数空间内对多个目标同时做 RL，各目标的梯度方向会互相干扰。Weight merge（参数平均）是一种常见逃法，但实验一再证明会导致可观的性能损耗。

MiMo 的三阶段方案：Stage 1 是通用 SFT 建立基础；Stage 2 是独立的领域专家 RL 训练（代码 Agent、搜索 Agent、数学、通用推理、安全对齐各自独立优化，互不干扰）；Stage 3 是 MOPD，用各领域专家的 logit 分布作为学生的学习信号，在 logit 空间而非参数空间完成能力整合。

技术上最有特色的是 MOPD 的 advantage 公式（Eq. 9）：

$$\hat{A}\_{\text{MOPD},t} = \text{sg}\left[\log \frac{\pi\_{\text{domain}\_x}(y\_t|x,y\_{<t})}{\pi\_\theta(y\_t|x,y\_{<t})}\right] + \alpha \cdot \hat{A}\_{\text{ORM}}$$

\pi\_{\text{domain}\_x} 是根据提示所属领域动态选取的教师策略。KL 项给出 dense 的 per-token 方向信号，ORM 项保留与可验证结果的端到端对齐，两者以系数 α 权衡。

另一个创新是 **Rollout Routing Replay（R3）**：MoE 模型在推理时（rollout）和训练时（update）的 expert routing 可能不一致，这会引入梯度噪声。R3 通过缓存 rollout 时的 routing 决策并在训练时复现，保证两阶段 routing 一致，使 RL 训练更稳定。

效果上，MOPD 在多个指标上让学生超越最强教师（Table 7）：AIME 2025 +0.2，HMMT Feb 2025 +1.8，LiveCodeBench +0.6，HLE +0.9。同时 SWE-Bench Verified 73.4% 登顶开源排行，SWE-Bench Multilingual 71.7%。

### 3.4 DeepSeek V4：万亿参数专家知识的 Logit-Space 压缩

DeepSeek V4 的后训练场景是这四家中最复杂的：需要整合 10 个以上独立训练的专家模型，每个专家针对一个领域，还有三种推理强度变体（Non-think / Think High / Think Max），对应不同的 length penalty 和 context window 设置。

传统方案的失败已有先例：参数合并（weight merge）导致各专家的尖锐能力在参数空间里 " 稀释 "；Mixed RL（同时对多领域做联合强化）则是 MiMo 所描述的 see-saw effect。DeepSeek V4 的选择是完全放弃 Mixed RL，将 OPD 设定为整个后训练的统一化终点。原文表述直接："the mixed Reinforcement Learning (RL) stage was entirely replaced by On-Policy Distillation (OPD)"。

DeepSeek V4 OPD 最显著的技术贡献是 **full-vocabulary logit distillation**，以及配套的工程基础设施。逻辑链条很清晰：既然用 10 个以上的万亿参数教师，就必须精确地从每个教师的完整分布中学习，token-level 近似的高方差会掩盖各专家的细微差异，导致统一化质量下降。

三层工程支持使得大规模全词表 OPD 成为现实：

* **教师权重调度**（Teacher Weight Scheduling）：10 个以上万亿参数的教师权重无法常驻显存，系统将它们卸载到分布式存储，用 ZeRO-like 共享机制按需加载，每次 mini-batch 每个教师 head 只加载一次
* **Hidden State 缓存**：教师 forward pass 只缓存最后一层 hidden state，需要 logit 时实时经过 prediction head 重建，彻底消除词表维度的显存瓶颈
* **TileLang 专用 kernel**：精确计算两个完整分布之间的 KL，加速运算并压制动态内存分配

结果是 DeepSeek-V4-Pro-Max 在知识密集型任务（HLE、Terminal Bench 2.0）上显著超越 GPT-5.2 和 Gemini-3.0-Pro，在 Agent 任务上持平甚至超越 Kimi-K2.6 和 GLM-5.1。

四、未来展望
------

OPD 在不到一年内从边缘技术变为主流范式，接下来的演化方向已经初现轮廓。

### 4.1 Full-Vocabulary KL 将成为标配，工程门槛持续下降

DeepSeek V4 已经证明全词表 KL 在理论和实践上都优于 token-level 近似。随着 hidden state 缓存和专用 kernel 的开源化（DeepSeek V4 已开源 TileLang），其他团队复制这套工程方案的成本将大幅降低。可以预期，未来 12-18 个月内，主要实验室的 OPD 实现会向全词表方向收敛。

### 4.2 OPD + PRM：从结果监督到过程监督

MiMo 的 MOPD 证明 KL + ORM（序列级结果奖励）的组合优于单独的任一方案。下一步自然演化是将 ORM 替换为 **Process Reward Model（PRM）**——对每个推理步骤而非最终答案打分。PRM 可以在轨迹中途识别 " 推理失误的关键 fork point"，与 OPD 的 per-token 信号在粒度上高度匹配。两者结合，可能是目前最密集的训练信号配置：教师 logit（全局方向）+ PRM（步骤正确性）+ ORM（最终结果）三重叠加。

### 4.3 Iterative Co-Evolution：自强化的师生螺旋

MiMo 在论文中明确提出了一个前瞻性路线图：蒸馏产生的学生模型可以重新进入专家 RL 训练阶段，成为更强的下一代教师，再反哺下一代学生——形成自强化循环。这与 AlphaZero 的 self-play 范式在结构上高度相似，区别在于 OPD 框架让 " 教师 - 学生 " 角色的切换更加显式和可控。

如果这个循环被验证有效，它意味着 OPD 不只是一次性的知识压缩操作，而是一种**持续改进机制**。每一代模型都可以在前一代的基础上自动提升，无需持续引入新的外部数据或人工标注。

### 4.4 OPD 与百万 Token 长上下文的张力

DeepSeek V4 和 MiMo 都将百万 token 长上下文作为核心能力目标。但 OPD 面临一个显著的工程困难：在百万 token 长轨迹上做 on-policy 采样，推理成本极高；而计算完整轨迹每个 token 上的教师 logit，显存需求随序列长度线性增长。

这个矛盾目前靠 " 分段采样 " 和 " 轨迹截断 " 缓解，但理论上并不完美。如何在超长上下文中设计高效的 OPD 采样策略（例如只在关键决策点做 OPD 更新，其余位置用 RL），是下一个值得攻关的工程问题。

### 4.5 Inference-Time Distillation：推理时的动态教师

目前的 OPD 全部发生在训练阶段。一个更激进的方向是 **inference-time distillation**：在模型推理时，对于识别出的关键 "forking token"（决定推理路径走向的关键节点），实时查询教师模型的分布，在 beam search 或 sampling 过程中加入教师引导。

这本质上是将 OPD 的信号从训练时延伸到推理时，让学生在每次推理中都能实时 " 请教 " 教师，而不是只在训练阶段学习一次就固化。thinkingmachines.ai 博客在实验中自然发现了 forking token 的存在——这些 token 上 OPD 的惩罚信号特别大，说明它们正是学生偏离教师正确路径的关键节点。将这种识别能力迁移到推理时，是一条逻辑上连贯的演化路径。

### 4.6 范式总结：从参数空间整合到 Logit 空间整合

OPD 的核心贡献不仅在于训练效率，更在于它提供了一种**在 logit 空间而非参数空间整合知识**的方法论。

传统的知识整合方案（weight merge、adapter 叠加、混合 RL）都在参数空间操作，各专家能力的 " 干涉 " 不可避免。OPD 则绕开了这个问题：专家模型独立存在，它们的知识以 logit 分布的形式流入学生，而学生的参数在自身生成的轨迹上学习，两个空间的操作互不干扰。

这一洞察被四家团队从不同角度独立发现，并相继写入各自的技术报告，说明它触及了某种更深层的结构性真理：**语言模型的能力，在 logit 空间比在参数空间更容易合并、迁移和保留。**

随着专家模型的规模和数量持续扩大，OPD 作为 " 能力压缩与整合 " 的核心工具，其重要性将只增不减。

---

*参考文献：Qwen3 Technical Report (2505.09388)；GLM-5: from Vibe Coding to Agentic Engineering (2602.15763)；MiMo-V2-Flash Technical Report (2601.02780)；DeepSeek-V4 Technical Report；On-Policy Distillation, thinkingmachines.ai*