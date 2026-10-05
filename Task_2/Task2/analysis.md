# Day 2 Task: Comparing Direct Prompting, Chain-of-Thought, and ReAct

## 1. Scenario

The scenario chosen for this task is **College Student Attendance and Fine Management**.

In this scenario, a college assistant needs to answer questions about student attendance, calculate attendance-related values, and retrieve student information such as attendance percentage and fine amount.

The scenario contains both reasoning-based questions and questions that require external information. For example, calculating the average attendance of a student across multiple subjects requires mathematical reasoning, while finding the attendance and fine of a particular student requires accessing student data through tools.

The three approaches compared in this task are Direct Prompting, Chain-of-Thought (CoT) Prompting, and ReAct.

---

## 2. Direct Prompting

Direct prompting gives the question directly to the language model and asks it to provide an answer. In this approach, there is no visible reasoning process and no tool is used.

For this scenario, the question used was:

> A student has 82% attendance in DSA, 71% in German, and 91% in Python. What is the average attendance?

The model directly returned:

> 81.33%

The calculation is correct because the three attendance percentages are added and divided by the number of subjects.

Direct prompting is suitable for simple questions where the required information is already available to the model or included directly in the question. However, it cannot independently retrieve external student information because there is no tool access in this approach.

In this scenario, direct prompting can calculate an average attendance, but it cannot directly retrieve the attendance or fine amount of a student from the student database.

---

## 3. Chain-of-Thought Prompting

Chain-of-Thought prompting asks the model to solve a problem step by step before giving the final answer. This makes the intermediate calculation visible in the output.

For the attendance scenario, the same average-attendance question was used.

The model calculated:

1. 82% + 71% + 91% = 244%
2. There are 3 subjects.
3. 244% / 3 = 81.33%

Therefore, the final answer was approximately **81.33%**.

Chain-of-Thought is useful for problems that require multiple reasoning steps. It can make the calculation easier to follow compared with direct prompting.

However, Chain-of-Thought by itself does not provide access to external tools. If the model does not have a required fact, it cannot retrieve that fact just because it is asked to reason step by step.

For example, if the question asks for the current attendance and fine of student ST101, Chain-of-Thought alone cannot access the student data unless an external tool is provided.

---

## 4. ReAct Agent

ReAct stands for **Reasoning and Acting**. It combines reasoning with actions performed through tools. The basic cycle is Thought → Action → Observation, which can be repeated until enough information is available to provide the final answer.

For this scenario, the question used was:

> For student ST101, what is the attendance percentage and fine amount?

Two tools were used:

- `get_attendance()`
- `get_fine()`

The ReAct-style trace was:

1. Thought: The attendance information is required.
2. Action: `get_attendance('ST101')`
3. Observation: `68`
4. Thought: The fine information is also required.
5. Action: `get_fine('ST101')`
6. Observation: `150`
7. Final answer: Student ST101 has 68% attendance and a fine of Rs. 150.

The important advantage of ReAct is that it can use external information through tools before producing the final answer.

In this implementation, the ReAct trace is a scripted demonstration of the Thought, Action, and Observation cycle. The tool functions are explicitly called by the Python program, and their results are then passed to the model for the final response.

For this scenario, ReAct is useful when the answer depends on information that is outside the model's immediate knowledge and must be retrieved through a tool.

---

## 5. Comparison of the Three Approaches

| Basis | Direct Prompting | Chain-of-Thought | ReAct Agent |
|---|---|---|---|
| **Reasoning depth** | Low; gives the answer directly | Higher; performs step-by-step reasoning | Higher; combines reasoning with actions and observations |
| **Tool usage** | No tool usage | No tool usage in this implementation | Uses tools to retrieve external information |
| **Reliability on multi-step questions** | Suitable for simple calculations; can be less transparent for complex problems | Useful for multi-step reasoning and calculations | Useful when multi-step reasoning also requires external information |
| **Transparency** | Final answer is visible, but reasoning is not shown | Intermediate calculation is shown in this demonstration | Tool actions and observations are visible in the trace |
| **Speed / cost** | Generally fastest because it produces a direct response | Can require more output because of the reasoning steps | Can be slower because it may involve multiple tool calls and model interactions |
| **Consistency across repeated runs** | Usually consistent at temperature 0 | Can vary in wording or reasoning at non-zero temperature | Can depend on both model reasoning and tool results |

The comparison shows that the three approaches differ mainly in how much reasoning they expose and whether they can access external information. Direct prompting is simple and fast, Chain-of-Thought is more suitable for step-by-step reasoning, and ReAct is designed for situations where reasoning needs to be combined with external actions or tools.

---

## 6. Self-Consistency Observation

The average-attendance question was selected for the self-consistency experiment.

The question was run **five times at temperature 0.8**.

The results were:

- Run 1: 81.33%
- Run 2: 81.33%
- Run 3: 81.33%
- Run 4: 81.33%
- Run 5: 81.33%

Although the formatting and wording differed slightly between some runs, all five runs produced the same numerical answer.

Therefore, the majority answer was **81.33%, occurring in 5 out of 5 runs**.

The answer is correct because:

82 + 71 + 91 = 244

244 / 3 = 81.33%

A separate run was performed with **temperature 0**. It also produced 81.33%. This shows that, for this particular question, the model produced a deterministic and consistent answer at temperature 0.

The experiment also shows that non-zero temperature can change the wording or formatting of an answer even when the final numerical result remains the same.

---

## 7. Suitability Analysis

For the chosen college attendance and fine management scenario, the ReAct approach is useful when the task requires information from external student records because it can interact with tools and use their observations before producing the final answer.

Direct prompting is sufficient for simple questions such as calculating an average when all required values are already provided in the question. It is simple and fast, but it does not provide tool access.

Chain-of-Thought is useful when a question requires multiple reasoning steps. In the attendance example, it clearly showed how the average was calculated. However, it still depends on the information available to the model and does not independently retrieve student records.

The self-consistency experiment showed that the selected reasoning question produced the correct answer in all five temperature-0.8 runs, and the temperature-0 run also produced the same answer. Therefore, the selected calculation was stable across the tested runs.

Overall, the choice of approach depends on the type of task. For this scenario, a tool-based ReAct approach is appropriate for questions involving student records, while direct prompting or Chain-of-Thought can be used for questions where the required information is already provided.

---

## 8. Conclusion

Direct prompting, Chain-of-Thought, and ReAct provide different ways of solving problems.

Direct prompting is appropriate for simple questions where a direct answer is sufficient and no external information is required. It is straightforward and generally fast.

Chain-of-Thought is useful for problems that require several reasoning steps. It can make the calculation or reasoning process easier to follow, although it does not provide external tool access by itself.

ReAct combines reasoning with actions and observations. It is useful when a problem requires both reasoning and external information retrieved through tools. The agent can identify the information it needs, perform an action using a tool, observe the result, and then use that result to produce a final answer.

Therefore, the appropriate approach depends on the problem. Simple problems can be handled with direct prompting, multi-step reasoning problems can benefit from Chain-of-Thought, and problems requiring external information or tool interaction can use a ReAct-style approach.