"""Middleware de Mensajes y Abstraccion de Cola (Amazon SQS / Cola Local con DLQ).
Permite procesamiento asincrono, politica de reintentos (max 3) y canalizacion a Dead Letter Queue (DLQ).
"""
import os
import json
import time
import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QUEUE_DIR = os.path.join(BASE_DIR, "data", "queue")
INBOX_DIR = os.path.join(QUEUE_DIR, "inbox")
DLQ_DIR = os.path.join(QUEUE_DIR, "dlq")
PROCESSING_DIR = os.path.join(QUEUE_DIR, "processing")

for d in [INBOX_DIR, DLQ_DIR, PROCESSING_DIR]:
    os.makedirs(d, exist_ok=True)


class MessageQueue(ABC):
    @abstractmethod
    def send_message(self, payload: Dict[str, Any]) -> str:
        """Envia un mensaje a la cola principal."""
        pass

    @abstractmethod
    def receive_messages(self, max_messages: int = 10, visibility_timeout: int = 30) -> List[Dict[str, Any]]:
        """Recibe hasta max_messages de la cola."""
        pass

    @abstractmethod
    def delete_message(self, receipt_handle: str) -> bool:
        """Elimina un mensaje procesado con exito."""
        pass

    @abstractmethod
    def send_to_dlq(self, payload: Dict[str, Any], error_reason: str, receipt_handle: Optional[str] = None) -> str:
        """Mueve un mensaje fallido a la Dead Letter Queue tras agotar reintentos."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """Retorna conteos de mensajes en cola principal, procesando y DLQ."""
        pass


class LocalDiskQueue(MessageQueue):
    """Implementacion local persistente con semantica identica a Amazon SQS + DLQ."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def send_message(self, payload: Dict[str, Any]) -> str:
        message_id = str(uuid.uuid4())
        msg = {
            "message_id": message_id,
            "receipt_handle": message_id,
            "payload": payload,
            "created_at": time.time(),
            "attempts": 0,
            "visible_after": 0,
        }
        fpath = os.path.join(INBOX_DIR, f"{message_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(msg, f, indent=2)
        return message_id

    def receive_messages(self, max_messages: int = 10, visibility_timeout: int = 30) -> List[Dict[str, Any]]:
        now = time.time()
        received = []
        files = sorted(os.listdir(INBOX_DIR))

        for fname in files:
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(INBOX_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    msg = json.load(f)

                if msg.get("visible_after", 0) > now:
                    continue

                msg["attempts"] = msg.get("attempts", 0) + 1
                msg["visible_after"] = now + visibility_timeout

                # Si sobrepasa reintentos, mover a DLQ
                if msg["attempts"] > self.max_retries:
                    self.send_to_dlq(
                        payload=msg["payload"],
                        error_reason=f"Excedido el limite maximo de {self.max_retries} reintentos en worker.",
                        receipt_handle=fname.replace(".json", "")
                    )
                    continue

                # Guardar estado actualizado
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(msg, f, indent=2)

                received.append({
                    "MessageId": msg["message_id"],
                    "ReceiptHandle": msg["receipt_handle"],
                    "Body": json.dumps(msg["payload"]),
                    "Attempts": msg["attempts"],
                    "Payload": msg["payload"]
                })

                if len(received) >= max_messages:
                    break
            except Exception:
                continue

        return received

    def delete_message(self, receipt_handle: str) -> bool:
        fpath = os.path.join(INBOX_DIR, f"{receipt_handle}.json")
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                return True
            except OSError:
                return False
        return False

    def send_to_dlq(self, payload: Dict[str, Any], error_reason: str, receipt_handle: Optional[str] = None) -> str:
        dlq_id = str(uuid.uuid4())
        record = {
            "dlq_id": dlq_id,
            "original_receipt_handle": receipt_handle,
            "payload": payload,
            "error_reason": error_reason,
            "moved_at": time.time(),
        }
        fpath = os.path.join(DLQ_DIR, f"{dlq_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        # Eliminar de la cola principal si estaba ahi
        if receipt_handle:
            self.delete_message(receipt_handle)
        return dlq_id

    def get_stats(self) -> Dict[str, int]:
        inbox_count = len([f for f in os.listdir(INBOX_DIR) if f.endswith(".json")])
        dlq_count = len([f for f in os.listdir(DLQ_DIR) if f.endswith(".json")])
        return {
            "mensajes_en_cola": inbox_count,
            "mensajes_en_dlq": dlq_count,
            "backend": "LocalDiskQueue (Semantica SQS)",
        }


class AWSSQSQueue(MessageQueue):
    """Implementacion administrada en Amazon SQS con Dead Letter Queue (DLQ)."""

    def __init__(self, queue_url: str, dlq_url: Optional[str] = None, region: str = "us-east-1"):
        import boto3
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.client = boto3.client("sqs", region_name=region)

    def send_message(self, payload: Dict[str, Any]) -> str:
        resp = self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(payload),
        )
        return resp.get("MessageId", "")

    def receive_messages(self, max_messages: int = 10, visibility_timeout: int = 30) -> List[Dict[str, Any]]:
        resp = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            VisibilityTimeout=visibility_timeout,
            WaitTimeSeconds=2,
            AttributeNames=["ApproximateReceiveCount"]
        )
        messages = []
        for m in resp.get("Messages", []):
            attempts = int(m.get("Attributes", {}).get("ApproximateReceiveCount", 1))
            try:
                body_dict = json.loads(m.get("Body", "{}"))
            except json.JSONDecodeError:
                body_dict = {"raw": m.get("Body")}
            messages.append({
                "MessageId": m.get("MessageId"),
                "ReceiptHandle": m.get("ReceiptHandle"),
                "Body": m.get("Body"),
                "Attempts": attempts,
                "Payload": body_dict
            })
        return messages

    def delete_message(self, receipt_handle: str) -> bool:
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
            return True
        except Exception:
            return False

    def send_to_dlq(self, payload: Dict[str, Any], error_reason: str, receipt_handle: Optional[str] = None) -> str:
        if not self.dlq_url:
            return ""
        resp = self.client.send_message(
            QueueUrl=self.dlq_url,
            MessageBody=json.dumps({"payload": payload, "error": error_reason, "timestamp": time.time()}),
        )
        if receipt_handle:
            self.delete_message(receipt_handle)
        return resp.get("MessageId", "")

    def get_stats(self) -> Dict[str, int]:
        try:
            attrs = self.client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=["ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"]
            ).get("Attributes", {})
            return {
                "mensajes_en_cola": int(attrs.get("ApproximateNumberOfMessages", 0)),
                "mensajes_en_proceso": int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0)),
                "backend": "Amazon SQS",
            }
        except Exception:
            return {"mensajes_en_cola": -1, "backend": "Amazon SQS (Error de conexion)"}


def get_queue() -> MessageQueue:
    """Fabrica que retorna la instancia de cola configurada en el entorno."""
    sqs_url = os.getenv("AWS_SQS_QUEUE_URL", "").strip()
    dlq_url = os.getenv("AWS_SQS_DLQ_URL", "").strip()
    aws_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()

    if sqs_url and aws_key and aws_key != "TU_ACCESS_KEY_IAM_AQUI":
        try:
            return AWSSQSQueue(queue_url=sqs_url, dlq_url=dlq_url, region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        except Exception:
            pass
    return LocalDiskQueue()
