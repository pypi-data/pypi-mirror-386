from datetime import datetime

ADD_KWARGS = {"prompt_id": "zh_merge_profile"}

MERGE_FACTS_PROMPT = """你负责用户的备忘录的维护。
你的工作是判断新的补充信息如何与当前备忘录合并。
你应该判断新的补充信息是直接添加，更新还是放弃合并。
用户会提供备忘录的主题/子主题，也可能会提供主题描述和特定的更新要求。

以下是你的输出动作：
1. 直接添加：如果补充信息带来了新的信息，你应该直接添加。如果当前备忘录为空的话，你应该直接添加补充信息。
2. 更新备忘录：如果补充信息与当前备忘录有冲突或者你需要修改当前备忘录才能更好的体现当前的信息，你应该更新备忘录。
3. 放弃合并：如果补充信息本身没有价值，或者信息已经被当前备忘录完全包含了，或者不符合当前备忘录的内容要求，你应该放弃合并。

## 思考
在你输出动作之前，你需要先思考如下的内容：
1. 补充信息是否符合备忘录的主题描述
    1.1. 如果不符合的话，判断是否可以从补充信息中修改得到符合备忘录要求的内容，然后处理你修改后的补充信息
    1.2. 如果无法通过修改补充信息使其满足主题描述，你应该放弃合并
3. 符合当前备忘录要求的补充信息，你需要参考上面的描述进行输出动作的判断
4. 如果选择更新备忘录的话，同时思考下是否当前备忘录有其余的部分可以精简或者去除。

额外情况：
1. 当前备忘录可能为空，在这个情况下，思考1之后如果可以得到符合要求的补充信息，直接添加即可
2. 如果更新要求不为空，你需要参考用户的更新要求进行思考

## 输出动作
### 直接添加
```
- APPEND{tab}APPEND
```
如果选择直接添加，直接输出`APPEND`单词即可，不需要复述内容
### 更新备忘录
```
- UPDATE{tab}[UPDATED_MEMO]
```
在`[UPDATED_MEMO]`中，你需要重新写出更新后完整的当前备忘录
### 放弃合并
```
- ABORT{tab}ABORT
```
如果选择放弃合并，直接输出`ABORT`单词即可，不需要复述内容

## 输出模版
根据上述说明，你的输出应该是如下的模版

THOUGHT
---
ACTION

其中:
- `THOUGHT`是你的思考过程
- `ACTION`是你的输出动作
比如：
```example
补充信息中提到了用户当前的学习目标是准备期末考试，当前主题描述记录的是用户的学习目标，符合要求。同时，当前备忘录中还有准备期中考试的记录，推断来说期中考试应该已经结束了。所以补充信息不能简单的添加，而是需要更新当前备忘录。
我需要更新对应的区域，同时保留剩余的备忘录
---
- UPDATE{tab}...使用多邻国自学日语中，希望可以通过日语二级考试[提及于2025/05/05]; 准备期末考试中[提及于2025/06/01];
```

遵循以下说明：
- 严格遵守正确的输出格式。
- 确保最终备忘录不超过5句话。始终保持简洁并输出备忘录的要点。
- 永远不要编造输入中未提到的内容。
- 保留新旧备忘录中的时间标注（例如： XXX[提及于 2025/05/05, 发生于 2022]）。
- 如果决定更新，确保最终备忘录简洁且没有冗余信息。（例如："User is sad; User's mood is sad" == "User is sad"）

以上就是全部内容，现在执行你的工作。
"""


def get_input(
    topic, subtopic, old_memo, new_memo, update_instruction=None, topic_description=None, config=None
):
    today = datetime.now().strftime("%Y-%m-%d") if config is None else datetime.now().astimezone(config.timezone).strftime("%Y-%m-%d")
    return f"""今天是{today}。
## 备忘录更新要求
{update_instruction or "[empty]"}
### 备忘录主题描述
{topic_description or "[empty]"}
## 备忘录主题
{topic}, {subtopic}
## 当前备忘录
{old_memo or "[empty]"}
## 补充信息
{new_memo}
"""


def get_prompt(config=None) -> str:
    return MERGE_FACTS_PROMPT.format(
        tab=config.llm_tab_separator if config else "::",
    )


def get_kwargs() -> dict:
    return ADD_KWARGS


if __name__ == "__main__":
    print(get_prompt())
