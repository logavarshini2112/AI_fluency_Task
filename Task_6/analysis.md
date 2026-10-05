# Day 6 - Reliable Tool Calling

> **How to read this file:** Sections 1-13 and 18 (concept answers) are written from the design of the code.
> Items marked **⬜ REPLACE AFTER RUNNING** are placeholders. I must fill them with my real observed output.
> No results in this file have been invented.

## 1. Scenario

The project is a **Student Assistant**. A user asks a question in plain English and the model can use two tools:

| Tool | Purpose | Arguments |
|---|---|---|
| `get_marks` | Return a student's marks for one subject | `student_name` (string), `subject` (enum: Python, Java, AI) |
| `calculate_grade` | Convert marks into a letter grade | `marks` (number, 0-100) |

Grade rules: 90-100 = A, 80-89 = B, 70-79 = C, 60-69 = D, below 60 = F.
Sample data is a small hard-coded dictionary (e.g. Logavarshini: Python 85, Java 78, AI 92).

Files: `tools.py` (tools + schemas), `validator.py` (checks arguments), `agent.py` (manual agent loop), `fault_injection.py` (offline broken-call tests), `structured_outputs.py` (JSON mode vs schema mode demo).

Goal: show that the model's tool calls are only *requests*, and that our code must check them before running anything.

## 2. Chat Completions

**Main request fields**
- `model`: which model to use.
- `messages`: the conversation, a list of `{role, content}` where role is `system`, `user`, `assistant`, or `tool`.
- `tools`: the list of function schemas the model may call.
- `tool_choice`: whether/how the model should use tools.
- `max_tokens`: maximum length of the reply.
- Others: `temperature`, `stream`, `response_format`.

**Main response fields**
- `choices[0].message`: the model's reply, with `role`, `content`, and optionally `tool_calls`.
- `choices[0].finish_reason`: *why* the model stopped.
- `usage`: token counts. Also `id`, `model`, `created`.

**finish_reason and what the program does**

| finish_reason | Meaning | What our program does |
|---|---|---|
| `stop` | The model finished normally | Return `message.content` as the final answer |
| `tool_calls` | The model wants one or more tools run | Parse, validate and execute every tool call, send one `tool` message per call, then call the model again |
| `length` | The reply hit `max_tokens` and was cut off | Do NOT trust or run the partial reply. Retry with a larger `max_tokens` (doubling, up to a limit) |

(Other values such as `content_filter` are possible; the agent stops and reports them.)

**Why can `message.content` be empty when the model requests a tool?**
When the model decides to call a tool, its output *is* the tool call (name + arguments in `message.tool_calls`). It has no sentence to say yet. The real answer comes later, after it receives the tool result. So code must check `tool_calls`, not assume `content` has text.

## 3. OpenAI-Compatible APIs

**What "OpenAI-compatible" means:** a server offers the same HTTP endpoint (`/chat/completions`) and the same JSON request/response shapes as OpenAI's API. Because of that, the same OpenAI Python client can talk to it.

**Configuration changes needed** (only three values, all kept in `.env`):

| Setting | Meaning |
|---|---|
| `BASE_URL` | Where the server is |
| `API_KEY` | The provider's key (never hard-coded, never committed) |
| `MODEL` | The provider's name for the model |

Typical examples (always check the provider's current docs):
- **Ollama (local):** base URL `http://localhost:11434/v1`; the key is ignored but the client needs a non-empty value.
- **Groq:** base URL `https://api.groq.com/openai/v1`, with a Groq key.
- **vLLM:** run your own server (it exposes a `/v1` endpoint), e.g. `http://localhost:8000/v1`. Tool calling needs the server started with tool-calling options for your model.
- **Hugging Face:** the Inference Providers router exposes an OpenAI-style `/v1` endpoint, used with a Hugging Face token.

The Python code does not change when switching provider. Only `.env` changes.

**One thing compatibility does NOT guarantee:** identical *features and behaviour*. Providers and models differ in whether they support tool calling at all, parallel tool calls, `tool_choice="required"`, `strict` schemas, `response_format` schema mode, and how reliably the model produces valid arguments. This is exactly why we validate and why `structured_outputs.py` catches "unsupported" errors instead of assuming.

## 4. Streaming and Responses API

**Streaming** (`stream=True`) means the server sends the reply in small pieces (chunks) as they are generated instead of one finished response.
- *What it improves:* perceived speed. The user sees the first words quickly (good for chat UIs).
- *Why it is normally disabled in an agent loop:* tool-call names and arguments arrive in fragments that must be reassembled before they can be parsed; `finish_reason` only appears in the last chunk; and nobody reads the intermediate steps anyway. The loop needs the complete message to validate it, so non-streaming is simpler and safer.

**Responses API vs Chat Completions:** the Responses API is OpenAI's newer API. It uses `input`/`instructions`, returns typed output items, and can keep conversation state on the server and offer built-in tools. Chat Completions is the older, simpler design: a stateless list of `messages` in, one `choices[0].message` out.
**Why this project uses Chat Completions:** it is the format that Ollama, Groq, vLLM and others commonly implement, so the same code works across providers, and its message list makes every step of the tool loop visible to a beginner.

## 5. Five-Step Tool Calling Flow

1. **Send** the `messages` and the `tools` (our `SCHEMAS`) to the model.
2. **The model returns a tool call**: `finish_reason="tool_calls"` with a function name and a JSON *string* of arguments.
3. **Python parses** the call (JSON decode, find the tool).
4. **Python validates and executes** the function, only if validation passes.
5. **The result is sent back** as a `tool` message (with the matching `tool_call_id`) and the model **produces the final answer**.

> **THE MODEL DOES NOT EXECUTE THE PYTHON FUNCTION.**
> **OUR PYTHON CODE EXECUTES THE FUNCTION.**
> The model only writes text that *asks* for a call. If our code did nothing, nothing would run. That is why the model's request must be checked before we act on it.

## 6. Schemas

Each tool has a JSON Schema in `tools.py` (the `SCHEMAS` dictionary), sent to the model and reused by the validator.

| Schema field | What it does | Mistake it prevents / helps with |
|---|---|---|
| `description` | Plain-language explanation of the tool and of each argument | Helps the model pick the right tool and fill arguments correctly. It is guidance only; it enforces nothing |
| `properties` | Names and types of arguments (`string`, `number`) | Wrong types, e.g. `marks: "eighty-five"` |
| `enum` | Complete list of allowed values (`subject`: Python, Java, AI) | Invented values such as `Cricket` |
| `required` | Arguments that must be present | Missing arguments, e.g. no `subject` |
| `additionalProperties: false` | Forbids arguments not listed | Invented arguments, e.g. `age` |
| `strict` | An option (OpenAI-style) asking the server to force the model's arguments to match the schema exactly | Reduces malformed calls at generation time, but support varies by provider and it limits which schema keywords are allowed. So it is **off by default** here (`STRICT_TOOLS=false`) and we still validate ourselves |

Extra rules in our schemas: `minimum`/`maximum` (marks 0-100) and `minLength` (name not empty). Our own `validator.py` enforces all of these.

## 7. tool_choice

| Value | Meaning | Use |
|---|---|---|
| `"auto"` | The model decides whether to call a tool or answer directly | **Used in this project.** Needed so "Explain what a grade means." can be answered without a tool |
| `"none"` | The model must not call tools and must answer in text | When you want a text-only answer even though tools are defined |
| `"required"` | The model must call at least one tool | When an answer without a tool is never acceptable. Warning: if kept on after the tool result, the loop may never end |
| Named function, e.g. `{"type": "function", "function": {"name": "get_marks"}}` | Forces that specific tool | A fixed workflow where one tool must be used. Support differs between providers |

## 8. JSON Mode vs Schema Mode

| Mode | What you get | Limitation |
|---|---|---|
| **Normal output** | Free text. The shape can be anything | Cannot be reliably parsed by code |
| **JSON mode** (`response_format={"type": "json_object"}`) | The reply is intended to be syntactically valid JSON | It does NOT force your keys or types. Prompts usually must mention "JSON". Truncation can still break it |
| **Schema mode** (`response_format={"type": "json_schema", ...}`) | The reply is constrained to match *your* JSON Schema (required keys, types) | Not every provider/model supports it; some reject it or ignore it, so we catch errors and check the keys |

## 9. Parallel Tool Calls

**What they are:** one assistant message containing *several* entries in `tool_calls`, e.g. for "What is Logavarshini's Python mark and what grade does that mark correspond to?" a model might request `get_marks` and `calculate_grade` together. (Honestly, the second call depends on the first result, so many models call them one after another instead. Both are handled.)

**How our loop handles them:**
1. It appends the assistant message once, containing all tool calls.
2. It loops over *every* call; each one goes through the same 4 stages (parse, find, validate, execute).
3. It appends exactly one `tool` message per call, using that call's `tool_call_id`.
4. Then it calls the model again.

**Why every `tool_call_id` needs a tool message:** the API treats each call as a question that must be answered. A missing answer usually causes a 400 error, or confuses the model about what happened. Failed calls also get a tool message (containing the error string).

## 10. Failure Handling

| Failure | Where caught | What the loop returns to the model |
|---|---|---|
| Invalid JSON | Stage 1 (`parse_json_arguments`) | "Arguments are not valid JSON ..." |
| Arguments are valid JSON but not an object | Stage 1 | "Arguments must be a JSON object" |
| Unknown tool | Stage 2 | "Unknown tool ... Available tools: ..." |
| Missing argument | Stage 3 (validator) | "Missing required argument: subject" |
| Wrong type | Stage 3 | "Argument marks must be a number" |
| Enum violation | Stage 3 | "Argument subject must be one of: Python, Java, AI" |
| Invented argument | Stage 3 | "Unexpected argument: age" |
| Out-of-range / empty value | Stage 3 | "Argument marks must be between 0 and 100" |
| Tool itself fails or student not found | Stage 4 | "ERROR: ..." text (never an uncaught crash) |
| Truncated response | `finish_reason == "length"` | Not a tool message. The agent retries the call with larger `max_tokens` and never executes a cut-off call |
| Repeated identical calls | `register_call` | After more than 2 identical calls the agent stops with an explanation instead of looping forever |

Also: a maximum number of steps (`MAX_STEPS`) stops runaway loops.

## 11. Repair Pattern

- **Why failures are returned as strings:** an exception would crash the whole agent and the user would see nothing. A string becomes a normal `tool` message, so the loop keeps running.
- **Why malformed calls go back to the model:** the error message tells the model *exactly* what was wrong (e.g. the allowed subjects). The model can then fix the call (repair) or tell the user honestly that the request is impossible (e.g. Cricket). One bad call does not need to end the conversation.
- **Why `finish_reason="length"` triggers a retry with more tokens:** the reply was cut off, so tool-call JSON may be incomplete (and could even look valid but be missing fields). Running or repairing a half-written call is unsafe, so we ask again with a bigger `max_tokens` budget.
- **Limit on repairs:** repeated identical calls and the maximum step count prevent infinite repair loops.

## 12. Fault Injection

**What it is:** deliberately feeding the handler broken tool calls, written by hand, to see whether it survives them.

**Why it can run without a model or internet:** the handler (`handle_tool_call`) only receives two strings: a tool name and argument text. It does not care who produced them. So `fault_injection.py` can write those strings itself, with no LLM call and no key.

**What it proves:** the failure paths work *every time*, on demand. Real models rarely produce some of these faults, so waiting for them to happen naturally would prove nothing. It proves the handler returns an error string instead of crashing (and that a valid call still works, via the control test). It does not prove how well a real model will repair its call. That needs real runs.

## 13. Tool Calling vs Structured Outputs

| Basis | Tool Calling | Structured Outputs |
|---|---|---|
| What the model is asked to do | Decide *which* function to call and with *what* arguments, so that real work can be done | Reply in a fixed data shape (JSON that matches a schema) |
| Who performs the action / produces final data | Our Python code runs the function and produces the data; the model writes the final answer from the result | The model itself produces the final data. Nothing is executed |
| How result shape is controlled | Tool schema (`parameters`) plus our validator for the arguments | `response_format` (JSON mode or JSON Schema) for the whole reply |
| What can still go wrong | Wrong tool, invalid JSON, missing/extra/wrong-type arguments, invalid values, loops, truncation, valid-looking but wrong arguments | Invalid JSON (JSON mode, truncation), wrong keys/types if the provider ignores the schema, correct shape but wrong content (a wrong department) |
| How code guards against it | Parse, look up, validate against `SCHEMAS`, return errors to the model, retry, step and repeat limits | `json.loads` in try/except, check keys/types, handle "unsupported" errors, retry |
| Support across servers/models | Varies: depends on the model being trained for tools and the server's parser; parallel calls and `strict` differ | Varies: JSON mode is more common; schema mode is less universal |
| Choice for fetch/calculate | **Tool calling**: data lives in our code and the model cannot know it (marks, grades) | Not suitable: the model would have to make the data up |
| Choice for extracting fields | Overkill, no real action to perform | **Structured outputs**: the information is already in the text, we only need it in a clean shape |

## 14. Fault Observation Table

**⬜ REPLACE AFTER RUNNING `python fault_injection.py`:** copy the real "Returned message" and "Handler continued" values from my terminal. I must not leave the placeholders in the final submission.

| Fault | Input | Returned message | Continued? |
|---|---|---|---|
| 1. Invalid JSON | `get_marks`, `{'student_name': 'Logavarshini', 'subject': 'Python'}` | ⬜ REPLACE | ⬜ |
| 2. Unknown tool | `get_attendance`, `{"student_name": "Logavarshini"}` | ⬜ REPLACE | ⬜ |
| 3. Missing required argument | `get_marks`, `{"student_name": "Logavarshini"}` | ⬜ REPLACE | ⬜ |
| 4. Wrong type | `calculate_grade`, `{"marks": "eighty-five"}` | ⬜ REPLACE | ⬜ |
| 5. Enum violation | `get_marks`, subject `Cricket` | ⬜ REPLACE | ⬜ |
| 6. Invented argument | `get_marks`, extra `age: 20` | ⬜ REPLACE | ⬜ |
| 7. Custom: marks out of range | `calculate_grade`, `{"marks": 150}` | ⬜ REPLACE | ⬜ |
| 8. Custom: empty student_name | `get_marks`, `{"student_name": "", "subject": "Python"}` | ⬜ REPLACE | ⬜ |
| 9. Custom: JSON list, not object | `get_marks`, `["Logavarshini", "Python"]` | ⬜ REPLACE | ⬜ |
| 10. Custom: boolean as number | `calculate_grade`, `{"marks": true}` | ⬜ REPLACE | ⬜ |
| 11. Custom: truncated JSON | `get_marks`, `{"student_name": "Logavarshini", "subje` | ⬜ REPLACE | ⬜ |
| 12. Custom: unknown student (passes schema) | `get_marks`, student `Nobody` | ⬜ REPLACE | ⬜ |
| Control: valid call | `get_marks`, Logavarshini / Python | ⬜ REPLACE | ⬜ |

Repeated-identical-call simulation output: ⬜ REPLACE (paste the 4 lines printed at the end of the script).

## 15. Agent Behaviour Table

**⬜ REPLACE AFTER RUNNING `python agent.py`:** use the "RUN SUMMARY" printed after each question. Also record my provider and model: ⬜ provider / ⬜ model.

| Question | Steps | Tool calls | Final answer | Parallel? | finish_reason=length? |
|---|---:|---|---|---|---|
| 1. What is Logavarshini's Python mark? | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2. What is Logavarshini's Python mark and what grade does that mark correspond to? | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3. Get Logavarshini's Cricket mark. | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 4. Explain what a grade means. | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

Note for question 3: record whether the model *tried* `Cricket` (validation caught it), refused on its own, or repaired the call.

## 16. Before and After Guards

**Goal:** show what the guards add, by comparing an *unguarded, Day-3-style* loop with this *guarded Day-6* loop on the same inputs.

**How to run the comparison**
1. Make a throwaway copy of the loop (not part of the submission) that does only this for each tool call:
   `args = json.loads(call.function.arguments)` followed by `result = TOOL_FUNCTIONS[call.function.name](**args)`. It has no validation, no try/except, no repeat limit, and no `length` handling.
2. Feed it the same bad inputs (the fault inputs from section 14 and question 3) and run the same four questions on both versions.
3. Record what happens in each version and fill in the table.

| Input | Unguarded (Day-3 style) result | Guarded (Day-6) result |
|---|---|---|
| Invalid JSON | ⬜ REPLACE (observed) | ⬜ REPLACE |
| Unknown tool | ⬜ | ⬜ |
| Missing argument | ⬜ | ⬜ |
| Wrong type | ⬜ | ⬜ |
| Enum violation (Cricket) | ⬜ | ⬜ |
| Invented argument | ⬜ | ⬜ |
| Question 3 with the real model | ⬜ | ⬜ |

Things to look for: crash vs. error string, a misleading answer vs. an honest one, and one bad call ending the whole run vs. the loop continuing.
If the unguarded version happens to work for some input, I must write that honestly.

## 17. Structured Output Observations

**⬜ REPLACE AFTER RUNNING `python structured_outputs.py`.**
Question: "Extract the student's name, department, and year from this sentence: Logavarshini is a second-year student in Artificial Intelligence and Data Science."

| Mode | Raw model reply | Parsed result / error | Matches requested shape? |
|---|---|---|---|
| No constraint | ⬜ REPLACE | ⬜ | ⬜ |
| JSON mode | ⬜ REPLACE | ⬜ | ⬜ |
| Schema mode | ⬜ REPLACE (or "provider does not support it" with the real error text) | ⬜ | ⬜ |

Provider/model used: ⬜ REPLACE

## 18. Suitability and Conclusion

**Which failures actually happened with the real model?**
⬜ REPLACE using real run results (for example: whether the model sent `Cricket`, produced parallel calls, or hit `length`). If none happened, I say so honestly.

**Which failures were only observed through injection?**
⬜ REPLACE. Typically the failures that the real model did not produce naturally, such as invalid JSON, an unknown tool, or an invented argument, can only be seen through `fault_injection.py`.

**Which guard mattered most?**
⬜ REPLACE with my own conclusion, based on observation. (Design expectation: argument validation with errors returned to the model, because it turns one bad call into a recoverable event instead of a crash or a silently wrong action.)

**When should we use tools?**
When the model needs something it cannot know or cannot do reliably itself: looking up data (marks), exact calculation (grades), or performing an action. Our code does the real work.

**When should we use structured outputs?**
When the needed information is already in the text/context and we just need clean, machine-readable fields (name, department, year). No lookup, calculation or action is involved.

**Why can model tool calls never be blindly trusted?**
A tool call is generated text. It can be invalid JSON, name a tool that does not exist, miss or invent arguments, use wrong types or values, be cut off, or be repeated forever. Even a well-formed call can be wrong in meaning. Running it unchecked could crash the program or perform the wrong action.

**What should every tool-calling loop do?**
Parse safely, look up the tool, validate arguments, execute only after validation, turn every failure into a string result, answer every `tool_call_id`, handle several calls per response, retry on `finish_reason="length"`, detect repeated identical calls, and enforce a maximum step count. Also log each step.

**What can a schema prevent?**
Missing required arguments, wrong types, values outside an enum or range, and invented arguments.

**What can a schema NOT prevent?**
Calls that fit the schema but are wrong in meaning, such as the wrong student, a wrong-but-valid subject, or a made-up name (our `Nobody` test passes the schema, so the tool itself must handle it). It also cannot stop the model from choosing the wrong tool, repeating calls, being cut off, or giving a wrong final answer, and it cannot guarantee that every provider enforces it.

**Why is fault injection useful?**
It makes rare failures happen on demand, offline and repeatably. It proves the handler's failure paths work and never crash, and it makes the guards testable without relying on the model misbehaving.