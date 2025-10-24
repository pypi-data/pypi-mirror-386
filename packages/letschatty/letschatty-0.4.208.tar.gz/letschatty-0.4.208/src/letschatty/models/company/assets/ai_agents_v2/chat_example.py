from pydantic import BaseModel, Field, model_validator
from typing import List, Any, ClassVar
from enum import StrEnum
from letschatty.models.base_models.ai_agent_component import AiAgentComponent


class ExampleElementType(StrEnum):
    """Type of an example element"""
    USER = "user"
    AI = "ai"
    CHAIN_OF_THOUGHT = "chain_of_thought"

class ExampleElement(BaseModel):
    """An element of a chat example"""
    type: ExampleElementType = Field(..., description="Type of the element")
    content: str = Field(..., description="Content of the element")

    def to_string(self) -> str:
        return self.type.value + ": " + self.content

class ChatExample(AiAgentComponent):
    """Example conversation for training the AI agent"""
    content: List[ExampleElement] = Field(..., description="Sequence of elements in this example")
    is_essential: bool = Field(default=False, description="Whether the example is essential for the ai agent to work")
    is_training_example: bool = Field(default=True, description="Whether the example is a training example or just a test example")

    def to_string(self) -> str:
        result = ""
        for element in self.content:
            result += element.to_string() + "\n"
        return result

    @model_validator(mode='after')
    def check_that_test_cases_are_only_for_one_ai_agent(self):
        """If a chat example is NOT a training example, it must have an only_ai_agent_id"""
        if not self.is_training_example and self.is_only_for_one_ai_agent:
            raise ValueError("Chat example must have an ai_agent_id if it is not a training example")
        return self

    @property
    def is_only_for_quality_tests(self) -> bool:
        """Check if the chat example is only for quality tests"""
        return not self.is_training_example