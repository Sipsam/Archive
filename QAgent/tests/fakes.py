"""Small API-free test doubles for deterministic Agent evaluation."""


class FakeAgentClient:
    def __init__(self, responses: dict[str, str]):
        self._responses = responses
        self.calls: list[str] = []

    def generate(self, case_id: str) -> str:
        self.calls.append(case_id)
        return self._responses[case_id]
