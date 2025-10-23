import asyncio
from ....config import TRACE_LOG 
from ....core.constants import ConstantsTable
from ....core.extraction.prompts.utils import parse_string_into_merge_action
from ....core.extraction.prompts.router import PROMPTS, UpdateResponse
from ....models.profile_topic import UserProfileTopic, SubTopic, ProfileConfig
from ....llm.complete import llm_complete
from ....models.promise import Promise, CODE
from ....models.response import ProfileData
from ....models.types import MergeAddResult


async def merge_or_valid_new_memos(
    user_id: str,
    fact_contents: list[str],
    fact_attributes: list[dict],
    profiles: list[ProfileData],
    profile_config: ProfileConfig,
    total_profiles: list[UserProfileTopic],
    config,
) -> Promise[MergeAddResult]:
    assert len(fact_contents) == len(
        fact_attributes
    ), "Length of fact_contents and fact_attributes must be equal"
    DEFINE_MAPS = {
        (p.topic, sp.name): sp for p in total_profiles for sp in p.sub_topics
    }

    RUNTIME_MAPS = {
        (p.attributes[ConstantsTable.topic], p.attributes[ConstantsTable.sub_topic]): p
        for p in profiles
    }

    profile_session_results: MergeAddResult = {
        "add": [],
        "update": [],
        "delete": [],
        "update_delta": [],
        "before_profiles": profiles,
    }
    tasks = []
    for f_c, f_a in zip(fact_contents, fact_attributes):
        task = handle_profile_merge_or_valid(
            user_id,
            f_a,
            f_c,
            profile_config,
            RUNTIME_MAPS,
            DEFINE_MAPS,
            profile_session_results,
            config,
        )
        tasks.append(task)
    await asyncio.gather(*tasks)
    return Promise.resolve(profile_session_results)


async def handle_profile_merge_or_valid(
    user_id: str,
    profile_attributes: dict,
    profile_content: str,
    profile_config: ProfileConfig,
    profile_runtime_maps: dict[tuple[str, str], ProfileData],
    profile_define_maps: dict[tuple[str, str], SubTopic],
    session_merge_validate_results: MergeAddResult,
    config,  # System config
) -> Promise[None]:
    KEY = (
        profile_attributes[ConstantsTable.topic],
        profile_attributes[ConstantsTable.sub_topic],
    )
    USE_LANGUAGE = profile_config.language or config.language
    PROFILE_VALIDATE_MODE = (
        profile_config.profile_validate_mode
        if profile_config.profile_validate_mode is not None
        else config.profile_validate_mode
    )
    runtime_profile = profile_runtime_maps.get(KEY, None)
    define_sub_topic = profile_define_maps.get(KEY, SubTopic(name=""))

    if (
        not PROFILE_VALIDATE_MODE
        and not define_sub_topic.validate_value
        and runtime_profile is None
    ):
        TRACE_LOG.info(
            user_id,
            f"Skip validation: {KEY}",
        )
        session_merge_validate_results["add"].append(
            {
                "content": profile_content,
                "attributes": profile_attributes,
            }
        )
        return Promise.resolve(None)
    r = await llm_complete(
        PROMPTS[USE_LANGUAGE]["merge"].get_input(
            KEY[0],
            KEY[1],
            runtime_profile.content if runtime_profile else None,
            profile_content,
            update_instruction=define_sub_topic.update_description,  # maybe none
            topic_description=define_sub_topic.description,  # maybe none
        ),
        system_prompt=PROMPTS[USE_LANGUAGE]["merge"].get_prompt(),
        temperature=0.2,  # precise
        config=config,
        **PROMPTS[USE_LANGUAGE]["merge"].get_kwargs(),
    )
    # print(KEY, profile_content)
    # print(r.data())
    if not r.ok():
        TRACE_LOG.warning(
            user_id,
            f"Failed to merge profiles: {r.msg()}",
        )
        return Promise.reject(r.code(), r.msg())
    update_response: UpdateResponse | None = parse_string_into_merge_action(r.data())
    if update_response is None:
        TRACE_LOG.warning(
            user_id,
            f"Failed to parse merge action: {r.data()}",
        )
        return Promise.reject(
            CODE.SERVER_PARSE_ERROR, "Failed to parse merge action of Memobase"
        )
    if update_response["action"] == "UPDATE":
        if runtime_profile is None:
            session_merge_validate_results["add"].append(
                {
                    "content": update_response["memo"],
                    "attributes": profile_attributes,
                }
            )
        else:
            if ConstantsTable.update_hits not in runtime_profile.attributes:
                runtime_profile.attributes[ConstantsTable.update_hits] = 1
            else:
                runtime_profile.attributes[ConstantsTable.update_hits] += 1
            session_merge_validate_results["update"].append(
                {
                    "profile_id": runtime_profile.id,
                    "content": update_response["memo"],
                    "attributes": runtime_profile.attributes,
                }
            )
            session_merge_validate_results["update_delta"].append(
                {
                    "content": profile_content,
                    "attributes": profile_attributes,
                }
            )
    elif update_response["action"] == "APPEND":
        if runtime_profile is None:
            session_merge_validate_results["add"].append(
                {
                    "content": profile_content,
                    "attributes": profile_attributes,
                }
            )
        else:
            if ConstantsTable.update_hits not in runtime_profile.attributes:
                runtime_profile.attributes[ConstantsTable.update_hits] = 1
            else:
                runtime_profile.attributes[ConstantsTable.update_hits] += 1
            session_merge_validate_results["update"].append(
                {
                    "profile_id": runtime_profile.id,
                    "content": f"{runtime_profile.content};{profile_content}",
                    "attributes": runtime_profile.attributes,
                }
            )
            session_merge_validate_results["update_delta"].append(
                {
                    "content": profile_content,
                    "attributes": profile_attributes,
                }
            )
    elif update_response["action"] == "ABORT":
        if runtime_profile is None:
            TRACE_LOG.info(
                user_id,
                f"Invalid profile: {KEY}::{profile_content}, abort it\n<raw_response>\n{r.data()}\n</raw_response>",
            )
        else:
            TRACE_LOG.info(
                user_id,
                f"Invalid merge: {runtime_profile.attributes}, {profile_content}, abort it\n<raw_response>\n{r.data()}\n</raw_response>",
            )
            # session_merge_validate_results["delete"].append(runtime_profile.id)
        return Promise.resolve(None)
    else:
        TRACE_LOG.warning(
            user_id,
            f"Invalid action: {update_response['action']}",
        )
        return Promise.reject(
            CODE.SERVER_PARSE_ERROR, "Failed to parse merge action of Memobase"
        )
    return Promise.resolve(None)
