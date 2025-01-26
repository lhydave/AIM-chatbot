
import textwrap


testcontent = r"""\begin{itemize}
    \item \Cref{part:AI-logic}，AI的逻辑：这部分探究AI的认知是什么样的，如何被数学建模. 我们将会探究如何用Bayes概率论建立AI的推理模型（\Cref{chap:plausible-reasoning}），以及如何用Markov链建立AI包含时间的认知与决策模型（\Cref{chap:markov-chain}）. 
    \item  \Cref{part:information-data}，信息与数据：这部分探究AI如何从环境中获得认知，而现实中，这就是关于信息与数据的问题. 我们将会展示信息论的基本事实（\Cref{chap:information-theory}），AI面对数据的特性（\Cref{chap:J-L-Lemma}），以及如何在保护个人隐私的前提下让AI利用数据（\Cref{chap:differential-privacy}）. 
    \item  \Cref{part:decision-optimization}，决策与优化：这部分探究AI如何面对环境做出决策以及优化. 我们将会给出优化的基本概念以及特别重要的一类优化问题——凸优化（\Cref{chap:convex-analysis}），以及如何处理带约束的优化问题（\Cref{chap:duality}），最后我们将会给出“多体优化”的基本工具——不动点理论（\Cref{chap:fixed-point-theory}）. 
    \item  \Cref{part:logic-game}，博弈与逻辑：这部分探究AI如何面对其他个体做出决策以及优化，即博弈论，它也为多体智能的研究提供了一个标准的语言（\Cref{chap:game}）. 
    \item  \Cref{part:cognitive-logic}，认知与逻辑：这部分探究AI如形成对其他个体的认知，特别是如何在数学上建模这种认知. 我们将给出两种风格的数学模型：基于Bayes概率论的Bayes博弈（\Cref{chap:bayesian-game}）和基于形式逻辑的模态逻辑（\Cref{chap:modal-logic}）. 
\end{itemize}
"""

print(len(textwrap.wrap(testcontent,1000)))