def agent_evaluation_remove(data: str) -> str:
    if "<agent_evaluation>" in data and "</agent_evaluation>" in data:
        data = (
            data[: data.find("<agent_evaluation>")]
            + data[data.find("</agent_evaluation>") + 19 :]
        )
    return data


def need_print_check(message: str) -> bool:
    return (
        not message.startswith("<Transfer_Tool>")
        and not message.startswith("Memories related to the user request:")
        and not message.startswith("Need to tailor response bases on this")
    )
