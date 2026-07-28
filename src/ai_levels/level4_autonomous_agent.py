"""Level 4: planning and memory example for candidate screening."""


class AutonomousGoalAgent:
    def __init__(self, goal: str) -> None:
        self.goal = goal
        self.memory: list[dict[str, str]] = []

    def execute(self) -> None:
        plan = (
            ("Doc JD", "get_job_description[0]"),
            ("Doc ho so", "get_candidate_profile[976112]"),
            ("Cham diem", "score_candidate[0, 976112]"),
        )
        print(f"Goal: {self.goal}")
        for step, (thought, action) in enumerate(plan, start=1):
            result = f"Da hoan thanh {action}"
            self.memory.append({"step": str(step), "thought": thought, "result": result})
            print(f"Step {step}: {thought} -> {action} -> {result}")
        print("Goal Evaluation: HR can xem ho so goc truoc quyet dinh.")


if __name__ == "__main__":
    AutonomousGoalAgent("Danh gia ung vien cho JobID 0").execute()
