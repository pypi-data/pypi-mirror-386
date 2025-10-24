# -*- coding: utf-8 -*-

# Contributors:
#    Antonio López Martínez-Carrasco <antoniolopezmc1995@gmail.com>

"""This file contains the implementation of the mapper that follows a Few-Shot approach and uses LLMs from ollama.
"""
import pandas as pd
from ollama import Client
from typing import Mapping, Sequence, Any

class FewShotAndOllama(object):
    """This class represent a mapper that follows a Few-Shot approach and uses LLMs from ollama.
    
    :param random_state:
    :param number_of_shots:
    :param model_name:
    :params_for_ollama_client:
    """

    def __init__(self, random_state : pd._typing.RandomState,
                 number_of_shots : int,
                 model_name : str,
                 params_for_ollama_client : Mapping):
        _random_state = random_state
        _number_of_shots = number_of_shots
        _model_name = model_name
        _ollama_client = Client(**params_for_ollama_client)
        _general_prompt = '''You are a clinical coding expert. Read the following medical note and determine if the diagnosis corresponding to ICD-9 code [CODE]: "[CODE_DESCRIPTION]" is present in the note.

Your task:
Return your answer in a JSON object with the following **exact format** and keys:
{
  "code_present": 1 or 0,
  "explanation": "Brief justification including the specific phrases or sentences in the note that support your decision."
}

Formatting rules:
- Output must be **valid JSON**. Do not include any text before or after the JSON.
- The JSON object must contain **only** the two keys: "code_present" and "explanation".
- "code_present" must be an integer (1 or 0).
- "explanation" must be a single-line string, 1–3 sentences, without line breaks or additional keys.
- Do not include markdown, commentary, or quotes outside the JSON.

Decision rules:
- Output 1 if the diagnosis is explicitly or implicitly present or clearly supported by clinical evidence.
- Output 0 if the diagnosis is not mentioned, ruled out, or lacks supporting evidence.
- Consider synonyms, abbreviations, and equivalent clinical expressions.
- Ignore mentions in family history, hypothetical, or differential contexts.

Medical note:
"[MEDICAL_NOTE]"
'''

    def map(self, list_of_texts : Sequence[str], icd9_code : Mapping[str, str], include_explanation : bool = True) -> Mapping[str, Any] | Sequence[int]:
        """Method to map an ICD-9 code from a text.
        """
        pass
    
