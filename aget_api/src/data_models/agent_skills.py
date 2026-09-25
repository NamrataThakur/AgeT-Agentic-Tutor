from enum import Enum

class AgentSkill(str, Enum):
    EVALUATE_ANSWER = "answer_evaluation"
    GENERATE_HINT = "hint_generation"
    ASK_QUESTION = "question_generation"
    GENERATE_EXPLANATION = "concept_explanation"
    SUMMARIZE = "summary_generation"