prompt_assertion_reason = r"""
Please analyze the image provided and extract any questions present in the text. Format the questions in LaTeX format. If there are any diagrams present, please create only the TikZ environment with a node "Diagram" only, in the center environment. If there are any multiple-choice questions, please put the options in a tasks environment. If there are any assertion-reason type questions, use this code as reference
\begin{enumerate}
    \item[1. Assertion:] This is an assertion.
    \item[Reason:] This is a reason.
\end{enumerate}
Please provide only the enumerated part of the LaTeX file, not the whole LaTeX file.
"""


prompt_solution_with_o4_mini = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image which depicts a physics problem. Generate *only* the complete LaTeX `solution` environment for that problem.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\begin{solution}` and ending precisely after `\end{solution}`. Do **NOT** include *any* problem statement (`\item`), diagram (`tikzpicture`), multiple-choice options (`tasks`), preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure (`solution` Environment)

Follow this exact structure for your output:

1.  **Start:** Begin the output *immediately* with `\begin{solution}`.
2.  **Alignment:** Use an `align*` environment directly inside the `solution` environment.
3.  **Content:**
    *   Show key conceptual steps and reasoning for solving the problem depicted in the image.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step on each line within the `align*` environment.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.
4.  **End:** End the output *immediately* after `\end{solution}`.

---

## Strict LaTeX Formatting Rules (Apply within `solution`)

Adhere to these rules meticulously within the `align*` and `\intertext` environments:

*   **Math Mode:** Use `$ ... $` for *all* inline math (e.g., within `\intertext`).
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## Example Reference Output (Solution Only)

*(This demonstrates the required structure and formatting for the solution block)*

```latex
\begin{solution}
    \begin{align*}
        \intertext{Momentum of the ball will change only along the normal ($x$) direction. Impulse $\vec{J} = \Delta\vec{p} = m\vec{v}_f - m\vec{v}_i$.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} = -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m [ (-0.45 v_0 \hat{i} - 0.6 v_0 \hat{j}) - (0.8 v_0 \hat{i} - 0.6 v_0 \hat{j}) ] \\
        &= m (-0.45 - 0.8) v_0 \hat{i} \\
        &= -1.25 m v_0 \hat{i} = -\frac{5}{4} m v_0 \hat{i}
    \end{align*}
\end{solution}
```

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\begin{solution}` to `\end{solution}` with no extra text or formatting.
"""


prompt_match = r"""
Please analyze the image provided and extract the texts. Format these texts in LaTeX format like this, first put question in \item command, then diagram in tikz env nested within center env if there is any diagram present, then make the table for list/column/anything, then after put the options in a tasks environment. Use this below code as reference:

\item This is a sample question for matching type questions. There are two columns. Match column I with coulmn II. 

\begin{center}
    \begin{tikzpicture}
        \pic {frame=5cm};
    \end{tikzpicture}
\end{center}

\begin{center}
    \renewcommand{\arraystretch}{2}
    \begin{table}[h]
        \centering
        \begin{tabular}{p{0.25cm}p{8cm}|p{0.25cm}p{5cm}}
        \hline
        & Column I & &Column II \\
        \hline
        (a)& When the velocity of $3\kg$ block is $\dfrac{2}{3}\mps$ & (p) &Velocity of center of mass is $\dfrac{2}{3}\mps$\\
        (b)& When the velocity of $6\kg$ block is $\dfrac{2}{3}\mps$ & (q) &Deformation of the spring is zero\\
        (c)& When the speed of $3\kg$ block is minimum  & (r) &Deformation of the spring is maximum\\
        (d)& When the speed of $6\kg$ block is maximum & (s) &Both the blocks are at rest with respect to each other\\
        \hline
        \end{tabular}
    \end{table}
\end{center}

\begin{tasks}(2)
    \task $P \rightarrow 1$, $Q \rightarrow 2$, $R \rightarrow 3$, $S \rightarrow 4$
    \task $P \rightarrow 2$, $Q \rightarrow 1$, $R \rightarrow 4$, $S \rightarrow 3$
    \task $P \rightarrow 3$, $Q \rightarrow 4$, $R \rightarrow 1$, $S \rightarrow 2$
    \task $P \rightarrow 4$, $Q \rightarrow 3$, $R \rightarrow 2$, $S \rightarrow 1$
\end{tasks}

Please provide only the above described part of the LaTeX file, not the whole LaTeX file.
"""


prompt_solution_irodov = r"""
Please analyze the image provided and extract the texts. Format these texts in LaTeX format like this, first put a diagram in tikz env nested within center env if there is any diagram present, dont't code the diagram just put the below sample tikzpicture code instead, then put solution in solution environment, inside align* env use \intertext command for text inside solution, don't put any blank line inside align* env as it will cause rendering problem, use \tag command for numbering equations. Use this code as reference  

\begin{solution}
    \begin{center}
        \begin{tikzpicture}
            \pic at (0, 0) {frame=3cm};
        \end{tikzpicture}
    \end{center}
    
    \begin{align*}
        \intertext{Momentum of the ball will change only along the normal($x$ direction).}
        \vec{J} &= \vec{p}_f-\vec{p}_i\\
        &= m\vec{v}_f-m\vec{v}_i\\
        &= m\left(\dfrac{3}{4}v_0\hat{i}\right)-m\left(v_0\hat{i}\right)\\
        &= -\dfrac{1}{4}mv_0\hat{i}\\
        &= -\dfrac{5}{4}mv_0\hat{i}
        \interttext{Option (a) is correct.}
    \end{align*}
\end{solution}
"""


prompt_maths_inequality = r"""
Please analyze the image provided and extract the texts. Format these texts in LaTeX format like this, use $ $ for inline equation and \[ \] for independent  single line equation. first put problem statement in \item command, then put solution in solution environment, inside align* env use \intertext command for text inside solution, don't put any blank line inside align* env as it will cause rendering problem, use \tag command for numbering equations. Use this code as reference  

\item Which number is greater $(31)^{12}$ or $(17)^{12}$?
    \begin{solution}
        \begin{align*}
            \intertext{Now, } 
            31 &< 32 \\
            \intertext{Raising the power to 12:}
            (31)^{12} &< (32)^{12} \\
            \intertext{Now, } 
            &\implies (31)^{12} < (2^5)^{12} = 2^{60} \tag{1}\\
            \intertext{Now, } 
            2^{60} &< 2^{68} = 2^{4 \cdot 17}\tag{2} \\
            \intertext{Raising the power to 17:}
            (2^4)^{17} &< (16)^{17} \\
            \intertext{Raising the power to 17:}
            (16)^{17} &< (17)^{17}  \tag{3}
            \intertext{From (1), (2), and (3), we get:}
            (31)^{12} &< 2^{60} < 2^{68} < (17)^{17}
            \intertext{Therefore,}
            \Aboxed{(31)^{12} &< (17)^{17}}
        \end{align*}
\end{solution}
"""


prompt_mcq_problem_with_tikz_solution_o4_mini = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice physics question based on the image, including a step-by-step solution and, if applicable, a `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Write the exact physics question based on the image without any modifications.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables.

2.  **TZPlot Diagram (Optional, place immediately after `\item` line if used)**
    *   Include if the image contains a diagram OR if a diagram is necessary for clarity.
    *   Use `tzplot` commands (see reference below).
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your tzplot commands here
            \end{tikzpicture}
        \end{center}
        ```

3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
    *   Use a 2-column `tasks` environment.
    *   Provide four distinct options using `\task`.
    *   Mark the **single** correct answer by appending ` \ans` to the end of its `\task` line.

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step in every line
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Diagrams)

*(Use these `tzplot` commands inside the `tikzpicture` environment if creating a diagram. A good workflow is to define key variables and coordinates first, then draw elements using them.)*

*   **Define Variables:** `\def\myLength{2cm}` `\def\myAngle{30}` (Define lengths, angles, etc. at the start of `tikzpicture`)
*   **Define Coordinates:** `\tzcoor*(x, y)(Name){label}` (defines coordinate 'Name' at (x,y) with a dot and optional label)
*   **Axes:** `\tzaxes(0, 0)(5, 4){$x$}{$y$}`
*   **Vectors/Lines:** `\tzline[->](A)(B)`, `\tzline[-->--](start)(end)` (dashed arrow)
*   **Curve:** `\tzfn"curve"{-.25*(\x)^2+1*\x}[0:4]`
*   **Point on Curve:** `\tzvXpointat{curve}{0.01}(PG)`, `\tzvXpointat*{curve}{0}(PT){$P$}` (with dot)
*   **Point on Function:** `\tzfn[put coordinate=A at 0.01]{\x^2}[0:2]` (marks point 'A' on function)
*   **Tangent:** `\tztangentat[->]{curve}{0.01}[0:1]{$v$}[ar]`
*   **Angle Mark:** `\tzanglemark(A)(B)(C){$\theta$}(15pt)` (angle ABC)
*   **Projections:** `\tzprojx[dashed](P){$x_p$}`, `\tzprojy[dashed](P){$y_p$}`
*   **Ground/Wall:** `\pic[xshift=2cm] (0, 0) {frame=7cm};`

---

## Example Reference Output

*(This demonstrates the required structure and formatting)*

\item A ball of mass $m$ moving with velocity $v_0$ collides a wall as shown in figure. After impact it rebounds with a velocity $\frac{3}{4} v_0$. The impulse acting on ball during impact is
    \begin{center}
        \begin{tikzpicture}
            \tzline+[->](1, 0)(1, 0){$x$}[r]
            \tzline+[->](1, 0)(0, -1){$y$}[b]
            \pic[rotate=90] {frame=4cm};
            \tzline+[dashed](0, 0)(-2, 0)
            \coordinate  (a) at (-2, 1.5);
            \coordinate  (b) at (-2, -2.6);
            \tzdot*(a)(10pt)
            \tzdot*(b)(10pt)
            \tzline[-->--](a)(0, 0)
            \tzline[-->--](0, 0)(b)
            \tzanglemark(a)(0, 0)(-2, 0){$37^\circ$}(15pt)
            \tzanglemark(-2, 0)(0, 0)(b){$53^\circ$}(18pt)
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(2)
        \task $-\frac{m}{2}v_0 \ \hat{\jmath}$
        \task $-\frac{3}{4}mv_0 \ \hat{\imath}$
        \task $-\frac{5}{4}mv_0 \ \hat{\imath}$ \ans
        \task None of the above
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Momentum of the ball will change only along the normal ($x$) direction. Impulse $\vec{J} = \Delta\vec{p} = m\vec{v}_f - m\vec{v}_i$.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} = -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m [ (-0.45 v_0 \hat{i} - 0.6 v_0 \hat{j}) - (0.8 v_0 \hat{i} - 0.6 v_0 \hat{j}) ] \\
        &= m (-0.45 - 0.8) v_0 \hat{i} \\
        &= -1.25 m v_0 \hat{i} = -\frac{5}{4} m v_0 \hat{i}
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""


prompt_mcq_problem_with_solution_o4_mini = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice physics question based on the image, including a step-by-step solution and, if applicable, a `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Write the exact physics question based on the image without any modifications.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables.

2.  **TZPlot Diagram (Optional, place immediately after `\item` line if used)**
    *   Include if the image contains a diagram OR if a diagram is necessary for clarity.
    *   Use `tzplot` commands (see reference below).
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your tzplot commands here
            \end{tikzpicture}
        \end{center}
        ```

3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
    *   Use a 2-column `tasks` environment.
    *   Provide four distinct options using `\task`.
    *   Mark the **single** correct answer by appending ` \ans` to the end of its `\task` line.

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step in every line of calculation.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Diagrams)

*(Use these `tzplot` commands inside the `tikzpicture` environment if creating a diagram. Don't draw complete diagram, just draw the frame and the surface) if necessary otherwise don't draw anything else*

*   **Ground/Wall:** `\pic (surface) at (0, 0) {frame=7cm};`

---

## Example Reference Output

*(This demonstrates the required structure and formatting)*

\item A ball of mass $m$ moving with velocity $v_0$ collides a wall as shown in figure. After impact it rebounds with a velocity $\frac{3}{4} v_0$. The impulse acting on ball during impact is
    \begin{center}
        \begin{tikzpicture}
            \pic (surface) at (0, 0) {frame=5cm};
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(2)
        \task $-\frac{m}{2}v_0 \ \hat{\jmath}$
        \task $-\frac{3}{4}mv_0 \ \hat{\imath}$
        \task $-\frac{5}{4}mv_0 \ \hat{\imath}$ \ans
        \task None of the above
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Momentum of the ball will change only along the normal ($x$) direction. Impulse $\vec{J} = \Delta\vec{p} = m\vec{v}_f - m\vec{v}_i$.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} = -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m [ (-0.45 v_0 \hat{i} - 0.6 v_0 \hat{j}) - (0.8 v_0 \hat{i} - 0.6 v_0 \hat{j}) ] \\
        &= m (-0.45 - 0.8) v_0 \hat{i} \\
        &= -1.25 m v_0 \hat{i} = -\frac{5}{4} m v_0 \hat{i}
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""


prompt_mcq_problem_with_solution_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice physics question based **exactly** on the image, including a step-by-step solution (which identifies all correct options) and, if applicable, a simplified `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Extract the **exact** physics question text from the image **without any modifications or additions**.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables as they appear in the image.

2.  **TZPlot Diagram (Optional, place immediately after `\item` line if used)**
    *   Include *only* if the image contains a diagram OR if a diagram is essential for understanding the extracted text.
    *   Use `tzplot` commands (see reference below). **Only draw the frame/surface if necessary.** Do not draw other elements.
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your simplified tzplot commands here (e.g., \pic)
            \end{tikzpicture}
        \end{center}
        ```

3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
    *   Use a 2-column `tasks` environment.
    *   Extract the **exact** option text from the image **without any modifications**.
    *   Provide the options using `\task`.
    *   Based on your analysis in the solution step, mark **every** correct answer by appending ` \ans` to the end of its corresponding `\task` line.

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem based on the extracted text.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   **Critically:** Analyze the problem to determine if it's single-correct or multi-correct. Evaluate *each* extracted option explicitly (e.g., "Checking option (a): ... This is correct/incorrect."). State the final correct options by letter (e.g., "Therefore, the correct option is (c)." or "Therefore, the correct options are (a) and (c)."). This analysis justifies the `\ans` markings in the `tasks` environment.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step in every line of calculation.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Simplified Diagrams)

*(Only use the following if a simple surface/frame diagram is needed)*

*   **Ground/Wall:** `\pic (surface) at (0, 0) {frame=7cm};`

---

## Example Reference Output (Illustrating Multi-Correct Handling)

*(This demonstrates how the structure handles a problem determined to be multi-correct during the solution phase, even if the extracted question wasn't explicitly phrased as multi-correct. The key is exact extraction first, then analysis.)*

\item A ball of mass $m$ moving with velocity $v_0$ collides a wall as shown in figure. After impact it rebounds with a velocity $\frac{3}{4} v_0$. Select the correct statement(s).
    \begin{center}
        \begin{tikzpicture}
            \pic (surface) [rotate=90] at (0, 0) {frame=4cm}; % Example using the simplified diagram command
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(2)
        \task The component of impulse along $\hat{\jmath}$ is zero. \ans
        \task The magnitude of impulse is $\frac{3}{4}mv_0$.
        \task The impulse vector is $-\frac{5}{4}mv_0 \ \hat{\imath}$ (using standard angle approximations). \ans
        \task The impulse is purely vertical.
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Let the initial velocity be $\vec{v}_i$ and final velocity be $\vec{v}_f$. Impulse $\vec{J} = \Delta\vec{p} = m(\vec{v}_f - \vec{v}_i)$. Assume standard angles $37^\circ$ and $53^\circ$ as implied by similar problems.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} \\
        &= -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m [ (-0.45 v_0 \hat{i} - 0.6 v_0 \hat{j}) - (0.8 v_0 \hat{i} - 0.6 v_0 \hat{j}) ] \\
        &= m [ (-0.45 - 0.8) v_0 \hat{i} + (-0.6 - (-0.6)) v_0 \hat{j} ] \\
        &= m \left[ -1.25 v_0 \hat{i} + 0 \hat{j} \right] \\
        &= -1.25 m v_0 \hat{i} = -\frac{5}{4} m v_0 \hat{i} \\
        \intertext{Now checking the options based on the extracted text:}
        \intertext{(a) Option states: "The component of impulse along $\hat{\jmath}$ is zero." Our calculated $\vec{J}$ has a zero $\hat{j}$ component. So, option (a) is correct.}
        \intertext{(b) Option states: "The magnitude of impulse is $\frac{3}{4}mv_0$." Our calculated magnitude is $|\vec{J}| = \frac{5}{4} m v_0$. So, option (b) is incorrect.}
        \intertext{(c) Option states: "The impulse vector is $-\frac{5}{4}mv_0 \ \hat{\imath}$ (using standard angle approximations)." This matches our calculated $\vec{J}$. So, option (c) is correct.}
        \intertext{(d) Option states: "The impulse is purely vertical." Our calculated $\vec{J}$ is purely horizontal. So, option (d) is incorrect.}
        \intertext{Based on the analysis, the problem allows for multiple correct statements. Therefore, the correct options are (a) and (c).}
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""

prompt_mcq_single_correct_problem_with_solution_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice physics question based **exactly** on the image, assuming it has a **single correct answer**. Include a step-by-step solution (which identifies the correct option) and, if applicable, a simplified `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Extract the **exact** physics question text from the image **without any modifications or additions**.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables as they appear in the image.

2.  **TZPlot Diagram (Optional, place immediately after `\item` line if used)**
    *   Include *only* if the image contains a diagram OR if a diagram is essential for understanding the extracted text.
    *   Use `tzplot` commands (see reference below). **Only draw the frame/surface if necessary.** Do not draw other elements.
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your simplified tzplot commands here (e.g., \pic)
            \end{tikzpicture}
        \end{center}
        ```

3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
    *   Use a 2-column `tasks` environment.
    *   Extract the **exact** option text from the image **without any modifications**.
    *   Provide the options using `\task`.
    *   Based on your analysis in the solution step, mark the **single** correct answer by appending ` \ans` to the end of its corresponding `\task` line.

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem based on the extracted text.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   **Critically:** Evaluate the options to identify the **single** correct answer. Explain why it is correct and briefly why others might be incorrect if helpful for clarity. State the final correct option by letter (e.g., "Therefore, the correct option is (c)."). This analysis justifies the `\ans` marking in the `tasks` environment.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step in every line of calculation.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Simplified Diagrams)

*(Only use the following if a simple surface/frame diagram is needed)*

*   **Ground/Wall:** `\pic (surface) at (0, 0) {frame=7cm};`

---

## Example Reference Output (Single Correct Answer)

*(This demonstrates the required structure for a single-correct answer question)*

\item A ball of mass $m$ moving with velocity $v_0$ collides a wall as shown in figure. After impact it rebounds with a velocity $\frac{3}{4} v_0$. The impulse acting on ball during impact is
    \begin{center}
        \begin{tikzpicture}
            \pic (surface) [rotate=90] at (0, 0) {frame=4cm}; % Example using the simplified diagram command
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(2)
        \task $-\frac{m}{2}v_0 \ \hat{\jmath}$
        \task $-\frac{3}{4}mv_0 \ \hat{\imath}$
        \task $-\frac{5}{4}mv_0 \ \hat{\imath}$ \ans
        \task None of the above
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Let the initial velocity be $\vec{v}_i$ and final velocity be $\vec{v}_f$. Impulse $\vec{J} = \Delta\vec{p} = m(\vec{v}_f - \vec{v}_i)$. Assume standard angles $37^\circ$ and $53^\circ$ as implied by similar problems.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} \\
        &= -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m [ (-0.45 v_0 \hat{i} - 0.6 v_0 \hat{j}) - (0.8 v_0 \hat{i} - 0.6 v_0 \hat{j}) ] \\
        &= m [ (-0.45 - 0.8) v_0 \hat{i} + (-0.6 - (-0.6)) v_0 \hat{j} ] \\
        &= m (-1.25 v_0 \hat{i} + 0 \hat{j}) \\
        &= -1.25 m v_0 \hat{i} = -\frac{5}{4} m v_0 \hat{i} \\
        \intertext{Comparing this result with the options:}
        \intertext{(a) $-\frac{m}{2}v_0 \hat{j}$ is incorrect as the impulse is purely along $\hat{i}$.}
        \intertext{(b) $-\frac{3}{4}mv_0 \hat{i}$ is incorrect.}
        \intertext{(c) $-\frac{5}{4}mv_0 \hat{i}$ matches our calculation.}
        \intertext{(d) Since (c) is correct, 'None of the above' is incorrect.}
        \intertext{Therefore, the correct option is (c).}
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""


prompt_mcq_single_correct_problem_only_solution_with_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided **LaTeX input** (which includes a multiple-choice physics question, options, potentially a TikZ diagram, and a **preliminary solution** block). Critique and **refine** the provided solution, ensuring correctness, clarity, and adherence to formatting standards. Add a conceptual explanation block using `tcolorbox`. Assume the problem has a **single correct answer**.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw, **refined** LaTeX code snippet starting precisely with `\begin{solution}` and ending precisely after `\end{solution}`. This output will contain the new concept box and the refined step-by-step derivation. Do **NOT** include the original input or any text outside of this refined `solution` block.

---

## Required LaTeX Structure (Refined `solution` Environment)

Follow this exact structure for your **output**:

1.  **Start:** Begin the output *immediately* with `\begin{solution}`.
2.  **Concept Explanation (`tcolorbox`)**:
    *   Immediately after `\begin{solution}`, insert a `tcolorbox` environment.
    *   Inside the `tcolorbox`, provide a brief explanation of the core physics concept(s) needed to solve the problem.
    *   Use clear explanatory text.
    *   If defining formulas or key conceptual equations, use an `align*` environment *inside* the `tcolorbox` for proper formatting. You can add text before/after this inner `align*` or use `\intertext` within it if appropriate.
3.  **Step-by-Step Derivation (`align*`)**:
    *   Immediately after the `tcolorbox`, use an `align*` environment for the main calculation.
    *   Show key conceptual steps and reasoning for solving the problem, refining the logic from the preliminary solution provided in the input. Correct any errors found.
    *   Use `\intertext{}` for brief text explanations *between* equation lines, ensuring clarity and conciseness. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   **Critically:** Evaluate the options from the input LaTeX to identify the **single** correct answer based on your refined derivation. State the final correct option by letter (e.g., "Therefore, the correct option is (c).").
    *   Keep the solution concise and elegant. Omit trivial intermediate algebra where appropriate but ensure logical flow.
    *   Align equations using `&` (typically at relation symbols like `=`). Use `\\` to end *each* line of the derivation. **Crucially, if a calculation spans multiple lines using alignment (e.g., `A &= B \\ &= C`), each `&=` (or similar aligned operator) must start on a new line.**
    *   **Strictly forbidden:** Do **not** leave any blank lines inside this main `align*` environment.
4.  **End:** End the output *immediately* after `\end{solution}`.

---

## Strict LaTeX Formatting Rules (Apply within refined `solution`)

Adhere to these rules meticulously within the `tcolorbox` and the main `align*` environment:

*   **Math Mode:** Use `$ ... $` for *all* inline math. Use `align*` for displayed equations.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.
*   **Environments:** Ensure `tcolorbox` and `align*` environments are properly nested and closed. No blank lines within `align*`.

---

## Example Reference Input (Illustrative LaTeX Problem with Preliminary Solution)

*(This is an example of the LaTeX input you would receive)*

```latex
\item A ball of mass $m$ moving with velocity $v_0$ collides a wall as shown in figure. After impact it rebounds with a velocity $\frac{3}{4} v_0$. The impulse acting on ball during impact is
    \begin{center}
        \begin{tikzpicture}
            \pic (surface) [rotate=90] at (0, 0) {frame=4cm}; % Example diagram
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(2)
        \task $-\frac{m}{2}v_0 \ \hat{\jmath}$
        \task $-\frac{3}{4}mv_0 \ \hat{\imath}$
        \task $-\frac{5}{4}mv_0 \ \hat{\imath}$ \ans % Preliminary answer marked
        \task None of the above
    \end{tasks}
\begin{solution} % Preliminary solution provided in input
    \begin{align*}
        J &= p_f - p_i \\
        &= m v_f - m v_i \\
        v_i &= v_0 \cos(37) i - v_0 \sin(37) j \\
        v_f &= -0.75 v_0 \cos(53) i - 0.75 v_0 \sin(53) j \\
        J &= m(-0.75 v_0 (0.6) i - 0.75 v_0 (0.8) j) - m(v_0 (0.8) i - v_0 (0.6) j) \\
        &= m(-0.45 v_0 i - 0.6 v_0 j - 0.8 v_0 i + 0.6 v_0 j) \\
        &= -1.25 m v_0 i
    \end{align*}
\end{solution}
```

---

## Example Reference Output (Refined Solution Only)

*(Based on the example input above, this is the expected output: the refined solution block)*

```latex
\begin{solution}
    \begin{tcolorbox}[colback=blue!5!white,colframe=blue!75!black,title=Concept: Impulse-Momentum Theorem]
        The impulse $\vec{J}$ delivered to an object equals the change in its momentum $\Delta\vec{p}$. Momentum $\vec{p}$ is the product of mass $m$ and velocity $\vec{v}$.
        \begin{align*}
            \vec{J} &= \Delta\vec{p} \\
            \vec{J} &= \vec{p}_f - \vec{p}_i \\
            \vec{J} &= m\vec{v}_f - m\vec{v}_i = m(\vec{v}_f - \vec{v}_i)
        \end{align*}
        We need to resolve the initial and final velocities into components along the chosen axes (typically normal and tangential to the surface).
    \end{tcolorbox}
    \begin{align*}
        \intertext{Let the initial velocity be $\vec{v}_i$ and final velocity be $\vec{v}_f$. Use the axes shown implicitly (normal $\hat{i}$, tangential $-\hat{j}$). Assume standard angles $37^\circ$ and $53^\circ$ based on context.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} \\
        &= -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \intertext{Now calculate the impulse using the Impulse-Momentum Theorem:}
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m \left[ \left( -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \right) - \left( 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \right) \right] \\
        &= m \left[ (-0.45 - 0.8) v_0 \hat{i} + (-0.6 - (-0.6)) v_0 \hat{j} \right] \\
        &= m \left[ -1.25 v_0 \hat{i} + 0 \hat{j} \right] \\
        &= -1.25 m v_0 \hat{i} \\
        &= -\frac{5}{4} m v_0 \hat{i} \\
        \intertext{Therefore, the correct option is (c).}
    \end{align*}
\end{solution}
```

---

**Final Check:** Ensure your output is ONLY the refined LaTeX snippet from `\begin{solution}` to `\end{solution}` with no extra text or comments.
"""


prompt_mcq_single_correct_problem_refine_solution_with_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided **LaTeX input** (which includes a multiple-choice physics question, options, potentially a TikZ diagram for the problem, and a **preliminary solution block**). The preliminary solution block itself might contain its own TikZ diagrams and/or alternative solution paths.
Critique and **refine** the provided solution, ensuring correctness, clarity, and adherence to formatting standards.
1.  Add a conceptual explanation block using a specifically styled `tcolorbox` with a `sidebyside` layout: a conceptual diagram (if applicable) on the left, and explanatory text with formulas on the right.
2.  Preserve any TikZ diagram found *within* the input's `\begin{solution}...\end{solution}` block (that is part of the main solution flow, not the concept box), placing it after the `tcolorbox`.
3.  Refine the primary step-by-step derivation.
4.  Preserve and refine any "Alternative Solution" found within the input's `\begin{solution}...\end{solution}` block, placing it after the primary derivation.
Assume the problem has a **single correct answer** (the primary solution should conclude this).

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw, **refined** LaTeX code snippet starting precisely with `\begin{solution}` and ending precisely after `\end{solution}`. This output will contain the new concept box, any preserved TikZ diagram from the input solution, the refined primary derivation, and any preserved alternative solution. Do **NOT** include the original input's problem statement, options, or main diagram, nor any text outside of this refined `solution` block.

---

## Required LaTeX Structure (Refined `solution` Environment)

Follow this exact structure for your **output**:

1.  **Start:** Begin the output *immediately* with `\begin{solution}`.
2.  **Concept Explanation (`tcolorbox` with `sidebyside`)**:
    *   Immediately after `\begin{solution}`, insert a `tcolorbox` environment.
    *   **Use the following specific style definition for this `tcolorbox`**:
        Options: `[enhanced, fonttitle=\scshape, title=Concept: <Relevant Concept Name>, sidebyside, bicolor, colback=white, colbacklower=black!10, colframe=black!75, lefthand width=4.5cm, overlay={\begin{tcbclipinterior}\fill[pattern=dots, pattern color=black!25](interior.south west) rectangle (interior.north east);\end{tcbclipinterior}}]`. Replace `<Relevant Concept Name>` with the actual concept.
    *   **Content of the `tcolorbox`**:
        *   **Left-hand side (before `\tcblower`)**: If a simple diagram helps illustrate the core concept (distinct from the main problem's diagram), place it here, typically within a `\begin{center}\begin{tikzpicture}...\end{tikzpicture}\end{center}` block. If no diagram is suitable for the *concept explanation itself*, this side can be left for very brief key terms or kept minimal.
        *   `\tcblower` : This command separates the left and right sides.
        *   **Right-hand side (after `\tcblower`)**: Provide the main textual explanation of the core physics concept(s). Follow this text with key formulas or definitions relevant to the concept, using an `align*` environment for proper formatting of these mathematical expressions.
3.  **Preserved TikZ Diagram from Input Solution (Optional)**:
    *   If the **input's** `\begin{solution}...\end{solution}` block contains a `\begin{tikzpicture}...\end{tikzpicture}` environment (intended as part of the *solution steps*, not the concept explanation), reproduce it faithfully here, immediately after the `tcolorbox`. Typically, this would be wrapped in a `\begin{center}...\end{center}` environment.
4.  **Primary Step-by-Step Derivation (`align*`)**:
    *   Immediately after the (optional) preserved TikZ diagram (or after the `tcolorbox` if no diagram), use an `align*` environment for the main calculation.
    *   Show key conceptual steps and reasoning, refining the logic from the preliminary solution provided in the input. Correct any errors found.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   **Critically:** Evaluate the options from the input LaTeX to identify the **single** correct answer based on your refined derivation. State the final correct option by letter (e.g., "Therefore, the correct option is (c).").
    *   Keep the solution concise and elegant. Align equations using `&`. Use `\\` to end *each* line. If a calculation spans multiple lines (e.g., `A &= B \\ &= C`), each `&=` must start on a new line.
    *   **Strictly forbidden:** No blank lines inside this `align*` environment.
5.  **Alternative Solution (Optional)**:
    *   If the **input's** `\begin{solution}...\end{solution}` block contains a clearly demarcated alternative solution (e.g., introduced by text like "Alternative Method:", or another distinct `align*` block), reproduce and refine that alternative solution here.
    *   This might involve an `\intertext{}` followed by another `align*` environment or other appropriate formatting based on the input.
6.  **End:** End the output *immediately* after `\end{solution}`.

---

## Strict LaTeX Formatting Rules (Apply within refined `solution`)

Adhere to these rules meticulously:

*   **Math Mode:** `$ ... $` for inline math. `align*` for displayed equations.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** `\vec{a}` for generic vectors, `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** `\frac{a}{b}`. No `\tfrac`.
*   **Parentheses/Brackets:** `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. No `\bigl`, `\bigr`, etc.
*   **Environments:** Ensure `tcolorbox`, `tikzpicture`, `center`, `align*` are properly nested and closed. No blank lines within `align*`.

---

## Example Reference Input (Illustrative LaTeX Problem with Preliminary Solution, TikZ in solution, and Alternative)

*(This is an example of the LaTeX input you would receive)*

```latex
\item A particle is projected with velocity $u$ at an angle $\theta$ with the horizontal. Find the time of flight.
    \begin{center}
        % Main problem diagram if any - NOT part of what this prompt processes for output
        \begin{tikzpicture}
            \draw[->] (0,0) -- (5,0) node[right]{$x$};
            \draw[->] (0,0) -- (0,3) node[above]{$y$};
            \draw[dashed] (0,0) parabola (4,2);
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(1)
        \task $\frac{u \sin\theta}{g}$
        \task $\frac{2u \sin\theta}{g}$ \ans % Preliminary ans
        \task $\frac{u \cos\theta}{g}$
        \task $\frac{2u \cos\theta}{g}$
    \end{tasks}
\begin{solution} % Preliminary solution provided in input
    Vertical motion: $y = u_y t - \frac{1}{2}gt^2$.
    When particle lands, $y=0$.
    So, $u \sin\theta t - \frac{1}{2}gt^2 = 0$.
    $t(u \sin\theta - \frac{1}{2}gt) = 0$.
    $t=0$ or $t = \frac{2u\sin\theta}{g}$.

    \begin{center} % TikZ diagram intended for the main solution steps
        \begin{tikzpicture}
            \node[draw, circle, label=above:Path] at (0,0) {Trajectory};
            \draw[->] (0,-0.5) -- (0,-1.5) node[below]{$g$};
        \end{tikzpicture}
    \end{center}

    Alternative Method:
    Time to reach max height $t_h = u_y/g = u\sin\theta/g$.
    Total time $T = 2 t_h = 2u\sin\theta/g$.
\end{solution}
```

---

## Example Reference Output (Refined Solution Only)

*(Based on the example input above, this is the expected output: the refined solution block)*

```latex
\begin{solution}
    \begin{tcolorbox}[
        enhanced, 
        fonttitle=\scshape, 
        title=Concept: Projectile Motion Analysis, 
        sidebyside, 
        bicolor, 
        colback=white, 
        colbacklower=black!10, 
        colframe=black!75, 
        lefthand width=4.5cm, 
        overlay={
            \begin{tcbclipinterior}
                \fill[pattern=dots, pattern color=black!25](interior.south west) rectangle (interior.north east);
            \end{tcbclipinterior}
            }
        ]
        % Left-hand side: Conceptual Diagram (if applicable)
        \begin{center}
            \begin{tikzpicture} % Simple diagram for concept
                \draw[->, thick] (0,1) node[left]{$u_y$} -- (0,0) -- (1,0) node[below]{$u_x$};
                \draw[->, thick] (0.5,0.5) -- (1.5,1) node[right]{$\vec{u}$};
                \draw (0.3,0) arc (0:atan(1/1):0.3) node[midway, right]{$\theta$};
            \end{tikzpicture}
        \end{center}
        \tcblower
        % Right-hand side: Explanatory text and Key Conceptual Formulas
        For projectile motion, we analyze horizontal and vertical components of velocity independently. Initial vertical velocity is $u_y = u \sin\theta$, and initial horizontal velocity is $u_x = u \cos\theta$. The vertical motion is uniformly accelerated due to gravity ($a_y = -g$), while horizontal motion is uniform ($a_x = 0$), ignoring air resistance.
        Key equations for vertical motion (starting from $y_0=0$):
        \begin{align*}
            y(t) &= u_y t - \frac{1}{2}gt^2 \\
            v_y(t) &= u_y - gt
        \end{align*}
        The time of flight $T$ is the total time the projectile is in the air until it returns to $y=0$.
    \end{tcolorbox}
    \begin{center} % This is the TikZ diagram preserved from the INPUT's solution block
        \begin{tikzpicture}
            \node[draw, circle, label=above:Path] at (0,0) {Trajectory};
            \draw[->] (0,-0.5) -- (0,-1.5) node[below]{$g$};
        \end{tikzpicture}
    \end{center}
    \begin{align*}
        \intertext{Let $u_y = u \sin\theta$ be the initial vertical component of velocity. The vertical displacement $y$ is given by $y(t) = u_y t - \frac{1}{2}gt^2$. The particle lands when $y(t) = 0$ (assuming projection from $y_0=0$).}
        u \sin\theta \cdot t - \frac{1}{2}gt^2 &= 0 \\
        t \left( u \sin\theta - \frac{1}{2}gt \right) &= 0 \\
        \intertext{This gives two solutions for $t$: $t=0$ (initial projection point) and the time of flight $T$ when the second factor is zero:}
        u \sin\theta - \frac{1}{2}gT &= 0 \\
        \frac{1}{2}gT &= u \sin\theta \\
        T &= \frac{2u \sin\theta}{g} \\
        \intertext{Comparing with the options, option (b) is $\frac{2u \sin\theta}{g}$. This matches our result.}
        \intertext{Therefore, the correct option is (b).}
    \end{align*}
    \begin{align*}
    \intertext{\textbf{Alternative Method}: Using symmetry}
        \intertext{The time taken to reach the maximum height ($t_h$) is when the vertical component of velocity becomes zero. $v_y(t_h) = u_y - gt_h = 0$.}
        t_h &= \frac{u_y}{g} \\
        &= \frac{u \sin\theta}{g} \\
        \intertext{The total time of flight $T$ is twice the time taken to reach maximum height, due to the symmetry of the parabolic trajectory (assuming projection and landing at the same vertical level).}
        T &= 2 t_h \\
        &= 2 \left( \frac{u \sin\theta}{g} \right) \\
        &= \frac{2u \sin\theta}{g}
    \end{align*}
\end{solution}
```

---

**Final Check:** Ensure your output is ONLY the refined LaTeX snippet from `\begin{solution}` to `\end{solution}` with no extra text or comments.
"""


prompt_subjective_problem_with_solution_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX **subjective** physics question based **exactly** on the image. Include a detailed, step-by-step solution and, if applicable, a simplified `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Extract the **exact** physics question text from the image **without any modifications or additions**.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables as they appear in the image.

2.  **TZPlot Diagram (Optional, place immediately after `\item` line if used)**
    *   Include *only* if the image contains a diagram **or** if a diagram is essential for understanding the extracted text.
    *   Use `tzplot` commands (see reference below). **Only draw the frame/surface if necessary.** Do not draw additional elements.
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your simplified tzplot commands here (e.g., \pic)
            \end{tikzpicture}
        \end{center}
        ```

3.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem based on the extracted text.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   Keep the solution concise and elegant. Omit trivial intermediate algebra where appropriate while ensuring logical flow.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep **only one step** in every line of calculation.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Simplified Diagrams)

*(Only use the following if a simple surface/frame diagram is needed)*

*   **Ground/Wall:** `\pic (surface) at (0, 0) {frame=7cm};`

---

## Example Reference Output (Subjective Question)

*(This demonstrates the required structure for a subjective question)*

\item A ball of mass $m$ moving with velocity $v_0$ collides with a wall as shown in the figure. After impact, it rebounds with a velocity $\frac{3}{4} v_0$. Calculate the impulse acting on the ball during impact.
    \begin{center}
        \begin{tikzpicture}
            \pic (surface) [rotate=90] at (0,0) {frame=4cm};
        \end{tikzpicture}
    \end{center}
\begin{solution}
    \begin{align*}
        \intertext{Let the initial velocity be $\vec{v}_i$ and final velocity be $\vec{v}_f$. Impulse $\vec{J} = \Delta\vec{p} = m(\vec{v}_f - \vec{v}_i)$.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using $\cos(37^\circ)\approx\sin(53^\circ)\approx0.8$ and $\sin(37^\circ)\approx\cos(53^\circ)\approx0.6$:}
        \vec{v}_i &\approx 0.8v_0\hat{i} - 0.6v_0\hat{j} \\
        \vec{v}_f &\approx -0.45v_0\hat{i} - 0.6v_0\hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m\left[(-0.45 - 0.8)v_0\hat{i} + (-0.6 - (-0.6))v_0\hat{j}\right] \\
        &= -1.25mv_0\hat{i} \\
        &= -\frac{5}{4}mv_0\hat{i}
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""

prompt_mcq_maths_single_correct_problem_with_solution_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice **mathematics** question based **exactly** on the image, assuming it has a **single correct answer**. Include a step-by-step solution (which identifies the correct option) and, if applicable, a simplified `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Extract the **exact** mathematics question text from the image **without any modifications or additions**.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables as they appear in the image.

2.  **TZPlot Diagram (Optional, place immediately after `\item` line if used)**
    *   Include *only* if the image contains a diagram OR if a diagram is essential for understanding the extracted text.
    *   Use `tzplot` commands (see reference below). **Only draw the frame/surface if necessary.** Do not draw other elements.
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your simplified tzplot commands here (e.g., \pic)
            \end{tikzpicture}
        \end{center}
        ```

3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
    *   Use a 2-column `tasks` environment.
    *   Extract the **exact** option text from the image **without any modifications**.
    *   Provide the options using `\task`.
    *   Based on your analysis in the solution step, mark the **single** correct answer by appending ` \ans` to the end of its corresponding `\task` line.

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem based on the extracted text.
    *   Use `\intertext{}` for concise explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   **Critically:** Evaluate the options to identify the **single** correct answer and demonstrate why it is correct (and why others are not) **without** adding a concluding line such as `\intertext{Therefore, the correct option is (c).}`.
    *   Keep the solution concise and elegant, omitting trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end each line of the derivation.
    *   Keep only one step on every line of calculation.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\frac{a}{b}`, `\sqrt{\,}`, etc.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Simplified Diagrams)

*(Only use the following if a simple surface/frame diagram is needed)*

*   **Ground/Wall:** `\pic (surface) at (0, 0) {frame=7cm};`

---

## Example Reference Output (Single Correct Answer)

*(This demonstrates the required structure for a mathematics problem. Notice there is **no** final intertext stating the correct option explicitly.)*

\item Evaluate the limit $\displaystyle \lim_{x\to 0} \frac{\sin 3x}{x}$.
    \begin{tasks}(2)
        \task $1$
        \task $2$
        \task $3$ \ans
        \task $4$
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Using the standard limit $\displaystyle \lim_{x\to 0} \frac{\sin x}{x} = 1$:}
        \lim_{x\to 0} \frac{\sin 3x}{x} &= \lim_{x\to 0} \left( 3 \cdot \frac{\sin 3x}{3x} \right) \\
        &= 3 \cdot 1 \\
        &= 3
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""


prompt_match_problem_with_solution_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX *matching–type* question (two columns to be matched) including a detailed, step-by-step solution.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Write the exact question text extracted from the image without modification.
    *   Use inline math mode `$ ... $` for every mathematical symbol.

2.  **Optional Diagram**
    *   If the image contains a diagram **or** a diagram aids understanding, place a minimal placeholder diagram **immediately** after the `\item` line, wrapped like this:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % your tzplot commands (e.g. \pic {frame=5cm};)
            \end{tikzpicture}
        \end{center}
        ```

3.  **Matching Table**
    *   Reproduce the two columns (Column I and Column II) exactly as in the image using a `table` environment inside another `center` environment – see the *Example Reference Output* below for formatting.
    *   You **must** precede the `tabular` with `\renewcommand{\arraystretch}{2}` so that rows are comfortably spaced.

4.  **Multiple-Choice Mapping Options (`tasks` environment)**
    *   Provide the mapping options in a 2-column `tasks` environment (`\begin{tasks}(2)` … `\end{tasks}`).
    *   Extract the option text exactly.  Append ` \ans` to the **single** correct option identified in the solution.

5.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Inside `solution`, use a single `align*` environment.
    *   Show concise yet complete reasoning that leads to the correct mapping.
    *   Use `\intertext{}` for short textual explanations between the aligned equation lines.
    *   Align at relation symbols (`&=` etc.) and keep **exactly one logical step per line**.
    *   **Do not** leave blank lines inside `align*`.

---

## Strict LaTeX Formatting Rules

*   **Math Mode:** `$ ... $` for all inline math.
*   **Macros:** Always use curly braces – e.g. `\frac{a}{b}`, `\vec{A}`.
*   **Fractions:** Use `\frac{a}{b}`; *never* `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. Never use `\bigl`, `\bigr`, etc.
*   **Vectors & Units:** Use `\vec{a}`, `\hat{i}`, `\mathrm{m\,s^{-1}}`, etc. as appropriate.

---

## Example Reference Output

```latex
\item Four situations for a spring–block system are listed in Column I.  Match them with the corresponding statements in Column II.
    \begin{center}
        \begin{tikzpicture}
            \pic {frame=5cm};
        \end{tikzpicture}
    \end{center}

    \begin{center}
        \renewcommand{\arraystretch}{2}
        \begin{table}[h]
            \centering
            \begin{tabular}{p{0.25cm}p{7cm}|p{0.25cm}p{4.5cm}}
            \hline
            & Column I & & Column II \\
            \hline
            (a) & $x = x_{\text{max}}$ & (p) & Spring potential energy is maximum \\
            (b) & $x = 0$ & (q) & Kinetic energy is maximum \\
            (c) & $v = 0$ & (r) & Acceleration is maximum \\
            (d) & $a = 0$ & (s) & Force on block is zero \\
            \hline
            \end{tabular}
        \end{table}
    \end{center}

    \begin{tasks}(2)
        \task $p\to1,\;q\to2,\;r\to3,\;s\to4$
        \task $p\to2,\;q\to1,\;r\to4,\;s\to3$ \ans
        \task $p\to3,\;q\to4,\;r\to1,\;s\to2$
        \task None of these
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{At $x = x_{\text{max}}$ the spring is at extreme compression/extension, so $v=0$ and potential energy is maximum. Hence (a)$\to$p.}
        E_{\text{spring,max}} &= \frac{1}{2}k x_{\text{max}}^2 \\
        \intertext{At $x = 0$ the block passes through equilibrium, acceleration is zero and kinetic energy is maximum. Hence (b)$\to$q and (d)$\to$s.}
        a &= -\frac{k}{m}x \;\Rightarrow\; a=0 \text{ at } x=0 \\
        \intertext{When $v=0$ (turning points) the block is momentarily at rest while acceleration is maximum in magnitude: (c)$\to$r.}
        a_{\text{max}} &= \frac{k}{m}x_{\text{max}} \\
    \end{align*}
\end{solution}
```

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""

prompt_comprehension_problem_with_solution_o3 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image and generate a *comprehension-type* LaTeX snippet that contains:
1.  A centred passage title (if any).
2.  The passage text exactly as it appears.
3.  An optional TikZ diagram (placeholder only) if one is present in, or helpful for, the image.
4.  A series of follow-up questions, each with its own multiple-choice options.
5.  **A separate `solution` block placed *immediately after every individual question*** – i.e. the pattern must be:
   ```latex
   \item <Question-1 text>
       <tasks env for options>
   \begin{solution}
       \begin{align*}
           ...steps for Q-1...
       \end{align*}
   \end{solution}

   \item <Question-2 text>
       <tasks env for options>
   \begin{solution}
       ...
   \end{solution}
   ```
   This ensures the reader sees the solution just below each problem statement.

**CRITICAL OUTPUT CONSTRAINT:** Emit *only* the LaTeX snippet starting with the passage title's `center` environment (or the first `\item` if no title) and ending after the final `\end{solution}`. Do **NOT** add any preamble, `\documentclass`, `\begin{document}`, or explanatory comments outside the snippet.

---

## Detailed LaTeX Structure

1.  **Title (optional)**
    ```latex
    \item[]
    \begin{center}
        \textsc{<Title from image>}
    \end{center}
    ```

2.  **Passage** – Write the paragraph exactly as-is (no surrounding environment).

3.  **Optional Diagram** (placeholder only, if a diagram exists OR is essential):
    ```latex
    \begin{center}
        \begin{tikzpicture}
            \pic {frame=3cm};
        \end{tikzpicture}
    \end{center}
    ```

4.  **Each Question-Solution pair**
    *   Begin with `\item` followed by the question text.
    *   Provide the options in a `tasks` environment.  Use two columns unless the image shows otherwise.
    *   Append ` \ans` to every correct option (single- or multi-correct).
    *   Insert a `solution` environment directly after the `tasks` block.  Inside it use **one** `align*` environment.
    *   Use `\intertext{}` to mix concise prose with math lines.  Keep **one logical step per line** and **no blank lines** inside `align*`.

---

## Strict Formatting Rules

* **Inline math:** Always wrap inline maths in `$ … $`.
* **Macros:** Use curly braces – e.g. `\vec{a}`, `\frac{a}{b}`.
* **Fractions:** Use `\frac{…}{…}` (never `\tfrac`).
* **Delimiters:** Use `\left( … \right)` etc.; avoid size macros like `\bigl`.
* **No blank lines** inside any `align*` environment.

---

## Mini Example

```latex
\item[]
\begin{center}
    \textsc{Comprehension-X}
\end{center}

A block of mass $m$ is projected up a rough incline… (passage continues).

\item The work done by friction until the block stops is
    \begin{tasks}(4)
        \task $mg\mu L$
        \task $-mg\mu L$ \ans
        \task $2mg\mu L$
        \task $0$
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Friction opposes motion; work = $-\mu mg \cos\theta \times L$.  Here $\cos\theta = 1$ (horizontal example).}
        W_{\text{fr}} &= -\mu mg L
    \end{align*}
\end{solution}

\item The time taken for the block to return to the base is
    \begin{tasks}(4)
        \task $\sqrt{\dfrac{2L}{g\sin\theta}}$ \ans
        \task $\sqrt{\dfrac{L}{g\sin\theta}}$
        \task $\dfrac{2L}{g\sin\theta}$
        \task $\dfrac{L}{g\sin\theta}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Using $s = ut + \tfrac12 a t^{2}$ with $u=0$ and $a=g\sin\theta$:}
        L &= \tfrac12 g\sin\theta\, t^{2} \\
        t &= \sqrt{\frac{2L}{g\sin\theta}}
    \end{align*}
\end{solution}
```

---

**Final Check:** Return only the LaTeX snippet from the first line shown above through the last `\end{solution}` with nothing extra.
"""


prompt_mcq_single_correct_problem_with_solution_gpt_5 = r"""
## Overall Task & Output Format

**Goal:** Analyze the provided image. Generate a complete LaTeX multiple-choice physics question based **exactly** on the image, assuming it has a **single correct answer**. Include a step-by-step solution (which identifies the correct option) and, if applicable, a simplified `tzplot` diagram.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required LaTeX Structure

Follow this exact structure for your output:

1.  **Problem Statement (`\item ...`)**
    *   Begin the output *immediately* with `\item`.
    *   Extract the **exact** physics question text from the image **without any modifications or additions**.
    *   Use inline math mode `$ ... $` for all mathematical symbols and variables as they appear in the image.

2.  **Code to draw a Diagram (Optional, place immediately after `\item` line if used)**
    *   Try to use tzplot package to draw a diagram not necessarily, you can use other packages like tikz, pgfplots, etc.
    *   Use `tzplot` commands (see reference below).
    *   Use this code as reference for diagrams in different scenarios:
        
        - \tzaxes(0, 0)(5, 4){$x$}{$y$}
        - \tzticks*{1, 2, 3, 4, 5}{1, 2, 3, 4}
        - \tzticks{3/$3$}{2/$2$}
        - \tzproj[dashed](4, 5)
        - \tzprojx[dashed](4, 5)
        - \tzprojy[dashed](4, 5)
        - \tzcoor(4, 5)(A){$A$}[45]
        - \tzcoor*(4, 5)(B){$B$}[45]
        - \tzanglemark(2, 0)(0, 0)(2, 3){$\theta$}
        - \tzrightanglemark(C)(O)(B){$90^\circ$}
        - \tzfn{\x^2}[0:4]
        - \pic (surface) at (0, 0) {frame=7cm};
        - \pic[rotate=180] (ceiling) at (0, 0){frame=3cm};
        - \tzto[bend right](0, 0)(5, 4)
        - \tzto[bend left](0, 0)(5, 4)
        - \tztos"curve"(1, 1)[out=70, in=180](2.5, 3)[in=110, out=0](4, 1);
        - \tzvXpointat*{curve}{1.25}(A){$1$}[left]
        - \tzfn"AA"{0.35*(\x)^2}[0:3]{$y=x^2$}[ar]
        - \tzfnarea*[pattern=north east lines, opacity=1]{0.35*(\x)^2}[1:2]
        - \tzfnarealine{AA}{1}{2}
        - \tzfnarealine[->]{AA}{2}{3}
            
    For diagram try to use the above code as reference.
    
    *   Wrap *only* the `tikzpicture` environment within a `center` environment:
        ```latex
        \begin{center}
            \begin{tikzpicture}
                % Your simplified tzplot commands here (e.g., \pic)
            \end{tikzpicture}
        \end{center}
        ```

3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
    *   Use a 2-column `tasks` environment.
    *   Extract the **exact** option text from the image **without any modifications**.
    *   Provide the options using `\task`.
    *   Based on your analysis in the solution step, mark the **single** correct answer by appending ` \ans` to the end of its corresponding `\task` line.

4.  **Solution (`\begin{solution} ... \end{solution}`)**
    *   Use an `align*` environment directly inside the `solution` environment.
    *   Show key conceptual steps and reasoning for solving the problem based on the extracted text.
    *   Use `\intertext{}` for brief text explanations *between* equation lines. Ensure any math within `\intertext{}` uses `$ ... $`.
    *   **Critically:** Evaluate the options to identify the **single** correct answer. Explain why it is correct and briefly why others might be incorrect if helpful for clarity. State the final correct option by letter (e.g., "Therefore, the correct option is (c)."). This analysis justifies the `\ans` marking in the `tasks` environment.
    *   Keep the solution concise and elegant. Show conceptual steps, but omit trivial intermediate algebra where appropriate.
    *   Align equations using `&`. Use `\\` to end lines.
    *   Keep only one step in every line of calculation.
    *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

Adhere to these rules meticulously:

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`. **Do not use** `\bigl`, `\bigr`, `\Bigl`, `\Bigr`, etc.

---

## TZPlot Command Reference (Use for Simplified Diagrams)

*(Only use the following if a simple surface/frame diagram is needed)*

*   **Ground/Wall:** `\pic (surface) at (0, 0) {frame=7cm};`

---

## Example Reference Output (Single Correct Answer)

*(This demonstrates the required structure for a single-correct answer question)*

\item A ball of mass $m$ moving with velocity $v_0$ collides a wall as shown in figure. After impact it rebounds with a velocity $\frac{3}{4} v_0$. The impulse acting on ball during impact is
    \begin{center}
        \begin{tikzpicture}
            \pic (surface) [rotate=90] at (0, 0) {frame=4cm}; % Example using the simplified diagram command
        \end{tikzpicture}
    \end{center}
    \begin{tasks}(2)
        \task $-\frac{m}{2}v_0 \ \hat{\jmath}$
        \task $-\frac{3}{4}mv_0 \ \hat{\imath}$
        \task $-\frac{5}{4}mv_0 \ \hat{\imath}$ \ans
        \task None of the above
    \end{tasks}
\begin{solution}
    \begin{align*}
        \intertext{Let the initial velocity be $\vec{v}_i$ and final velocity be $\vec{v}_f$. Impulse $\vec{J} = \Delta\vec{p} = m(\vec{v}_f - \vec{v}_i)$. Assume standard angles $37^\circ$ and $53^\circ$ as implied by similar problems.}
        \vec{v}_i &= v_0 \cos(37^\circ)\hat{i} - v_0 \sin(37^\circ)\hat{j} \\
        \vec{v}_f &= -\frac{3}{4}v_0 \cos(53^\circ)\hat{i} - \frac{3}{4}v_0 \sin(53^\circ)\hat{j} \\
        \intertext{Using standard approximations $\cos(37^\circ) \approx \sin(53^\circ) \approx 0.8$ and $\sin(37^\circ) \approx \cos(53^\circ) \approx 0.6$:}
        \vec{v}_i &\approx 0.8 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{v}_f &\approx -\frac{3}{4}v_0 (0.6)\hat{i} - \frac{3}{4}v_0 (0.8)\hat{j} \\
        &= -0.45 v_0 \hat{i} - 0.6 v_0 \hat{j} \\
        \vec{J} &= m(\vec{v}_f - \vec{v}_i) \\
        &= m [ (-0.45 v_0 \hat{i} - 0.6 v_0 \hat{j}) - (0.8 v_0 \hat{i} - 0.6 v_0 \hat{j}) ] \\
        &= m [ (-0.45 - 0.8) v_0 \hat{i} + (-0.6 - (-0.6)) v_0 \hat{j} ] \\
        &= m (-1.25 v_0 \hat{i} + 0 \hat{j}) \\
        &= -1.25 m v_0 \hat{i} = -\frac{5}{4} m v_0 \hat{i} \\
        \intertext{Comparing this result with the options:}
        \intertext{(a) $-\frac{m}{2}v_0 \hat{j}$ is incorrect as the impulse is purely along $\hat{i}$.}
        \intertext{(b) $-\frac{3}{4}mv_0 \hat{i}$ is incorrect.}
        \intertext{(c) $-\frac{5}{4}mv_0 \hat{i}$ matches our calculation.}
        \intertext{(d) Since (c) is correct, 'None of the above' is incorrect.}
        \intertext{Therefore, the correct option is (c).}
    \end{align*}
\end{solution}

---

**Final Check:** Ensure your output is ONLY the LaTeX snippet from `\item` to `\end{solution}` with no extra text or comments.
"""

prompt_mcq_variant_with_gpt_5 = r"""
You are an expert physicist and mathematician.

Your task: Create a new MCQ (Multiple Choice Question) that is a variant of the given problem.
- Keep the **same main concept** as the original problem.
- Change all **numerical data, variables, and context** so that it is a fresh problem.
- Provide **four answer options** (A, B, C, D) with only one correct answer.
- Ensure the **solution** is fully worked out and matches the new data.
- Double-check all calculations and consistency between question, options, and solution.

Output format:
1. Problem statement
2. Options (A, B, C, D)
3. Correct answer
4. Step-by-step solution
"""

prompt_mcq_variant_with_gpt_5 = r"""
## Overall Task & Output Format

**Goal:** You are an expert physicist and skilled LaTeX typesetter. Your task is to take a given LaTeX-formatted physics problem and generate a **new, unique variant** of it. This involves modifying the problem's context, numerical values, and recalculating the solution and options accordingly.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet for the new problem, starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required Steps & LaTeX Structure

1.  **Analyze the Input Problem:**
    *   Thoroughly understand the physics principles, variables, and solution method of the provided problem.

2.  **Create a Variant:**
    *   **Modify the context:** Change the scenario slightly (e.g., if the original is about a car, change it to a train or a block on a surface).
    *   **Change numerical values:** Alter the given values (e.g., mass, velocity, distance) to be realistic but different.
    *   **Recalculate everything:** Based on the new values, re-solve the problem from first principles to get a new correct answer.
    *   **Generate new distractors:** Create three new incorrect options that are plausible but based on common mistakes (e.g., sign errors, unit conversion errors, wrong formula).
    *   **Prefer integer‑friendly values:** Choose parameters so that key intermediate results and the final answer come out as integers (or simple rationals) to keep arithmetic simple and let students focus on the core idea.

3.  **Format the Output:**
    *   Follow this exact LaTeX structure for your output:

    1.  **Problem Statement (`\item ...`)**
        *   Begin the output *immediately* with `\item`.
        *   Write the new, modified physics question.
        *   Use inline math mode `$ ... $` for all mathematical symbols and variables.

    2.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
        *   Use a 2-column `tasks` environment.
        *   Provide your four new options (one correct, three distractors) using `\task`.
        *   Mark the **single** correct answer by appending ` \ans` to the end of its `\task` line.

    3.  **Solution (`\begin{solution} ... \end{solution}`)**
        *   Use an `align*` environment directly inside the `solution` environment.
        *   Show the key conceptual steps and calculations for your new, modified problem.
        *   Use `\intertext{}` for brief text explanations *between* equation lines.
        *   Align equations using `&`. Use `\\` to end lines.
        *   Keep only one step in every line of calculation.
        *   Conclude with a statement indicating the correct option (e.g., `\intertext{Therefore, the correct option is (a).}`).
        *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`, `\text{m}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`.
*   **Units:** Use `\ \text{m}`, `\ \text{s}`, `\ \text{ms}^{-1}`, `\ \text{ms}^{-2}` for units to ensure proper spacing and formatting.

---

## Example of Task

**Input Problem:**
```latex
\item At a distance of $500\ \text{m}$ from the traffic light, brakes are applied to an automobile moving at a velocity of $20\ \text{ms}^{-1}$. The position of automobile wrt traffic light $50\ \text{s}$ after applying the brakes, if its acceleration is $-0.5\ \text{ms}^{-2}$, is
    \begin{tasks}(2)
        \task $125\ \text{m}$ \ans
        \task $375\ \text{m}$
        \task $400\ \text{m}$
        \task $100\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 20\ \text{ms}^{-1},\ a=-0.5\ \text{ms}^{-2},\ t=50\ \text{s},\ s_0=500\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 20(50)+\frac{1}{2}(-0.5)(50)^{2}\\
          &= 1000-625\\
          &= 375\ \text{m}\\
        \intertext{Distance from the traffic light after $50\ \text{s}$:}
        x &= s_0-s = 500-375 = 125\ \text{m}\\
        \intertext{Therefore, the correct option is (a).}
    \end{align*}
\end{solution}
```

**Expected Output (A well-formed variant):**
```latex
\item A train, $800\ \text{m}$ away from a station, starts to slow down from an initial velocity of $30\ \text{ms}^{-1}$. If the deceleration is a constant $-0.6\ \text{ms}^{-2}$, what is the train's distance from the station after $40\ \text{s}$?
    \begin{tasks}(2)
        \task $80\ \text{m}$
        \task $720\ \text{m}$
        \task $280\ \text{m}$ \ans
        \task $520\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 30\ \text{ms}^{-1},\ a=-0.6\ \text{ms}^{-2},\ t=40\ \text{s},\ s_0=800\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 30(40)+\frac{1}{2}(-0.6)(40)^{2}\\
          &= 1200-480\\
          &= 720\ \text{m}\\
        \intertext{Distance from the station after $40\ \text{s}$:}
        x &= s_0-s = 800-720 = 80\ \text{m}\\
        \intertext{Therefore, the correct option is (a).}
    \end{align*}
\end{solution}
```
"""

prompt_mcq_context_variant_with_gpt_5 = r"""
## Overall Task & Output Format

**Goal:** You are an expert physicist and skilled LaTeX typesetter. Your task is to take a given LaTeX-formatted physics problem and generate a **new, unique variant** by modifying **only its context**. The underlying physics, numerical values, and solution must remain identical.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet for the new problem, starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required Steps & LaTeX Structure

1.  **Analyze the Input Problem:**
    *   Thoroughly understand the physics principles, variables, and solution method of the provided problem.

2.  **Create a Contextual Variant:**
    *   **Modify the context ONLY:** Change the scenario or story of the problem (e.g., if the original is about a car, change it to a train, a satellite, or a block on a surface).
    *   **Keep numerical values IDENTICAL:** Do NOT change any of the initial numerical values, constants, or the final calculated answer. The solution steps and options must remain mathematically equivalent to the original.
    *   **Adapt LaTeX:** Update the text in the problem statement, diagram labels (if any), and solution explanations to match the new context, but ensure the underlying equations, numbers, and results are unchanged.
    *   **Integer‑friendly extras only:** If you introduce any auxiliary labels or diagram annotations that include numbers, prefer integer or simple rational values. Do not alter given numbers.

3.  **Format the Output:**
    *   Follow this exact LaTeX structure for your output:

    1.  **Problem Statement (`\item ...`)**
        *   Begin the output *immediately* with `\item`.
        *   Write the new, context-modified physics question.
        *   Use inline math mode `$ ... $` for all mathematical symbols and variables.

    2.  **Diagram (`\begin{center}\begin{tikzpicture}...\end{tikzpicture}\end{center}`)**
        *   If the input problem includes a `\begin{tikzpicture}...\end{tikzpicture}` block, you **MUST** include a `tikzpicture` in your output, wrapped in a `\begin{center}` environment.
        *   The diagram should be placed between the problem statement (`\item...`) and the multiple-choice options (`\begin{tasks}...`).
        *   **Adapt the diagram to the new context:** Modify labels or text within the `tikzpicture` to reflect the new context. The geometry and numerical labels should remain unchanged.

    3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
        *   Use a 1-column or 2-column `tasks` environment as in the original problem.
        *   The options MUST be identical to the original problem.
        *   Mark the **single** correct answer by appending ` \ans` to the end of its `\task` line, which should be the same as the original.

    4.  **Solution (`\begin{solution} ... \end{solution}`)**
        *   Use an `align*` environment directly inside the `solution` environment.
        *   The calculations must be identical to the original.
        *   Update `\intertext{}` explanations to match the new context.
        *   Conclude with a statement indicating the correct option.
        *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`, `\text{m}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`.
*   **Units:** Use `\ \text{m}`, `\ \text{s}`, `\ \text{ms}^{-1}`, `\ \text{ms}^{-2}` for units to ensure proper spacing and formatting.

---

## Example of Task

**Input Problem:**
```latex
\item At a distance of $500\ \text{m}$ from the traffic light, brakes are applied to an automobile moving at a velocity of $20\ \text{ms}^{-1}$. The position of automobile wrt traffic light $50\ \text{s}$ after applying the brakes, if its acceleration is $-0.5\ \text{ms}^{-2}$, is
    \begin{tasks}(2)
        \task $125\ \text{m}$ \ans
        \task $375\ \text{m}$
        \task $400\ \text{m}$
        \task $100\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 20\ \text{ms}^{-1},\ a=-0.5\ \text{ms}^{-2},\ t=50\ \text{s},\ s_0=500\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 20(50)+\frac{1}{2}(-0.5)(50)^{2}\\
          &= 1000-625\\
          &= 375\ \text{m}\\
        \intertext{Distance from the traffic light after $50\ \text{s}$:}
        x &= s_0-s = 500-375 = 125\ \text{m}\\
        \intertext{Therefore, the correct option is (a).}
    \end{align*}
\end{solution}
```

**Expected Output (A well-formed context variant):**
```latex
\item A satellite is located $500\ \text{m}$ from a docking station and is moving towards it at $20\ \text{ms}^{-1}$. Thrusters are fired, causing a constant deceleration of $-0.5\ \text{ms}^{-2}$. What is the satellite's distance from the station after $50\ \text{s}$?
    \begin{tasks}(2)
        \task $125\ \text{m}$ \ans
        \task $375\ \text{m}$
        \task $400\ \text{m}$
        \task $100\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 20\ \text{ms}^{-1},\ a=-0.5\ \text{ms}^{-2},\ t=50\ \text{s},\ s_0=500\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 20(50)+\frac{1}{2}(-0.5)(50)^{2}\\
          &= 1000-625\\
          &= 375\ \text{m}\\
        \intertext{Distance from the docking station after $50\ \text{s}$:}
        x &= s_0-s = 500-375 = 125\ \text{m}\\
        \intertext{Therefore, the correct option is (a).}
    \end{align*}
\end{solution}
```
"""

prompt_mcq_numerical_variant_with_gpt_5 = r"""
## Overall Task & Output Format

**Goal:** You are an expert physicist and skilled LaTeX typesetter. Your task is to take a given LaTeX-formatted physics problem and generate a **new, unique variant** by modifying **only its numerical values**. The context and physical principles must remain the same.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet for the new problem, starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required Steps & LaTeX Structure

1.  **Analyze the Input Problem:**
    *   Thoroughly understand the physics principles, variables, and solution method of the provided problem.

2.  **Create a Numerical Variant:**
    *   **Modify numerical values ONLY:** Alter the given values (e.g., mass, velocity, distance) to be realistic but different. The underlying physical context and scenario must remain the same.
    *   **Do NOT change the context:** If the problem is about a car on a road, it must remain about a car on a road.
    *   **Recalculate everything:** Based on the new values, re-solve the problem from first principles to get a new correct answer.
    *   **Generate new distractors:** Create three new incorrect options that are plausible but based on common mistakes (e.g., sign errors, unit conversion errors, wrong formula).
    *   **Prefer integer‑friendly values:** Choose parameters so that key intermediate results and the final answer come out as integers (or simple rationals) to keep arithmetic simple and let students focus on the core idea.

3.  **Format the Output:**
    *   Follow this exact LaTeX structure for your output:

    1.  **Problem Statement (`\item ...`)**
        *   Begin the output *immediately* with `\item`.
        *   Write the physics question with the new numerical values.
        *   Use inline math mode `$ ... $` for all mathematical symbols and variables.

    2.  **Diagram (`\begin{center}\begin{tikzpicture}...\end{tikzpicture}\end{center}`)**
        *   If the input problem includes a `\begin{tikzpicture}...\end{tikzpicture}` block, you **MUST** include a `tikzpicture` in your output, wrapped in a `\begin{center}` environment.
        *   The diagram should be placed between the problem statement (`\item...`) and the multiple-choice options (`\begin{tasks}...`).
        *   **Adapt the diagram to the new problem:** Modify coordinates, labels, or elements within the `tikzpicture` to reflect the new numerical values and context of your variant. For example, if you change a force from 10N to 20N, update the corresponding label in the diagram. If the setup changes, modify the drawing commands accordingly. Do not just copy the old diagram if changes are needed.

    3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
        *   Use a 1-column or 2-column `tasks` environment as in the original problem.
        *   Provide your four new options (one correct, three distractors) using `\task`.
        *   Mark the **single** correct answer by appending ` \ans` to the end of its `\task` line.

    4.  **Solution (`\begin{solution} ... \end{solution}`)**
        *   Use an `align*` environment directly inside the `solution` environment.
        *   Show the key conceptual steps and calculations for your new, modified problem.
        *   Use `\intertext{}` for brief text explanations *between* equation lines.
        *   Align equations using `&`. Use `\\` to end lines.
        *   Keep only one step in every line of calculation.
        *   Conclude with a statement indicating the correct option (e.g., `\intertext{Therefore, the correct option is (a).}`).
        *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`, `\text{m}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`.
*   **Units:** Use `\ \text{m}`, `\ \text{s}`, `\ \text{ms}^{-1}`, `\ \text{ms}^{-2}` for units to ensure proper spacing and formatting.

---

## Example of Task

**Input Problem:**
```latex
\item At a distance of $500\ \text{m}$ from the traffic light, brakes are applied to an automobile moving at a velocity of $20\ \text{ms}^{-1}$. The position of automobile wrt traffic light $50\ \text{s}$ after applying the brakes, if its acceleration is $-0.5\ \text{ms}^{-2}$, is
    \begin{tasks}(2)
        \task $125\ \text{m}$ \ans
        \task $375\ \text{m}$
        \task $400\ \text{m}$
        \task $100\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 20\ \text{ms}^{-1},\ a=-0.5\ \text{ms}^{-2},\ t=50\ \text{s},\ s_0=500\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 20(50)+\frac{1}{2}(-0.5)(50)^{2}\\
          &= 1000-625\\
          &= 375\ \text{m}\\
        \intertext{Distance from the traffic light after $50\ \text{s}$:}
        x &= s_0-s = 500-375 = 125\ \text{m}\\
        \intertext{Therefore, the correct option is (a).}
    \end{align*}
\end{solution}
```

**Expected Output (A well-formed numerical variant):**
```latex
\item At a distance of $600\ \text{m}$ from the traffic light, brakes are applied to an automobile moving at a velocity of $25\ \text{ms}^{-1}$. The position of automobile wrt traffic light $40\ \text{s}$ after applying the brakes, if its acceleration is $-0.5\ \text{ms}^{-2}$, is
    \begin{tasks}(2)
        \task $600\ \text{m}$
        \task $200\ \text{m}$
        \task $400\ \text{m}$ \ans
        \task $0\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 25\ \text{ms}^{-1},\ a=-0.5\ \text{ms}^{-2},\ t=40\ \text{s},\ s_0=600\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 25(40)+\frac{1}{2}(-0.5)(40)^{2}\\
          &= 1000-400\\
          &= 600\ \text{m}\\
        \intertext{Distance from the traffic light after $40\ \text{s}$:}
        x &= s_0-s = 600-600 = 0\ \text{m}\\
        \intertext{Therefore, the correct option is (d).}
    \end{align*}
\end{solution}
```
"""

prompt_mcq_conceptual_variant_with_gpt_5 = r"""
## Overall Task & Output Format

**Goal:** You are an expert physicist and skilled LaTeX typesetter. Your task is to take a given LaTeX-formatted physics problem and generate a **new, unique variant** by making a **conceptual modification**. This means changing the core principles being tested, not just the surface details.

**CRITICAL OUTPUT CONSTRAINT:** You MUST return *only* the raw LaTeX code snippet for the new problem, starting precisely with `\item` and ending precisely after `\end{solution}`. Do **NOT** include *any* preamble, `\documentclass`, `\begin{document}`, explanations, comments, or any text outside of this exact snippet.

---

## Required Steps & LaTeX Structure

1.  **Analyze the Input Problem:**
    *   Thoroughly understand the physics principles, variables, and solution method of the provided problem.

2.  **Create a Conceptual Variant:**
    *   **Perform a conceptual modification:** Instead of just changing the story or numbers, alter a core concept or the setup of the problem. For example:
        *   If the original problem uses constant acceleration, make it a problem with acceleration as a function of time (e.g., $a(t) = kt$).
        *   If the original is about linear motion, change it to rotational motion.
        *   If the original is about projectile motion on a flat surface, change it to an inclined plane.
        *   If the original asks for a final position, ask for the time taken to stop or the work done by the brakes instead.
    *   **Change numerical values:** You will likely need to introduce new values or change existing ones to fit the new concept.
    *   **Recalculate everything:** Solve the new, conceptually different problem from first principles.
    *   **Generate new distractors:** Create plausible incorrect options for your new problem.
    *   **Prefer integer‑friendly values:** Choose parameters so that key intermediate results and the final answer come out as integers (or simple rationals) to keep arithmetic simple and let students focus on the core idea.

3.  **Format the Output:**
    *   Follow this exact LaTeX structure for your output:

    1.  **Problem Statement (`\item ...`)**
        *   Begin the output *immediately* with `\item`.
        *   Write the new, conceptually modified physics question.
        *   Use inline math mode `$ ... $` for all mathematical symbols and variables.

    2.  **Diagram (`\begin{center}\begin{tikzpicture}...\end{tikzpicture}\end{center}`)**
        *   If relevant, include an adapted `tikzpicture` that correctly represents the new problem's setup.

    3.  **Multiple Choice Options (`\begin{tasks}(2) ... \end{tasks}`)**
        *   Provide your four new options (one correct, three distractors) using `\task`.
        *   Mark the **single** correct answer by appending ` \ans` to the end of its `\task` line.

    4.  **Solution (`\begin{solution} ... \end{solution}`)**
        *   Use an `align*` environment to show the derivation for the new problem. This will likely involve different formulas (e.g., integration if acceleration is not constant).
        *   Conclude with a statement indicating the correct option.
        *   **Strictly forbidden:** Do **not** leave any blank lines inside the `align*` environment.

---

## Strict LaTeX Formatting Rules

*   **Math Mode:** Use `$ ... $` for *all* inline math.
*   **Macros:** Always use `{}`: `\vec{a}`, `\frac{a}{b}`, `\text{m}`.
*   **Vectors:** Use `\vec{a}` for generic vectors and `\hat{i}`, `\hat{j}`, `\hat{k}` for unit vectors.
*   **Fractions:** Use `\frac{a}{b}`. **Do not use** `\tfrac`.
*   **Parentheses/Brackets:** Use `\left( ... \right)`, `\left[ ... \right]`, `\left| ... \right|`.
*   **Units:** Use `\ \text{m}`, `\ \text{s}`, `\ \text{ms}^{-1}`, `\ \text{ms}^{-2}` for units to ensure proper spacing and formatting.

---

## Example of Task

**Input Problem:**
```latex
\item At a distance of $500\ \text{m}$ from the traffic light, brakes are applied to an automobile moving at a velocity of $20\ \text{ms}^{-1}$. The position of automobile wrt traffic light $50\ \text{s}$ after applying the brakes, if its acceleration is $-0.5\ \text{ms}^{-2}$, is
    \begin{tasks}(2)
        \task $125\ \text{m}$ \ans
        \task $375\ \text{m}$
        \task $400\ \text{m}$
        \task $100\ \text{m}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 20\ \text{ms}^{-1},\ a=-0.5\ \text{ms}^{-2},\ t=50\ \text{s},\ s_0=500\ \text{m}\\
        \intertext{Displacement in $t$ seconds:}
        s &= ut+\frac{1}{2}at^{2}\\
          &= 20(50)+\frac{1}{2}(-0.5)(50)^{2}\\
          &= 1000-625\\
          &= 375\ \text{m}\\
        \intertext{Distance from the traffic light after $50\ \text{s}$:}
        x &= s_0-s = 500-375 = 125\ \text{m}\\
        \intertext{Therefore, the correct option is (a).}
    \end{align*}
\end{solution}
```

**Expected Output (A well-formed conceptual variant):**
```latex
\item Brakes are applied to an automobile moving at $20\ \text{ms}^{-1}$. The acceleration of the automobile is given by $a(t) = -0.1t \ \text{ms}^{-2}$. How much time does it take for the automobile to come to a complete stop?
    \begin{tasks}(2)
        \task $10\ \text{s}$
        \task $40\ \text{s}$
        \task $20\ \text{s}$ \ans
        \task $15\ \text{s}$
    \end{tasks}
\begin{solution}
    \begin{align*}
        u &= 20\ \text{ms}^{-1} \\
        a(t) &= -0.1t \\
        \intertext{To find the velocity $v(t)$, we integrate the acceleration:} \\
        v(t) &= v(0) + \int_{0}^{t} a(t') \,dt' \\
              &= 20 + \int_{0}^{t} -0.1t' \,dt' \\
              &= 20 - 0.1 \left[ \frac{t'^2}{2} \right]_{0}^{t} \\
              &= 20 - 0.05t^2 \\
        \intertext{The automobile stops when $v(t) = 0$:} \\
        0 &= 20 - 0.05t^2 \\
        0.05t^2 &= 20 \\
        t^2 &= \frac{20}{0.05} = 400 \\
        t &= 20\ \text{s} \\
        \intertext{Therefore, the correct option is (c).}
    \end{align*}
\end{solution}
```
"""


prompt_sketch_to_problem_simple_gpt_5 = r"""
You are an expert physics problem setter and LaTeX typesetter.

Task: From the provided sketch/image (a rough, handwritten overview of an idea), write a clean, well-posed physics problem in LaTeX.

Output requirements (strict):
- Start the output immediately with `\item`.
- Insert a minimal diagram when relevant: place a `tikzpicture` inside a `center` environment immediately after the `\item` line and before any options. Prefer tzplot-style commands such as `\tzaxes`, `\tzticks*`, `\tzfn{...}[a:b]` where applicable.
- If it is a multiple-choice problem, include a `\begin{tasks}(2) ... \end{tasks}` block with 4 options, and mark the correct one by appending ` \ans` at the end of that `\task` line.
- Always include a concise solution using `\begin{solution}\begin{align*} ... \end{align*}\end{solution}` with clear, step-by-step reasoning. Use `\intertext{...}` for brief textual explanations between equation lines.
- Do not include any preamble, `\documentclass`, or extra commentary.
- Return only the LaTeX snippet from the first `\item` through the final `\end{solution}`.

Guidelines:
- Convert the rough idea into a precise problem statement. Choose either MCQ or short-answer depending on the content of the sketch.
- Use correct math formatting with `$...$` for inline math and `\frac{}`, `\vec{}`, etc., as needed.
- Keep numbers realistic. Define symbols if they are not obvious from the sketch.
- Keep the solution elegant and minimal, with one step per line inside `align*`. Do not leave blank lines inside `align*`.
"""


prompt_sketch_to_math_problem_gpt_5 = r"""
You are an expert mathematics problem setter and LaTeX typesetter.

Task: From the provided sketch/image (a rough handwritten overview of a math idea), write a clean, precise mathematics problem in LaTeX with a concise solution.

Output requirements (strict):
- Start the output immediately with `\item`.
- Insert a diagram/graph when relevant: place a `tikzpicture` inside a `center` environment immediately after `\item` and before any options. Prefer tzplot-style commands like `\tzaxes`, `\tzticks*`, `\tzfn{...}[a:b]` for simple graphs.
- Choose the most suitable format based on the sketch content: MCQ with `\begin{tasks}(2) ... \end{tasks}` (4 options, mark correct with ` \ans`) OR a short-answer problem with no options.
- Always include a solution using `\begin{solution}\begin{align*} ... \end{align*}\end{solution}` and use `\intertext{...}` for textual explanations between equations.
- Use proper LaTeX math: `$...$`, `\frac{}`, `\sqrt{}`, `\sum`, `\int`, etc.
- Return only the snippet from the first `\item` through the final `\end{solution}`.

Guidelines:
- Convert the rough idea into a precise, unambiguous problem statement (algebra, geometry, calculus, number theory, etc.).
- Define symbols clearly, keep numbers realistic, and keep the solution minimal with one step per line in `align*`.
"""


prompt_sketch_to_math_mcq_gpt_5 = r"""
You are an expert mathematics problem setter and LaTeX typesetter.

Task: From the provided sketch/image (a rough handwritten math idea), write a multiple-choice mathematics problem in LaTeX with exactly four options and a worked answer.

Output requirements (strict):
- Start with `\item`.
- Insert a diagram/graph when relevant: place a `tikzpicture` in a `center` environment right after the `\item` line. For curves/plots, use tzplot-style commands (`\tzaxes`, `\tzticks*`, `\tzfn{...}[a:b]`).
- Include a `\begin{tasks}(2) ... \end{tasks}` block with exactly four `\task` options; append ` \ans` to the correct option line.
- Provide a concise solution in `\begin{solution}\begin{align*} ... \end{align*}\end{solution}` and use `\intertext{...}` for short textual explanations between equation lines.
- Use correct math formatting with `$...$`, `\frac{}`, `\sqrt{}`, etc.
- No preamble or commentary; return only from `\item` to `\end{solution}`.

Guidelines:
- Ensure options are plausible; only one is correct. Keep computations tidy and logically sequenced.
"""


prompt_sketch_to_math_subjective_gpt_5 = r"""
You are an expert mathematics problem setter and LaTeX typesetter.

Task: From the provided sketch/image (a rough handwritten math idea), write a short-answer mathematics problem in LaTeX (no options) with a concise solution.

Output requirements (strict):
- Start with `\item`.
- Do not include a tasks/options block.
- Insert a diagram/graph when relevant: place a minimal `tikzpicture` in a `center` environment right after `\item`. Prefer tzplot-style commands (`\tzaxes`, `\tzticks*`, `\tzfn{...}[a:b]`) for simple graphs.
- Provide a concise solution in `\begin{solution}\begin{align*} ... \end{align*}\end{solution}`; use `\intertext{...}` for short textual explanations; end with a clearly stated final answer (use `\boxed{}` if numerical or closed-form).
- Use proper math formatting and keep one step per line in `align*`.
- Return only the snippet from `\item` to `\end{solution}`.
"""


prompt_sketch_to_paragraph_problem_gpt_5 = r"""
You are an expert physics and mathematics problem setter and LaTeX typesetter.

Task: From the provided sketch/image (a rough handwritten overview), create a comprehensive paragraph-type problem in LaTeX with multiple related sub-questions.

Output requirements (strict):
- Start with `\item` followed by a detailed problem statement (2-4 sentences describing a physical scenario or mathematical context).
- Insert a relevant diagram when appropriate: place a `tikzpicture` in a `center` environment after the main problem statement. Use tzplot-style commands (`\tzaxes`, `\tzticks*`, `\tzfn{...}[a:b]`) for graphs/plots.
- Include an `\begin{enumerate}` block with 2-4 related sub-questions that build upon each other logically.
- For each sub-question, provide a solution using `\begin{solution}\begin{align*} ... \end{align*}\end{solution}` with `\intertext{...}` for explanations between equations.
- Use proper LaTeX math formatting and keep one step per line in `align*`.
- Return only the snippet from `\item` through the final `\end{solution}`.

Guidelines:
- Create a coherent scenario that connects all sub-questions (e.g., projectile motion with multiple phases, circuit analysis with changing conditions, calculus optimization with constraints).
- Sub-questions should progress from basic concepts to more complex applications.
- Each solution should be concise but complete, showing key conceptual steps.
- Use realistic numerical values and clearly define all symbols.

Example structure:
```
\item [Problem statement describing scenario]
\begin{center}
    \begin{tikzpicture}
        [diagram if relevant]
    \end{tikzpicture}
\end{center}
\begin{enumerate}
    \item [Sub-question 1]
    \item [Sub-question 2]
    \item [Sub-question 3]
\end{enumerate}
\begin{solution}
    \begin{align*}
        [Solution for part (a)]
        \intertext{For part (b):}
        [Solution for part (b)]
        \intertext{For part (c):}
        [Solution for part (c)]
    \end{align*}
\end{solution}
```
"""

prompt_mcq_conceptual_plus__variant_with_gpt_5 = r"""
## Overall Task & Output Format

**Goal:** Create a deep, thoughtful MCQ variant that keeps the original problem’s core topic central while deliberately blending in 1–2 auxiliary concepts (from related topics). Wherever reasonable, shift the formulation toward a calculus-based treatment (e.g., time/space dependent quantities, integration/differentiation, rates of change, optimization). Change context and numerical values; the underlying idea may evolve, but the core topic must remain primary.

**CRITICAL OUTPUT CONSTRAINT:** Return only the raw LaTeX snippet, starting exactly with `\item` and ending exactly after `\end{solution}`. No preamble, no `\documentclass`, no `\begin{document}`, no extra commentary.

---

## Construction Requirements

1. **Identify the core topic and keep it central** (e.g., kinematics, work–energy, circular motion, oscillations, electrostatics, thermodynamics). State it implicitly through the problem you write; do not label it explicitly.
2. **Blend with 1–2 auxiliary concepts** that deepen the reasoning (e.g., small-angle approximation, energy dissipation, variable forces, geometry/constraints, continuity, simple circuit relations, fluid pressure, etc.).
3. **Prefer calculus where appropriate**:
   - Replace constants with functions such as $a(t)$, $F(x)$, $E(r)$, or a parameter varying smoothly in time/space.
   - Use single-variable integrals/derivatives that are solvable in closed form; avoid unsolved differential equations.
   - If relevant, include an extremum/optimization step or a rate-of-change interpretation.
4. **Change numerical values and context** to be realistic, dimensionally consistent, and different from the original.
5. **Produce a complete MCQ with one correct option** and three plausible distractors consistent with the new model and numbers.
6. **Prefer integer‑friendly values** so that key intermediate results and the final answer are integers (or simple rationals) to keep arithmetic simple while emphasizing the core idea.

---

## Required LaTeX Structure

1. **Problem (`\item ...`)**
   - Begin immediately with `\item`.
   - State the new conceptual-plus question, keeping the core topic central and weaving in the auxiliary concept(s).
   - Use inline math `$...$` for all symbols and quantities.

2. **Optional diagram** in `\begin{center}\begin{tikzpicture}...\end{tikzpicture}\end{center}` if it clarifies geometry/fields/forces.

3. **Options (`\begin{tasks}(2) ... \end{tasks}`)**
   - Provide four options via `\task`.
   - Append ` \ans` to the single correct option.

4. **Solution (`\begin{solution} ... \end{solution}`)**
   - Use an `align*` environment, one logical step per line.
   - Incorporate the calculus step(s) cleanly (e.g., an integral of $a(t)$ to get $v(t)$, work via $\int F(x)\,dx$, charge via $\int i(t)\,dt$, flux via an area integral if simple, etc.).
   - Use `\intertext{...}` sparingly to explain ideas between lines; keep math inside `$...$`.
   - End with a clear statement: “Therefore, the correct option is (x).”
   - No blank lines inside `align*`.

---

## Strict Formatting Rules

* Inline math only: `$...$` everywhere (no display math fences).
* Use macros with braces: `\vec{a}`, `\frac{a}{b}`, `\hat{i}`, `\text{m}`.
* Parentheses/Brackets: `\left(\cdot\right)`, `\left[\cdot\right]`, `\left|\cdot\right|`.
* Units with proper spacing: `\ \text{m}`, `\ \text{s}`, `\ \text{N}`, `\ \text{J}`.
* Exactly one correct option, marked with `\ans`.

---

## Quality Checklist (silently ensure)

* Core topic is unmistakably central; auxiliary concept(s) enrich but do not overshadow it.
* Calculus step is necessary, correct, and solvable cleanly.
* Numbers are realistic and dimensionally consistent; final numeric values match the marked option.
* Options are coherent with the model (no impossible magnitudes/signs).
* The output begins with `\item` and ends right after `\end{solution}`.
"""


def switch_prompt(value):
    if value == "match":
        return prompt_match
    elif value == "assertion_reason":
        return prompt_assertion_reason
    elif value == "solution_irodov":
        return prompt_solution_irodov
    elif value == "subjective_instagram":
        return prompt_subjective_instagram
    elif value == "maths_inequality":
        return prompt_maths_inequality
    elif value == "solution_with_o4_mini":
        return prompt_solution_with_o4_mini
    elif value == "mcq_problem_with_tikz_solution_o4_mini":
        return prompt_mcq_problem_with_tikz_solution_o4_mini
    elif value == "mcq_problem_with_solution_o4_mini":
        return prompt_mcq_problem_with_solution_o4_mini
    elif value == "mcq_problem_with_solution_o3":
        return prompt_mcq_problem_with_solution_o3
    elif value == "mcq_single_correct_problem_with_solution_o3":
        return prompt_mcq_single_correct_problem_with_solution_o3
    elif value == "mcq_single_correct_problem_only_solution_with_o3":
        return prompt_mcq_single_correct_problem_only_solution_with_o3
    elif value == "mcq_single_correct_problem_refine_solution_o3":
        return prompt_mcq_single_correct_problem_only_solution_with_o3
    elif value == "subjective_problem_with_solution_o3":
        return prompt_subjective_problem_with_solution_o3
    elif value == "mcq_maths_single_correct_problem_with_solution_o3":
        return prompt_mcq_maths_single_correct_problem_with_solution_o3
    elif value == "match_problem_with_solution_o3":
        return prompt_match_problem_with_solution_o3
    elif value == "comprehension_problem_with_solution_o3":
        return prompt_comprehension_problem_with_solution_o3
    elif value == "mcq_single_correct_problem_with_solution_gpt_5":
        return prompt_mcq_single_correct_problem_with_solution_gpt_5
    elif value == "mcq_variant_with_gpt_5":
        return prompt_mcq_variant_with_gpt_5
    elif value == "mcq_context_variant_with_gpt_5":
        return prompt_mcq_context_variant_with_gpt_5
    elif value == "mcq_numerical_variant_with_gpt_5":
        return prompt_mcq_numerical_variant_with_gpt_5
    elif value == "mcq_conceptual_variant_with_gpt_5":
        return prompt_mcq_conceptual_variant_with_gpt_5
    elif value == "sketch_to_problem_simple_gpt_5":
        return prompt_sketch_to_problem_simple_gpt_5
    elif value == "sketch_to_math_problem_gpt_5":
        return prompt_sketch_to_math_problem_gpt_5
    elif value == "sketch_to_math_mcq_gpt_5":
        return prompt_sketch_to_math_mcq_gpt_5
    elif value == "sketch_to_math_subjective_gpt_5":
        return prompt_sketch_to_math_subjective_gpt_5
    elif value == "sketch_to_paragraph_problem_gpt_5":
        return prompt_sketch_to_paragraph_problem_gpt_5
    elif value == "mcq_conceptual_plus__variant_with_gpt_5":
        return prompt_mcq_conceptual_plus__variant_with_gpt_5
    else:
        return value
