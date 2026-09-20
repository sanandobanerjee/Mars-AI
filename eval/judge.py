import json
import re
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from groq import RateLimitError

from src.config import GROQ_API_KEY, GROQ_MODEL
from eval.schemas import EvalQuestion, JudgeScore

_judge_llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)


def _build_prompt(question: EvalQuestion, answer: str) -> str:
    adversarial_instruction = ""
    if question.difficulty == "adversarial":
        adversarial_instruction = (
            "This question asks about functionality that does not exist in the codebase. "
            "Set avoided_fabrication to true only if the answer correctly states the "
            "functionality is absent, without inventing a plausible-sounding but false "
            "explanation."
        )

    avoided_field = '"avoided_fabrication": null, ' if question.difficulty != "adversarial" else '"avoided_fabrication": true, '

    return (
        "You are grading an AI coding assistant's answer to a question about a codebase.\n\n"
        f"Question: {question.question}\n\n"
        f"Reference (ground truth) answer: {question.ground_truth}\n\n"
        f"AI's actual answer: {answer}\n\n"
        f"{adversarial_instruction}\n\n"
        "Score the AI's answer on:\n"
        "- faithfulness (0.0-1.0): does the answer avoid making claims not supported by "
        "the reference or plausible codebase knowledge, i.e. does it avoid hallucinating?\n"
        "- correctness (0.0-1.0): how well does the answer match the reference answer's "
        "substance, even if worded differently?\n\n"
        "Respond with ONLY a JSON object, no other text, in this exact shape:\n"
        '{"faithfulness": 0.0, "correctness": 0.0, ' + avoided_field + '"reasoning": "one short sentence"}'
    )


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
)
def _call_judge(prompt: str) -> str:
    response = _judge_llm.invoke(prompt)
    return response.content.strip()


def judge_answer(question: EvalQuestion, answer: str) -> JudgeScore:
    prompt = _build_prompt(question, answer)
    raw = _call_judge(prompt)

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    json_text = match.group(0) if match else raw

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        return JudgeScore(faithfulness=0.0, correctness=0.0, avoided_fabrication=None, reasoning="Judge output could not be parsed")

    return JudgeScore(
        faithfulness=float(parsed.get("faithfulness", 0.0)),
        correctness=float(parsed.get("correctness", 0.0)),
        avoided_fabrication=parsed.get("avoided_fabrication"),
        reasoning=str(parsed.get("reasoning", "")),
    )