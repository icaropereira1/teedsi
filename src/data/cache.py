"""Cache em disco das respostas brutas do LLM.

Por que existe: temperature=0.1 reduz variação, não produz determinismo. No
backtest o agente é chamado N CEOs x M datas de corte; sem cache o custo se
repete a cada execução e o resultado nunca se reproduz — violando o
princípio nº 1 do README.

A chave é o hash do pedido inteiro (modelo + system instruction + prompt +
schema), então qualquer mudança de prompt ou de evidência invalida a entrada
em vez de devolver silenciosamente algo velho.
"""

import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CACHE_DIR = Path(".cache") / "investigator"

# Suba isto ao mudar a semântica do prompt de um jeito que o texto não capture.
PROMPT_VERSION = "1"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "sem-nome"


def request_fingerprint(
    model: str,
    system_instruction: str,
    prompt: str,
    response_schema_json: str,
    prompt_version: str = PROMPT_VERSION,
) -> str:
    """Hash de tudo que determina a resposta. Muda o pedido, muda a chave."""
    payload = json.dumps(
        {
            "prompt_version": prompt_version,
            "model": model,
            "system_instruction": system_instruction,
            "prompt": prompt,
            "response_schema": response_schema_json,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class ResponseCache:
    """Guarda o JSON bruto do LLM em .cache/investigator/<ceo>/<data>/<hash>.json

    Respostas que falharam na validação vão para '<hash>.invalid.json' e nunca
    são servidas como cache-hit: ficam ali só para depuração.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        if root is None:
            root = os.getenv("INVESTIGATOR_CACHE_DIR") or DEFAULT_CACHE_DIR
        self.root = Path(root)

    def _path(
        self,
        ceo_name: str,
        cutoff_date: date,
        fingerprint: str,
        invalid: bool = False,
    ) -> Path:
        nome = f"{fingerprint}.invalid.json" if invalid else f"{fingerprint}.json"
        return self.root / _slug(ceo_name) / cutoff_date.isoformat() / nome

    def get(
        self, ceo_name: str, cutoff_date: date, fingerprint: str
    ) -> Optional[str]:
        path = self._path(ceo_name, cutoff_date, fingerprint)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Cache corrompido é tratado como miss, não como erro fatal.
            return None
        raw = payload.get("raw_response")
        return raw if isinstance(raw, str) else None

    def put(
        self,
        ceo_name: str,
        cutoff_date: date,
        fingerprint: str,
        raw_response: str,
        meta: Dict[str, Any],
        invalid_reason: Optional[str] = None,
    ) -> Path:
        path = self._path(
            ceo_name, cutoff_date, fingerprint, invalid=invalid_reason is not None
        )
        path.parent.mkdir(parents=True, exist_ok=True)

        payload: Dict[str, Any] = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "fingerprint": fingerprint,
            "meta": meta,
            "raw_response": raw_response,
        }
        if invalid_reason is not None:
            payload["invalid_reason"] = invalid_reason

        # Escrita atômica: um Ctrl-C no meio do backtest não deixa JSON truncado.
        tmp = path.parent / (path.name + ".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(path)
        return path
