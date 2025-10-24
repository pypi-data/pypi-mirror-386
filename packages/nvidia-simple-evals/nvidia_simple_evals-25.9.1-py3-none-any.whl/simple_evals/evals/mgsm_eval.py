"""
MGSM: Multilingual Grade School Math Benchmark (MGSM) is a benchmark of grade-school math problems. 
Language Models are Multilingual Chain-of-Thought Reasoners
Freda Shi, Mirac Suzgun, Markus Freitag, Xuezhi Wang, Suraj Srivats, Soroush Vosoughi, Hyung Won Chung, Yi Tay, Sebastian Ruder, Denny Zhou, Dipanjan Das, Jason Wei
https://arxiv.org/abs/2210.03057 reference: https://github.com/google-research/url-nlp 
"""

import re
from typing import Optional, Any
import random

from datasets import load_dataset


import simple_evals.common as common
from simple_evals.evals.mmlu_eval import HTML_JINJA
from simple_evals.simple_evals_types import Eval, EvalResult, SamplerBase, SingleEvalResult, SeedGenerator

ALL_LANGUAGES = ["bn", "de", "en", "es", "fr", "ja", "ru", "sw", "te", "th", "zh"]
LATIN_LANGUAGES = ["de", "en", "es", "fr", "sw"]
NON_LATIN_LANGUAGES = ["bn", "ja", "ru", "te", "th", "zh"]

LANG_TO_FPATH = {
    "bn": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_bn.tsv",
    "de": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_de.tsv",
    "en": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_en.tsv",
    "es": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_es.tsv",
    "fr": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_fr.tsv",
    "ja": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_ja.tsv",
    "ru": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_ru.tsv",
    "sw": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_sw.tsv",
    "te": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_te.tsv",
    "th": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_th.tsv",
    "zh": "https://openaipublic.blob.core.windows.net/simple-evals/mgsm_zh.tsv",
}
LANG_TO_INSTRUCTIONS = {
    "en": """Solve this math problem. Give the reasoning steps before giving the final answer on the last line by itself in the format of "Answer:". Do not add anything other than the integer answer after "Answer:".

{input}""",
    "bn": """এই গণিতের সমস্যাটি সমাধান করুন। চূড়ান্ত উত্তর দেওয়ার আগে যুক্তিসম্পন্ন পদক্ষেপ প্রদান করুন। চূড়ান্ত উত্তরটি একক সংখ্যা হিসাবে "উত্তর:" এর পরে শেষ লাইনে দিন। "উত্তর:" এর পরে অন্য কিছু যুক্ত করবেন না।.

{input}""",
    "de": """Löse dieses Mathematikproblem. Gib die Schritte zur Begründung an, bevor du die endgültige Antwort in der letzten Zeile alleine im Format "Antwort:" gibst. Füge nichts anderes als die ganzzahlige Antwort nach "Antwort:" hinzu.

{input}""",
    "es": """Resuelve este problema matemático. Proporciona los pasos de razonamiento antes de dar la respuesta final en la última línea por sí misma en el formato de "Respuesta:". No añadas nada más que la respuesta entera después de "Respuesta:".

{input}""",
    "fr": """Résolvez ce problème de mathématiques. Donnez les étapes de raisonnement avant de fournir la réponse finale sur la dernière ligne elle-même dans le format de "Réponse:". N'ajoutez rien d'autre que la réponse entière après "Réponse:".

{input}""",
    "ja": """の数学の問題を解いてください。最終的な答えを出す前に、解答の推論過程を記述してください。そして最後の行には "答え:" の形式で答えを記述し、その後には整数の答え以外何も追加しないでください。

{input}""",
    "ru": """Решите эту математическую задачу. Объясните шаги рассуждения перед тем, как дать окончательный ответ в последней строке сам по себе в формате "Ответ:". Не добавляйте ничего, кроме целочисленного ответа после "Ответ:".

{input}""",
    "sw": """Suluhisha tatizo hili la hesabu. Toa hatua za mantiki kabla ya kutoa jibu la mwisho kwenye mstari wa mwisho peke yake katika muundo wa "Jibu:". Usiongeze chochote kingine isipokuwa jibu la integer baada ya "Jibu:".

{input}""",
    "te": """ఈ గణిత సమస్యను పరిష్కరించండి. చివరి సమాధానాన్ని ఇవ్వదానికి ముందు తర్కాత్మక అదుగులను ఇవ్వండి. చివరి పంక్తిలో మాత్రమే 'సమాధానం:' అనే ఆకారంలో చివరి సమాధానాద్ని ఇవ్వండి సమాధానం: తర్వాత పూర్ణాంక సమాధానానికి తప్పించి ఎదేనా చేర్చవద్దు.

{input}""",
    "th": """แก้ปัญหาคณิตศาสตร์นี้ ให้ให้ขั้นตอนการใช้เหตุผลก่อนที่จะให้คำตอบสุดท้ายในบรรทัดสุดท้ายโดยอยู่ในรูปแบบ "คำตอบ:" ไม่ควรเพิ่มอะไรนอกจากคำตอบที่เป็นจำนวนเต็มหลังจาก "คำตอบ:"

{input}""",
    "zh": """解决这个数学问题。在最后一行给出答案前，请提供推理步骤。最后一行应该以 "答案: " 的形式独立给出答案。在 "答案：" 后不要添加除整数答案之外的任何内容。

{input}""",
}

LANG_TO_ANSWER_PREFIX = {
    "en": "Answer",
    "bn": "উত্তর",
    "de": "Antwort",
    "es": "Respuesta",
    "fr": "Réponse",
    "ja": "答え",
    "ru": "Ответ",
    "sw": "Jibu",
    "te": "సమాధానం",
    "th": "คำตอบ",
    "zh": "答案",
}


def parse_answer(answer: str, answer_prefix: str) -> str:
    if answer_prefix not in answer:
        return ""

    answer_text = answer.split(answer_prefix)[-1].strip()

    # find all the numbers (including decimals) in the string
    numbers = re.findall(r"\d+\.?\d*", answer_text.replace(",", ""))

    # return the first number (removing trailing decimal point if present),
    # or an empty string if there were no numbers
    return numbers[-1].rstrip(".") if numbers else ""


def score_mgsm(target: str, prediction: str) -> bool:
    if "." in prediction:
        prediction = prediction.rstrip("0").rstrip(".")

    target = target.replace(",", "")
    prediction = prediction.replace(",", "")

    return target == prediction


def get_lang_examples(lang: str) -> list[dict[str, str]]:
    # Load dataset for the specified language
    df = load_dataset("juletxara/mgsm", lang)["test"].to_pandas()

    # Initialize an empty list to store examples
    examples = []

    # Iterate through the rows of the DataFrame
    for _, row in df.iterrows():
        # Append each example in the desired format
        examples.append({
            "inputs": row["question"], 
            "targets": str(row["answer_number"]), 
            "lang": lang
        })
    
    return examples


def get_all_examples() -> list[dict[str, str]]:
    examples = []
    for lang in ALL_LANGUAGES:
        if lang != "en":
            continue
        examples += get_lang_examples(lang)
    return examples


class MGSMEval(Eval):
    def __init__(
        self,
        num_examples_per_lang: int = 250,  # restrict to a subset of the data for debugging
        languages: Optional[list[str]] = ALL_LANGUAGES,
        num_threads: int = 10,
        first_n: int | float | None = None,
        cache_dir: str = "cache",
        seed_generator: SeedGenerator | None = None,
        custom_eval_config: Optional[Any] = None,
    ):
        super().__init__(seed_generator=seed_generator, custom_eval_config=custom_eval_config)
        
        if languages is None:
            languages = ALL_LANGUAGES
        else:
            for language in languages:
                if language not in ALL_LANGUAGES:
                    raise ValueError(
                        f"language {language} is not a valid language. "
                        f"It should be one in {ALL_LANGUAGES}"
                    )
        self._languages = languages
        self._num_examples_per_lang = num_examples_per_lang
        self.num_threads = num_threads
        self.first_n = first_n
        self.cache_dir = cache_dir

        examples = []
        for lang in self._languages:
            lang_examples = get_lang_examples(lang)
            lang_examples = lang_examples[:num_examples_per_lang]
            examples.extend(lang_examples)
        self.examples = examples

    async def __call__(self, sampler: SamplerBase) -> EvalResult:
        async def fn(example: dict[str, str], index: int):
            language = example["lang"]
            latin_language = "group_latin" if language in LATIN_LANGUAGES else "group_non_latin"
            correct_answer = example["targets"]
            
            # Use custom config if provided, otherwise use default
            if self.custom_eval_config and self.custom_eval_config.prompt_template:
                # Use custom prompt template
                prompt_content = self.custom_eval_config.format_prompt(input=example["inputs"], instruction=LANG_TO_INSTRUCTIONS[language])
            else:
                # Use default language-specific instructions
                instruction = LANG_TO_INSTRUCTIONS[language]
                prompt_content = instruction.format(input=example["inputs"])
            
            prompt_messages = [
                sampler._pack_message(
                    content=prompt_content, role="user"
                )
            ]

            completion_seed = self.seed_generator.get_seed(index)
            response_text = await sampler(prompt_messages, seed=completion_seed)

            # Use custom extractor if provided, otherwise use default
            if self.custom_eval_config and self.custom_eval_config.extractor:
                extracted_answer = self.custom_eval_config.extract_answer(response_text)
            else:
                # Use default extraction logic
                answer_prefix = LANG_TO_ANSWER_PREFIX[language]
                extracted_answer = parse_answer(response_text, answer_prefix)

            # Use custom scorer if provided, otherwise use default
            if self.custom_eval_config and self.custom_eval_config.scorer:
                score = self.custom_eval_config.score_answer(extracted_answer, correct_answer)
            else:
                # Use default scoring logic
                score = score_mgsm(correct_answer, extracted_answer)

            html = common.jinja_env.from_string(HTML_JINJA).render(
                prompt_messages=prompt_messages,
                next_message=dict(content=response_text, role="assistant"),
                score=score,
                correct_answer=correct_answer,
                extracted_answer=extracted_answer,
            )
            convo = prompt_messages + [dict(content=response_text, role="assistant")]
            return SingleEvalResult(
                html=html,
                score=score,
                convo=convo,
                metrics={language: score, latin_language: score},
            )

        results = await common.map_with_progress(
            fn,
            self.examples,
            num_threads=self.num_threads,
            cache_dir=self.cache_dir,
            first_n=self.first_n
        )
        return common.aggregate_results(results, add_macro=True, task_name="mgsm")
