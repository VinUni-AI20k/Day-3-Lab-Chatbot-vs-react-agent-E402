"""Level 3: Thought -> Action -> Observation recruitment example."""


def get_job_description(job_id: str) -> str:
    return f"Job {job_id}: Sale Admin Website, yeu cau 1-3 nam kinh nghiem."


def reactive_agent_step(user_goal: str) -> None:
    print(f"Goal: {user_goal}")
    print("Thought: Can doc yeu cau cong viec truoc.")
    print("Action: get_job_description[0]")
    print(f"Observation: {get_job_description('0')}")
    print("Final Answer: Da co thong tin JobID 0 de HR tiep tuc danh gia.")


if __name__ == "__main__":
    reactive_agent_step("Xem JobID 0")
