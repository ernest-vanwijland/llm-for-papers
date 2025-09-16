from tree import *
from api import *
from verifier import *
from solver import *

tree = Tree("2308.05208")

PROOF = """
We are asked to prove Lemma 6.3, which states that for a finite set of points $C \subseteq \mathbb{R}^{d-1}$ with $d \ge 2$, the number of possible orderings $\check{\psi}(C, C)$ is at least $\binom{\psi_1(C)}{2}$.

### Proof of Lemma 6.3

Let $C \subseteq \mathbb{R}^{d-1}$ be a finite set of points. Let $n = |C|$.
Let $\Psi_1(C)$ be the set of orderings of $C$ that can be witnessed by a single vantage point in $\mathbb{R}^{d-1}$. The size of this set is denoted by $\psi_1(C)$. An ordering $\sigma \in \Psi_1(C)$ is a tuple of the points in $C$, $\sigma = (c_{\pi(1)}, c_{\pi(2)}, \dots, c_{\pi(n)})$ for some permutation $\pi$ of $[n]$. An ordering $\sigma$ is witnessed by a vantage point $v \in \mathbb{R}^{d-1}$ if $D_v(c_{\pi(1)}) < D_v(c_{\pi(2)}) < \dots < D_v(c_{\pi(n)})$, where $D_v(c) = \|c-v\|$.

The quantity $\check{\psi}(C, C)$ is the number of distinct orderings of the disjoint union $C \sqcup C$ that can be obtained. Let us denote the two copies of $C$ as $C^{(1)}$ and $C^{(2)}$. For a point $c \in C$, its corresponding point in $C^{(1)}$ is $c^{(1)}$ and in $C^{(2)}$ is $c^{(2)}$. The ordering is determined by the function $\check{D}_V$ for $V = (v_1, v_2, x, y) \in \mathbb{R}^{d-1} \times \mathbb{R}^{d-1} \times \mathbb{R} \times \mathbb{R}_{>0}$.
The function $\check{D}_V$ is defined as:
- For $c^{(1)} \in C^{(1)}$, $\check{D}_V(c^{(1)}) = \check{D}^V_1(c) = \sqrt{x^2 + \|c - v_1\|^2} - x$.
- For $c^{(2)} \in C^{(2)}$, $\check{D}_V(c^{(2)}) = \check{D}^V_2(c) = y\|c - v_2\|^2$.

Our goal is to show that we can generate at least $\binom{\psi_1(C)}{2}$ distinct orderings of $C \sqcup C$ by varying $V$.

Let $S = \Psi_1(C)$. We choose an arbitrary total order $\prec$ on the set $S$. For example, we can order the permutations lexicographically.

Consider the set of all unordered pairs of distinct orderings from $S$:
$$ P = \{\{\sigma_A, \sigma_B\} \mid \sigma_A, \sigma_B \in S, \sigma_A \neq \sigma_B \} $$
The size of this set is $|P| = \binom{|S|}{2} = \binom{\psi_1(C)}{2}$.

For each pair $\{\sigma_A, \sigma_B\} \in P$, we will construct a unique total ordering of $C \sqcup C$. Using the total order $\prec$, we can represent each pair as an ordered pair $(\sigma_1, \sigma_2)$ where $\sigma_1 \prec \sigma_2$. We will construct the specific ordering where all points of $C^{(1)}$, ordered according to $\sigma_1$, appear before all points of $C^{(2)}$, ordered according to $\sigma_2$. We denote this concatenated ordering by $(\sigma_1, \sigma_2)$.

Let $\{\sigma_1, \sigma_2\}$ be a pair in $P$ with $\sigma_1 \prec \sigma_2$.
By definition of $\Psi_1(C)$, there exist vantage points $v_1, v_2 \in \mathbb{R}^{d-1}$ that witness $\sigma_1$ and $\sigma_2$, respectively. We can choose $v_1$ and $v_2$ to be generic, meaning they do not lie on any of the perpendicular bisector hyperplanes of pairs of points in $C$. This ensures that for any distinct $c_i, c_j \in C$, we have $\|c_i - v_1\| \neq \|c_j - v_1\|$ and $\|c_i - v_2\| \neq \|c_j - v_2\|$. We can also choose $v_1, v_2 \notin C$.

Let's analyze the ordering of $C \sqcup C$ induced by $\check{D}_V$ with $V = (v_1, v_2, x, y)$.

1.  **Internal ordering of $C^{(1)}$**: The ordering of points within $C^{(1)}$ is determined by the values $\check{D}^V_1(c) = \sqrt{x^2 + \|c - v_1\|^2} - x$. Let $a = \|c - v_1\|$. For any fixed $x \in \mathbb{R}$, the function $f(a) = \sqrt{x^2 + a^2} - x$ is strictly increasing for $a > 0$. To see this, its derivative with respect to $a$ is $f'(a) = a/\sqrt{x^2+a^2} > 0$. Therefore, the ordering of points in $C^{(1)}$ is determined by the values of $\|c - v_1\|$, which is precisely the ordering $\sigma_1$. This holds for any choice of $x$ and $y$.

2.  **Internal ordering of $C^{(2)}$**: The ordering of points within $C^{(2)}$ is determined by the values $\check{D}^V_2(c) = y\|c - v_2\|^2$. Since $y > 0$, this ordering is determined by the values of $\|c - v_2\|^2$, which is equivalent to the ordering by $\|c - v_2\|$. This is precisely the ordering $\sigma_2$. This holds for any choice of $x$ and $y$.

3.  **Interleaving of $C^{(1)}$ and $C^{(2)}$**: The relative order of a point $c_i^{(1)} \in C^{(1)}$ and a point $c_j^{(2)} \in C^{(2)}$ is determined by the sign of $\check{D}^V_1(c_i) - \check{D}^V_2(c_j)$. We want to show that we can choose $x$ and $y$ such that all points from $C^{(1)}$ come before all points from $C^{(2)}$. This requires $\check{D}^V_1(c_i) < \check{D}^V_2(c_j)$ for all $c_i, c_j \in C$.

Let us fix $v_1$ and $v_2$ as described above. Let us also fix $y=1$. The values $\check{D}^V_2(c_j) = \|c_j - v_2\|^2$ are fixed positive numbers, since $v_2 \notin C$. Let $B_{\min} = \min_{c \in C} \|c - v_2\|^2$. Since $C$ is finite and $v_2 \notin C$, $B_{\min} > 0$.

Now consider the values $\check{D}^V_1(c_i) = \sqrt{x^2 + \|c_i - v_1\|^2} - x$. We analyze the behavior as $x \to +\infty$:
$$ \sqrt{x^2 + a^2} - x = \frac{(\sqrt{x^2 + a^2} - x)(\sqrt{x^2 + a^2} + x)}{\sqrt{x^2 + a^2} + x} = \frac{x^2 + a^2 - x^2}{\sqrt{x^2 + a^2} + x} = \frac{a^2}{\sqrt{x^2 + a^2} + x} $$
As $x \to +\infty$, the denominator goes to $+\infty$, so $\lim_{x \to +\infty} (\sqrt{x^2 + a^2} - x) = 0$.
Let $A_{\max} = \max_{c \in C} \|c - v_1\|^2$. For any $c_i \in C$, we have $0 < \check{D}^V_1(c_i) \le \frac{\|c_i - v_1\|^2}{2x} \le \frac{A_{\max}}{2x}$.
Given $\epsilon > 0$, we can choose $x$ large enough (e.g., $x > A_{\max}/(2\epsilon)$) such that $0 < \check{D}^V_1(c_i) < \epsilon$ for all $c_i \in C$.

Let us choose $\epsilon = B_{\min}$. There exists an $X$ such that for all $x > X$, we have $0 < \check{D}^V_1(c_i) < B_{\min}$ for all $c_i \in C$.
With such a choice of $x$ (e.g., $x=X+1$) and $y=1$, we have for all $c_i, c_j \in C$:
$$ \check{D}^V_1(c_i) < B_{\min} \le \|c_j - v_2\|^2 = \check{D}^V_2(c_j) $$
This shows that there exists a $V = (v_1, v_2, x, 1)$ that realizes the ordering $(\sigma_1, \sigma_2)$.

We have constructed a map from the set of canonical ordered pairs $O = \{(\sigma_1, \sigma_2) \mid \{\sigma_1, \sigma_2\} \in P, \sigma_1 \prec \sigma_2\}$ to the set of achievable orderings $\check{\Psi}(C,C)$.
The size of $O$ is $|P| = \binom{\psi_1(C)}{2}$.

To complete the proof, we must verify that the orderings constructed for different pairs are distinct.
Let $(\sigma_1, \sigma_2)$ and $(\sigma'_1, \sigma'_2)$ be two pairs in $O$. The corresponding constructed orderings are the concatenated orderings, which we also denote by $(\sigma_1, \sigma_2)$ and $(\sigma'_1, \sigma'_2)$.
Suppose $(\sigma_1, \sigma_2) = (\sigma'_1, \sigma'_2)$ as total orderings of $C \sqcup C$.
The ordering $(\sigma_1, \sigma_2)$ is a sequence of $2n$ points. The first $n$ points are the elements of $C^{(1)}$ ordered by $\sigma_1$. The last $n$ points are the elements of $C^{(2)}$ ordered by $\sigma_2$.
If the total orderings are identical, their first $n$ elements must be identical. This implies that the ordering $\sigma_1$ is identical to $\sigma'_1$.
Similarly, their last $n$ elements must be identical, which implies that $\sigma_2$ is identical to $\sigma'_2$.
Thus, the pair $(\sigma_1, \sigma_2)$ is the same as $(\sigma'_1, \sigma'_2)$.
This shows that our construction maps distinct pairs from $P$ to distinct total orderings in $\check{\Psi}(C,C)$.

The number of such constructed orderings is $|O| = \binom{\psi_1(C)}{2}$.
Therefore, the total number of possible orderings $\check{\psi}(C,C)$ must be at least this large.
$$ \check{\psi}(C, C) = |\check{\Psi}(C, C)| \ge |O| = \binom{\psi_1(C)}{2} $$
This completes the proof."""

print(verifier(tree, 16, PROOF))
#print(geminiSolver(tree, 16))















































