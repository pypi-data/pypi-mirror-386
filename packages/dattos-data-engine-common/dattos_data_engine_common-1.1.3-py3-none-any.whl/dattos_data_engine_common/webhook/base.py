from abc import ABC, abstractmethod
import asyncio

import structlog

from dattos_data_engine_common.webhook.models import BaseAsyncRequest
from dattos_data_engine_common.webhook.utils import send_webhook_notification

logger = structlog.stdlib.get_logger()


class BaseWebhookService(ABC):
    async def process_async(self, request: BaseAsyncRequest, **kwargs):
        heartbeat_task = None
        try:
            if request.heartbeat_check_seconds_interval:
                # Inicia o heartbeat em paralelo
                heartbeat_task = asyncio.create_task(
                    self._heartbeat_loop(
                        request.webhook_uri,
                        request.webhook_token,
                        request.request_id,
                        interval=request.heartbeat_check_seconds_interval,
                    )
                )

            # Executa o processamento principal
            result_data = await self.execute(request, **kwargs)

            # Envia notificação de sucesso
            await self.send_success_notification(
                request.webhook_uri,
                request.webhook_token,
                request.request_id,
                data=result_data,
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            # Notificação de falha
            await self.send_failure_notification(
                request.webhook_uri,
                request.webhook_token,
                request.request_id,
                error_message=str(e),
            )
        finally:
            # Cancela o heartbeat se ainda estiver rodando
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    async def _heartbeat_loop(
        self, webhook_uri, webhook_token, request_id, interval=10
    ):
        """
        Loop que envia check_notification periodicamente durante o processamento.
        """
        try:
            while True:
                await asyncio.sleep(interval)
                await self.send_check_notification(
                    webhook_uri, webhook_token, request_id=request_id
                )
        except asyncio.CancelledError:
            # Pode ser usado para enviar um 'heartbeat stopped', se quiser
            pass

    async def send_success_notification(
        self, webhook_uri, webhook_token, request_id, data
    ):
        await send_webhook_notification(
            webhook_uri,
            webhook_token,
            request_id,
            success=True,
            heartbeat_check=False,
            data=data,
        )

    async def send_failure_notification(
        self, webhook_uri, webhook_token, request_id, error_message
    ):
        await send_webhook_notification(
            webhook_uri,
            webhook_token,
            request_id,
            success=False,
            heartbeat_check=False,
            data={"message": error_message},
        )

    async def send_check_notification(self, webhook_uri, webhook_token, request_id):
        await send_webhook_notification(
            webhook_uri,
            webhook_token,
            request_id,
            success=True,
            heartbeat_check=True,
            data=None,
        )

    @abstractmethod
    async def execute(self, request: BaseAsyncRequest, **kwargs):
        """Hook method to be implemented by subclasses."""
        pass
