"""
RPC Testing ViewSet.

Provides REST API endpoints for testing RPC system with load testing capabilities.
"""

import time
import uuid
from threading import Thread

from django_cfg.modules.django_logging import get_logger
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ..serializers import (
    LoadTestRequestSerializer,
    LoadTestResponseSerializer,
    LoadTestStatusSerializer,
    TestRPCRequestSerializer,
    TestRPCResponseSerializer,
)

logger = get_logger("ipc.testing")

# Global load test state
_load_test_state = {
    'test_id': None,
    'running': False,
    'progress': 0,
    'total': 0,
    'success_count': 0,
    'failed_count': 0,
    'durations': [],
    'start_time': None,
}


class RPCTestingViewSet(viewsets.ViewSet):
    """
    ViewSet for RPC testing tools.

    Provides endpoints for:
    - Sending test RPC requests
    - Running load tests with concurrent requests
    - Monitoring load test progress
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = TestRPCRequestSerializer  # Default serializer for schema generation

    @extend_schema(
        tags=['IPC/RPC Testing'],
        summary="Send test RPC request",
        description="Send a single RPC request for testing purposes and measure response time.",
        request=TestRPCRequestSerializer,
        responses={
            200: TestRPCResponseSerializer,
            400: {"description": "Invalid parameters"},
            500: {"description": "RPC call failed"},
        },
    )
    @action(detail=False, methods=['post'], url_path='send')
    def test_send(self, request):
        """Send a test RPC request and return response with timing."""
        serializer = TestRPCRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        method = serializer.validated_data['method']
        params = serializer.validated_data['params']
        timeout = serializer.validated_data.get('timeout', 10)

        correlation_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            from django_cfg.apps.ipc import get_rpc_client

            rpc_client = get_rpc_client()
            result = rpc_client.call(
                method=method,
                params=params,
                timeout=timeout,
                user=request.user
            )

            duration_ms = (time.time() - start_time) * 1000

            response_data = {
                'success': True,
                'duration_ms': round(duration_ms, 2),
                'response': result,
                'error': None,
                'correlation_id': correlation_id,
            }

            return Response(response_data)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Test RPC call failed: {e}", exc_info=True)

            response_data = {
                'success': False,
                'duration_ms': round(duration_ms, 2),
                'response': None,
                'error': str(e),
                'correlation_id': correlation_id,
            }

            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=['IPC/RPC Testing'],
        summary="Start load test",
        description="Start a load test by sending multiple concurrent RPC requests.",
        request=LoadTestRequestSerializer,
        responses={
            200: LoadTestResponseSerializer,
            400: {"description": "Invalid parameters"},
            409: {"description": "Load test already running"},
        },
    )
    @action(detail=False, methods=['post'], url_path='load/start')
    def load_test_start(self, request):
        """Start a load test."""
        global _load_test_state

        if _load_test_state['running']:
            return Response(
                {'error': 'Load test already running'},
                status=status.HTTP_409_CONFLICT
            )

        serializer = LoadTestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_id = str(uuid.uuid4())[:8]
        method = serializer.validated_data['method']
        total_requests = serializer.validated_data['total_requests']
        concurrency = serializer.validated_data['concurrency']
        params = serializer.validated_data.get('params', {})

        # Reset state
        _load_test_state.update({
            'test_id': test_id,
            'running': True,
            'progress': 0,
            'total': total_requests,
            'success_count': 0,
            'failed_count': 0,
            'durations': [],
            'start_time': time.time(),
        })

        # Start load test in background
        def run_load_test():
            from django_cfg.apps.ipc import get_rpc_client

            try:
                rpc_client = get_rpc_client()

                def send_request(index):
                    try:
                        start = time.time()
                        rpc_client.call(
                            method=method,
                            params={**params, '_test_id': test_id, '_index': index},
                            timeout=10,
                            user=request.user
                        )
                        duration = (time.time() - start) * 1000

                        _load_test_state['success_count'] += 1
                        _load_test_state['durations'].append(duration)
                    except Exception as e:
                        logger.warning(f"Load test request {index} failed: {e}")
                        _load_test_state['failed_count'] += 1
                    finally:
                        _load_test_state['progress'] += 1

                # Send requests in batches based on concurrency
                for i in range(0, total_requests, concurrency):
                    if not _load_test_state['running']:
                        break

                    batch_size = min(concurrency, total_requests - i)
                    threads = []

                    for j in range(batch_size):
                        thread = Thread(target=send_request, args=(i + j,))
                        thread.start()
                        threads.append(thread)

                    for thread in threads:
                        thread.join()

            except Exception as e:
                logger.error(f"Load test failed: {e}", exc_info=True)
            finally:
                _load_test_state['running'] = False

        thread = Thread(target=run_load_test)
        thread.daemon = True
        thread.start()

        return Response({
            'test_id': test_id,
            'started': True,
            'message': f'Load test started with {total_requests} requests at {concurrency} concurrency'
        })

    @extend_schema(
        tags=['IPC/RPC Testing'],
        summary="Get load test status",
        description="Get current status of running or completed load test.",
        responses={
            200: LoadTestStatusSerializer,
        },
    )
    @action(detail=False, methods=['get'], url_path='load/status')
    def load_test_status(self, request):
        """Get status of current load test."""
        global _load_test_state

        elapsed_time = 0
        if _load_test_state['start_time']:
            elapsed_time = time.time() - _load_test_state['start_time']

        avg_duration = 0
        if _load_test_state['durations']:
            avg_duration = sum(_load_test_state['durations']) / len(_load_test_state['durations'])

        rps = 0
        if elapsed_time > 0:
            rps = _load_test_state['progress'] / elapsed_time

        response_data = {
            'test_id': _load_test_state['test_id'],
            'running': _load_test_state['running'],
            'progress': _load_test_state['progress'],
            'total': _load_test_state['total'],
            'success_count': _load_test_state['success_count'],
            'failed_count': _load_test_state['failed_count'],
            'avg_duration_ms': round(avg_duration, 2),
            'elapsed_time': round(elapsed_time, 2),
            'rps': round(rps, 2),
        }

        return Response(response_data)

    @extend_schema(
        tags=['IPC/RPC Testing'],
        summary="Stop load test",
        description="Stop currently running load test.",
        responses={
            200: {"description": "Load test stopped"},
            400: {"description": "No load test running"},
        },
    )
    @action(detail=False, methods=['post'], url_path='load/stop')
    def load_test_stop(self, request):
        """Stop current load test."""
        global _load_test_state

        if not _load_test_state['running']:
            return Response(
                {'message': 'No load test currently running'},
                status=status.HTTP_400_BAD_REQUEST
            )

        _load_test_state['running'] = False

        return Response({
            'message': 'Load test stopped',
            'progress': _load_test_state['progress'],
            'total': _load_test_state['total']
        })
