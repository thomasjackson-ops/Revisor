"""Construcción del prompt, llamado al LLM (Gemini o Anthropic) y parsing estructurado."""

from __future__ import annotations

import json
import random
import re
import time
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

GradoCompletitud = Literal["Completo", "Parcial", "Insuficiente", "No realizado"]

ProviderName = Literal["gemini", "anthropic"]


class Criterio(BaseModel):
    nombre_criterio: str
    puntaje_obtenido: float
    puntaje_maximo: float
    grado_completitud: GradoCompletitud
    feedback: str


class Evaluacion(BaseModel):
    resumen_general: str
    criterios: list[Criterio]
    puntaje_total: float
    puntaje_maximo_total: float
    nota_sugerida: float


class EvaluationError(Exception):
    """Se lanza cuando el LLM no pudo evaluar la entrega tras los reintentos."""


SYSTEM_PROMPT_TEMPLATE = """Eres un asistente de corrección académica extremadamente riguroso, objetivo y ceñido a la rúbrica proporcionada.

REGLAS ESTRICTAS (no negociables):
1. Evalúa ÚNICAMENTE con base en el texto de la entrega que se te entrega a continuación. No inventes contenido que no esté presente en la entrega.
1b. La entrega puede incluir más de un archivo (por ejemplo, un documento de investigación en PDF/Word y una planilla de datos en Excel/CSV con una base de contactos). Cada archivo aparece delimitado con un encabezado "=== Archivo: nombre (tipo) ===". Debes integrar la información de TODOS los archivos entregados al evaluar los criterios correspondientes (por ejemplo, un criterio sobre la base de datos de contactos debe evaluarse revisando el contenido de la planilla adjunta, no solo el documento de texto).
2. No alucines apartados, puntajes ni logros que no puedas justificar directamente citando o parafraseando el contenido real de la entrega.
3. Debes evaluar TODOS y CADA UNO de los criterios de la rúbrica, en el mismo orden en que aparecen, sin omitir ninguno.
4. Para cada criterio, asigna un `puntaje_obtenido` entre 0 y el `puntaje_maximo` de ese criterio (puede ser decimal).
5. El campo `grado_completitud` debe ser exactamente uno de: "Completo", "Parcial", "Insuficiente", "No realizado".
6. El campo `feedback` de cada criterio debe tener entre 2 y 3 líneas, ser conciso, constructivo y explicar concretamente qué faltó o qué estuvo correcto.
7. Si la entrega está vacía, incompleta o no corresponde al tema, marca los criterios pertinentes como "No realizado" con puntaje 0 y explica el motivo en el feedback, sin inventar contenido.
8. Calcula `puntaje_total` como la suma exacta de los `puntaje_obtenido` de todos los criterios, y `puntaje_maximo_total` como la suma de los `puntaje_maximo` de la rúbrica.
9. Calcula `nota_sugerida` en la escala {escala_min} a {escala_max}, aplicando la fórmula estándar chilena:
   nota = {escala_min} + (puntaje_total / puntaje_maximo_total) * ({escala_max} - {escala_min})
   Redondea a un decimal.
10. Responde EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional antes ni después, sin bloques de código markdown, que cumpla EXACTAMENTE este esquema:

{{
  "resumen_general": "string, 2-4 líneas resumiendo el desempeño general",
  "criterios": [
    {{
      "nombre_criterio": "string",
      "puntaje_obtenido": float,
      "puntaje_maximo": float,
      "grado_completitud": "Completo" | "Parcial" | "Insuficiente" | "No realizado",
      "feedback": "string de 2-3 líneas"
    }}
  ],
  "puntaje_total": float,
  "puntaje_maximo_total": float,
  "nota_sugerida": float
}}

RÚBRICA ACTIVA:
---
{rubrica}
---
"""

USER_PROMPT_TEMPLATE = """A continuación se entrega el texto completo extraído de la entrega del estudiante llamada "{filename}".

Evalúa esta entrega estrictamente según la rúbrica activa y las reglas del sistema. Responde solo con el JSON solicitado.

TEXTO DE LA ENTREGA:
---
{contenido}
---
"""


def build_prompts(rubrica: str, filename: str, contenido: str, escala_min: float, escala_max: float) -> tuple[str, str]:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        rubrica=rubrica, escala_min=escala_min, escala_max=escala_max
    )
    user_prompt = USER_PROMPT_TEMPLATE.format(filename=filename, contenido=contenido)
    return system_prompt, user_prompt


def _extract_json_block(raw_text: str) -> str:
    """Limpia respuestas que vengan envueltas en bloques markdown ```json ... ```."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
    if fenced:
        return fenced.group(1)

    first_brace = raw_text.find("{")
    last_brace = raw_text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return raw_text[first_brace : last_brace + 1]

    return raw_text


def _call_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    if not response.text:
        raise EvaluationError("Gemini devolvió una respuesta vacía.")
    return response.text


def _call_anthropic(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise EvaluationError("Anthropic devolvió una respuesta sin texto.")
    return "\n".join(text_blocks)


def evaluar_entrega(
    provider: ProviderName,
    api_key: str,
    model: str,
    rubrica: str,
    filename: str,
    contenido: str,
    escala_min: float = 1.0,
    escala_max: float = 7.0,
    max_retries: int = 4,
    base_delay: float = 2.0,
) -> Evaluacion:
    """Envía la entrega al LLM configurado y devuelve la evaluación validada.

    Reintenta con backoff exponencial ante errores transitorios (rate limit,
    errores 5xx, JSON malformado). Lanza EvaluationError si se agotan los reintentos.
    """
    system_prompt, user_prompt = build_prompts(rubrica, filename, contenido, escala_min, escala_max)

    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            if provider == "gemini":
                raw_text = _call_gemini(api_key, model, system_prompt, user_prompt)
            elif provider == "anthropic":
                raw_text = _call_anthropic(api_key, model, system_prompt, user_prompt)
            else:
                raise EvaluationError(f"Proveedor no soportado: {provider}")

            json_text = _extract_json_block(raw_text)
            data = json.loads(json_text)
            return Evaluacion.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
        except Exception as exc:
            last_error = exc

            error_name = type(exc).__name__.lower()
            is_retryable = any(
                token in error_name for token in ("ratelimit", "timeout", "connection", "internalserver", "apistatus")
            )
            if not is_retryable and attempt == 0:
                pass

        if attempt < max_retries - 1:
            delay = min(base_delay * (2**attempt) + random.uniform(0, 1), 60.0)
            time.sleep(delay)

    raise EvaluationError(
        f"No se pudo evaluar '{filename}' tras {max_retries} intentos. Último error: {last_error}"
    )
