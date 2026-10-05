# Comparing a Plain Chatbot, a Rule-Based Workflow, and an AI Agent

## 1. Scenario

The scenario chosen for this project is College Student Attendance and Fine Management.

The private student data used in this scenario includes attendance percentages for Python, DBMS, DSA, and German. The minimum required attendance is 75%. The system also contains predefined late-fine information for one, two, and three late days.

The private data used by the system is:

- Python: 85%
- DBMS: 78%
- DSA: 92%
- German: 74%
- Minimum attendance requirement: 75%
- Fine for 1 late day: Rs. 50
- Fine for 2 late days: Rs. 100
- Fine for 3 late days: Rs. 150

The same attendance scenario was implemented using three different approaches: a plain chatbot, a rule-based workflow, and an AI agent.

---

## 2. Purpose of the Comparison

The purpose of this project is to understand how a plain chatbot, a rule-based workflow, and an AI agent handle the same private-data problem differently.

The comparison focuses on how each approach accesses data, makes decisions, uses tools, handles multiple steps, performs automation, and provides reliable results.

---

# 3.1 How Each Approach Works

## Plain Chatbot

The plain chatbot uses an LLM to respond to the user's questions. It does not have access to the private attendance data stored in the application.

When a user asks a question such as "What is my DSA attendance?", the chatbot receives the question and sends it to the LLM. Since it has no connection to the private student data, it cannot retrieve the actual attendance value.

For example, the chatbot can answer general questions or write an encouraging message about attendance, but it cannot reliably provide the student's actual DSA attendance.

The chatbot does not use any external tools or predefined attendance rules. Its main component is the LLM.

The main limitation is that it cannot access the private student information required for data-specific questions. Therefore, it may not be suitable when accurate private data retrieval is required.

---

## Rule-Based Workflow

The rule-based workflow does not use an LLM. Instead, it follows predefined rules written in Python using conditions such as `if` and `elif`.

The workflow has direct access to the private attendance and fine data stored in the application.

For example, when the user asks for DSA attendance, the workflow checks whether the question matches the predefined DSA attendance rule. If it matches, it retrieves the DSA attendance value from the stored data and returns 92%.

For the German attendance question, the workflow compares the stored German attendance of 74% with the minimum attendance requirement of 75%.

For the average attendance question, the workflow calculates the average using the stored attendance values.

For the late-fine question, the workflow uses the predefined fine rule for three late days and returns Rs. 150.

The workflow is predictable because it follows fixed rules. However, its limitation is flexibility. If the user asks a question that does not match one of the predefined rules, the workflow cannot handle it automatically.

---

## AI Agent

The AI agent combines an LLM, tools, and a loop.

The agent has access to tools that can retrieve private attendance information, retrieve late-fine information, and perform calculations.

When a user asks a question, the LLM first interprets the request and decides whether a tool is required. If a tool is needed, the agent calls the appropriate tool. The tool returns the result to the agent, and the agent continues processing until it can provide the final answer.

For example, when the user asks for DSA attendance, the agent can use the attendance tool to retrieve the private DSA value of 92%.

For the German question, it can retrieve the German attendance and compare it with the 75% requirement.

For the average attendance question, the agent retrieves the attendance values and then performs the required calculation to produce an average of 82.25%.

For the late-fine question, the agent uses the fine tool to retrieve the fine for three late days.

Therefore, the AI agent demonstrates the combination of LLM + Tools + Loop. It can interpret the request, select appropriate tools, observe the results, and continue processing until the task is completed.

The main limitation is that the final response and tool selection depend partly on the LLM. Different models or prompts may make different tool-selection decisions.

---

# 3.2 Comparison

| Criterion | Plain Chatbot | Rule-Based Workflow | AI Agent |
|---|---|---|---|
| Flexibility | High for general conversation | Low because rules are predefined | High because the LLM can interpret different requests |
| Decision-making | LLM generates a response but has no private-data tools | Fixed decisions based on predefined conditions | LLM decides which tools are needed and can perform multiple steps |
| Tool usage | No | No | Yes |
| Private-data access | No | Yes | Yes |
| Multi-step task handling | Limited | Limited to predefined steps | Yes, through the tool-use loop |
| Automation | Limited to generating responses | High for predefined cases | High for tasks that can be handled through tools |
| Reliability | Depends on the LLM and available information | Predictable for implemented rules | Depends on the LLM, tool selection, and tools |

The three approaches therefore differ mainly in how much control and flexibility they provide. The chatbot relies mainly on the LLM, the workflow relies on predefined rules, and the agent combines the LLM with tools and an execution loop.

---

# 3.3 Suitability for the Scenario

For the college attendance and fine management scenario, the three approaches have different characteristics.

The plain chatbot can be used for general communication, such as writing a message encouraging students to maintain good attendance. However, it does not have access to the student's private attendance data.

The rule-based workflow can directly access private attendance information and provide predictable results for questions that have been explicitly implemented as rules. This makes it useful for fixed and clearly defined attendance operations.

The AI agent can access the same private data through tools and can interpret the user's request before deciding which tools are required. It can also handle multi-step operations such as retrieving attendance information and performing calculations.

For this scenario, the AI agent was used to demonstrate flexible private-data interaction and multi-step tool usage. The rule-based workflow remains useful for cases where the questions and decisions are known in advance, while the plain chatbot is useful for general conversational tasks that do not require private data.

---

# 3.4 Conclusion

A plain chatbot is appropriate when the main requirement is natural-language conversation, general information, or simple content generation and private application data is not required.

A rule-based workflow is appropriate when the process is clearly defined and predictable. It is useful when decisions must follow fixed conditions and the possible cases are known in advance.

An AI agent is appropriate when a problem requires flexible reasoning, access to tools or private data, and multiple steps to complete a task. The agent can interpret a request, select tools, observe their results, and continue until the task is completed.

The comparison shows that these three approaches are not identical implementations of the same idea. A chatbot mainly provides LLM-based responses, a workflow follows predefined rules, and an agent combines an LLM with tools and a loop to perform more flexible tasks.