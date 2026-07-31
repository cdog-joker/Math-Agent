from llm_client import DemoRuleClient
from user_agent import ReasoningAgent


def test_agent_contract_returns_json_serializable_dict():
    agent = ReasoningAgent(client=DemoRuleClient())
    result = agent.solve("计算 17+25 的值。", {"idx": 1})

    assert isinstance(result, dict)
    assert isinstance(result["final_response"], str)
    assert result["final_response"]
    assert isinstance(result.get("trace", []), list)
