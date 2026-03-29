"""
Evolution API Client
======================
HTTP client para a Evolution API (v2) — envio de mensagens texto,
áudio (OGG/OPUS) e imagem via WhatsApp.

Docs: https://doc.evolution-api.com
"""

from __future__ import annotations

import base64
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


class EvolutionClient:
    """Cliente para a Evolution API.

    Variáveis de ambiente esperadas:
        EVOLUTION_API_URL    — ex: http://localhost:8080
        EVOLUTION_API_KEY    — chave configurada no servidor Evolution
        EVOLUTION_INSTANCE   — nome da instância (ex: "shadowing")
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
        self.api_key = os.getenv("EVOLUTION_API_KEY", "changeme-secret-key").strip()
        self.instance = os.getenv("EVOLUTION_INSTANCE", "shadowing")
        self._session = requests.Session()
        self._session.headers.update({
            "apikey": self.api_key,
            "Content-Type": "application/json",
        })

    # ─────────────────────────── Low-level helpers ───────────────────────────

    def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        try:
            resp = self._session.post(url, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.json() if resp.text.strip() else {"ok": True}
        except requests.RequestException as exc:
            logger.error("Evolution API error [%s]: %s", url, exc)
            return {"error": str(exc)}

    def _get(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            resp = self._session.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json() if resp.text.strip() else {"ok": True}
        except requests.RequestException as exc:
            logger.error("Evolution API GET error [%s]: %s", url, exc)
            return {"error": str(exc)}

    @staticmethod
    def _phone_to_jid(phone: str) -> str:
        """Converte número para JID ou reaproveita JID já recebido do webhook."""
        raw = str(phone or "").strip()
        if "@" in raw:
            return raw
        digits = "".join(c for c in raw if c.isdigit())
        return f"{digits}@s.whatsapp.net" if digits else raw

    # ─────────────────────────── Instance management ──────────────────────────

    def create_instance(self, webhook_url: str | None = None) -> dict[str, Any]:
        """Cria a instância no Evolution API (apenas na primeira vez)."""
        payload: dict[str, Any] = {
            "instanceName": self.instance,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        }
        # Evolution v2.2.x valida a propriedade webhook no create.
        if webhook_url:
            payload["webhook"] = {
                "url": webhook_url,
                "byEvents": False,
                "base64": False,
                "events": [
                    "QRCODE_UPDATED",
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE",
                    "CONNECTION_UPDATE",
                ],
            }
        return self._post("instance/create", payload)

    def get_qrcode(self, number: str | None = None) -> dict[str, Any]:
        """Retorna o QR Code para conectar o WhatsApp."""
        params: dict[str, Any] = {}
        digits = "".join(c for c in str(number or "") if c.isdigit())
        if digits:
            params["number"] = digits
        token = self.instance_token()
        result: dict[str, Any] | Any
        if token:
            result = self._get(
                f"instance/connect/{self.instance}",
                params=params or None,
                headers={"apikey": token},
            )
        else:
            result = self._get(f"instance/connect/{self.instance}", params=params or None)

        # Fallback: usa a chave global quando o token não funciona.
        if isinstance(result, dict):
            error_text = str(result.get("error", "")).lower()
            if token and ("401" in error_text or "403" in error_text):
                result = self._get(f"instance/connect/{self.instance}", params=params or None)
        return result if isinstance(result, dict) else {"data": result}

    def instance_status(self) -> dict[str, Any]:
        """Verifica o status da conexão da instância."""
        data = self._get(f"instance/connectionState/{self.instance}")
        if isinstance(data, dict) and not data.get("error"):
            return data

        # Fallback para instalações em que o endpoint de estado falha.
        for item in self.fetch_instances():
            if item.get("name") == self.instance:
                return {
                    "instance": {
                        "instanceName": self.instance,
                        "state": item.get("connectionStatus", "close"),
                    }
                }
        return data if isinstance(data, dict) else {"data": data}

    def fetch_instances(self) -> list[dict[str, Any]]:
        """Lista instâncias disponíveis no Evolution."""
        raw = self._get("instance/fetchInstances")
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        return []

    def instance_token(self) -> str:
        """Obtém token da instância atual (usado por alguns endpoints do manager)."""
        for item in self.fetch_instances():
            if item.get("name") == self.instance:
                return str(item.get("token", "")).strip()
        return ""

    def set_webhook(self, webhook_url: str) -> dict[str, Any]:
        """Configura o webhook para receber mensagens."""
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "byEvents": False,
                "base64": False,
                "events": [
                    "QRCODE_UPDATED",
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE",
                    "CONNECTION_UPDATE",
                ],
            }
        }
        token = self.instance_token()
        if token:
            result = self._post(
                f"webhook/set/{self.instance}",
                payload,
                headers={"apikey": token},
            )
            if isinstance(result, dict) and not result.get("error"):
                return result
        return self._post(f"webhook/set/{self.instance}", payload)

    def get_media_base64_from_message(
        self,
        message_data: dict[str, Any],
        *,
        convert_to_mp4: bool = False,
    ) -> dict[str, Any]:
        """Baixa mídia recebida no webhook em base64 via Evolution.

        O endpoint espera o objeto completo `data` da mensagem recebida
        no evento `MESSAGES_UPSERT`.
        """
        payload: dict[str, Any] = {"message": message_data}
        if convert_to_mp4:
            payload["convertToMp4"] = True

        endpoint = f"chat/getBase64FromMediaMessage/{self.instance}"
        token = self.instance_token()
        if token:
            result = self._post(endpoint, payload, headers={"apikey": token})
            if isinstance(result, dict):
                error_text = str(result.get("error", "")).lower()
                if not ("401" in error_text or "403" in error_text):
                    return result
            else:
                return result

        return self._post(endpoint, payload)

    # ─────────────────────────── Messaging ────────────────────────────────────

    def send_text(self, phone: str, text: str, *, delay: int = 1200) -> dict[str, Any]:
        """Envia mensagem de texto simples."""
        jid = self._phone_to_jid(phone)
        result = self._post(
            f"message/sendText/{self.instance}",
            {
                "number": jid,
                "text": text,
                "delay": delay,  # ms — simula digitação humana
            },
        )
        # Fallback para payloads novos com @lid: tenta rota clássica @s.whatsapp.net.
        if isinstance(result, dict) and result.get("error") and jid.endswith("@lid"):
            digits = "".join(c for c in jid.split("@", 1)[0] if c.isdigit())
            if digits:
                return self._post(
                    f"message/sendText/{self.instance}",
                    {
                        "number": f"{digits}@s.whatsapp.net",
                        "text": text,
                        "delay": delay,
                    },
                )
        return result

    def send_audio(
        self,
        phone: str,
        audio_path: str | Path,
        *,
        ptt: bool = True,
    ) -> dict[str, Any]:
        """Envia áudio como nota de voz (ptt=True) ou arquivo de áudio.

        Converte WAV → OGG/OPUS automaticamente via ffmpeg se necessário.
        """
        audio_path = Path(audio_path)
        jid = self._phone_to_jid(phone)

        ogg_path = self._ensure_ogg(audio_path)
        with open(ogg_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()

        return self._post(
            f"message/sendMedia/{self.instance}",
            {
                "number": jid,
                "mediatype": "audio",
                "mimetype": "audio/ogg; codecs=opus",
                "media": audio_b64,
                "fileName": ogg_path.name,
                "caption": "",
                "ptt": ptt,
            },
        )

    def send_audio_b64(
        self,
        phone: str,
        audio_b64: str,
        *,
        ptt: bool = True,
    ) -> dict[str, Any]:
        """Envia áudio já em base64 (deve ser OGG/OPUS)."""
        jid = self._phone_to_jid(phone)
        return self._post(
            f"message/sendMedia/{self.instance}",
            {
                "number": jid,
                "mediatype": "audio",
                "mimetype": "audio/ogg; codecs=opus",
                "media": audio_b64,
                "fileName": "lesson_audio.ogg",
                "caption": "",
                "ptt": ptt,
            },
        )

    def send_reaction(self, phone: str, message_id: str, emoji: str = "✅") -> dict[str, Any]:
        """Reage a uma mensagem do aluno."""
        jid = self._phone_to_jid(phone)
        return self._post(
            f"message/sendReaction/{self.instance}",
            {
                "key": {"remoteJid": jid, "id": message_id},
                "reaction": emoji,
            },
        )

    # ─────────────────────────── Audio conversion ─────────────────────────────

    @staticmethod
    def _ensure_ogg(audio_path: Path) -> Path:
        """Converte WAV para OGG/OPUS via ffmpeg. Retorna o path do OGG."""
        if audio_path.suffix.lower() in {".ogg", ".opus"}:
            return audio_path

        ogg_path = audio_path.with_suffix(".ogg")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(audio_path),
                    "-c:a", "libopus",
                    "-b:a", "64k",
                    "-ar", "48000",
                    str(ogg_path),
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            return ogg_path
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            logger.warning("ffmpeg conversion failed (%s). Sending WAV as fallback.", exc)
            return audio_path

    @staticmethod
    def wav_bytes_to_ogg_b64(wav_bytes: bytes) -> str:
        """Converte WAV bytes → OGG/OPUS → base64 string."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_f:
            wav_f.write(wav_bytes)
            wav_path = Path(wav_f.name)

        ogg_path = wav_path.with_suffix(".ogg")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(wav_path),
                    "-c:a", "libopus",
                    "-b:a", "64k",
                    "-ar", "48000",
                    str(ogg_path),
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            with open(ogg_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as exc:
            logger.error("WAV→OGG conversion failed: %s", exc)
            return base64.b64encode(wav_bytes).decode()
        finally:
            wav_path.unlink(missing_ok=True)
            ogg_path.unlink(missing_ok=True)
