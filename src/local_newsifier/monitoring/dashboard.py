"""Simple metrics dashboard generator."""

from datetime import datetime
from typing import Any, Dict, List

from prometheus_client import REGISTRY, generate_latest
from prometheus_client.parser import text_string_to_metric_families

from .metrics import update_app_info, update_system_metrics


class MetricsDashboard:
    """Generate dashboard data from Prometheus metrics."""

    def __init__(self):
        """Initialize dashboard."""
        self.registry = REGISTRY

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        # Update system metrics before collecting
        update_system_metrics()
        update_app_info()

        # Parse metrics
        metrics_text = generate_latest(self.registry).decode("utf-8")
        metrics = list(text_string_to_metric_families(metrics_text))

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "api": self._get_api_metrics(metrics),
            "database": self._get_database_metrics(metrics),
            "celery": self._get_celery_metrics(metrics),
            "system": self._get_system_metrics(metrics),
            "entities": self._get_entity_metrics(metrics),
        }

        return summary

    def _get_api_metrics(self, metrics: List[Any]) -> Dict[str, Any]:
        """Extract API-related metrics."""
        api_metrics = {
            "total_requests": 0,
            "active_requests": 0,
            "average_duration": 0,
            "requests_by_endpoint": {},
            "errors_by_endpoint": {},
        }

        for metric in metrics:
            if metric.name == "newsifier_api_requests_total":
                for sample in metric.samples:
                    if sample.name == "newsifier_api_requests_total":
                        api_metrics["total_requests"] += sample.value
                        endpoint = sample.labels.get("endpoint", "unknown")
                        status = sample.labels.get("status_code", "unknown")

                        if endpoint not in api_metrics["requests_by_endpoint"]:
                            api_metrics["requests_by_endpoint"][endpoint] = 0
                        api_metrics["requests_by_endpoint"][endpoint] += sample.value

                        if int(status) >= 400:
                            if endpoint not in api_metrics["errors_by_endpoint"]:
                                api_metrics["errors_by_endpoint"][endpoint] = 0
                            api_metrics["errors_by_endpoint"][endpoint] += sample.value

            elif metric.name == "newsifier_api_active_requests":
                for sample in metric.samples:
                    if sample.name == "newsifier_api_active_requests":
                        api_metrics["active_requests"] += sample.value

            elif metric.name == "newsifier_api_request_duration_seconds":
                total_time = 0
                count = 0
                for sample in metric.samples:
                    if sample.name == "newsifier_api_request_duration_seconds_sum":
                        total_time += sample.value
                    elif sample.name == "newsifier_api_request_duration_seconds_count":
                        count += sample.value

                if count > 0:
                    api_metrics["average_duration"] = total_time / count

        return api_metrics

    def _get_database_metrics(self, metrics: List[Any]) -> Dict[str, Any]:
        """Extract database-related metrics."""
        db_metrics = {
            "total_queries": 0,
            "slow_queries": 0,
            "average_query_time": 0,
            "queries_by_operation": {},
            "connection_pool_size": 0,
        }

        for metric in metrics:
            if metric.name == "newsifier_db_queries_total":
                for sample in metric.samples:
                    if sample.name == "newsifier_db_queries_total":
                        db_metrics["total_queries"] += sample.value
                        operation = sample.labels.get("operation", "unknown")

                        if operation not in db_metrics["queries_by_operation"]:
                            db_metrics["queries_by_operation"][operation] = 0
                        db_metrics["queries_by_operation"][operation] += sample.value

            elif metric.name == "newsifier_db_slow_queries_total":
                for sample in metric.samples:
                    if sample.name == "newsifier_db_slow_queries_total":
                        db_metrics["slow_queries"] += sample.value

            elif metric.name == "newsifier_db_query_duration_seconds":
                total_time = 0
                count = 0
                for sample in metric.samples:
                    if sample.name == "newsifier_db_query_duration_seconds_sum":
                        total_time += sample.value
                    elif sample.name == "newsifier_db_query_duration_seconds_count":
                        count += sample.value

                if count > 0:
                    db_metrics["average_query_time"] = total_time / count

            elif metric.name == "newsifier_db_connection_pool_size":
                for sample in metric.samples:
                    if sample.name == "newsifier_db_connection_pool_size":
                        db_metrics["connection_pool_size"] = max(
                            db_metrics["connection_pool_size"], sample.value
                        )

        return db_metrics

    def _get_celery_metrics(self, metrics: List[Any]) -> Dict[str, Any]:
        """Extract Celery-related metrics."""
        celery_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_task_duration": 0,
            "tasks_by_name": {},
            "queue_lengths": {},
        }

        for metric in metrics:
            if metric.name == "newsifier_celery_tasks_total":
                for sample in metric.samples:
                    if sample.name == "newsifier_celery_tasks_total":
                        status = sample.labels.get("status", "unknown")
                        task_name = sample.labels.get("task_name", "unknown")

                        if status == "success":
                            celery_metrics["successful_tasks"] += sample.value
                        elif status == "failure":
                            celery_metrics["failed_tasks"] += sample.value

                        if status in ["success", "failure"]:
                            celery_metrics["total_tasks"] += sample.value

                            if task_name not in celery_metrics["tasks_by_name"]:
                                celery_metrics["tasks_by_name"][task_name] = {
                                    "total": 0,
                                    "success": 0,
                                    "failure": 0,
                                }

                            celery_metrics["tasks_by_name"][task_name]["total"] += sample.value
                            if status == "success":
                                celery_metrics["tasks_by_name"][task_name][
                                    "success"
                                ] += sample.value
                            elif status == "failure":
                                celery_metrics["tasks_by_name"][task_name][
                                    "failure"
                                ] += sample.value

            elif metric.name == "newsifier_celery_task_duration_seconds":
                total_time = 0
                count = 0
                for sample in metric.samples:
                    if sample.name == "newsifier_celery_task_duration_seconds_sum":
                        total_time += sample.value
                    elif sample.name == "newsifier_celery_task_duration_seconds_count":
                        count += sample.value

                if count > 0:
                    celery_metrics["average_task_duration"] = total_time / count

            elif metric.name == "newsifier_celery_queue_length":
                for sample in metric.samples:
                    if sample.name == "newsifier_celery_queue_length":
                        queue_name = sample.labels.get("queue_name", "default")
                        celery_metrics["queue_lengths"][queue_name] = sample.value

        return celery_metrics

    def _get_system_metrics(self, metrics: List[Any]) -> Dict[str, Any]:
        """Extract system-related metrics."""
        system_metrics = {
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "app_info": {},
        }

        for metric in metrics:
            if metric.name == "newsifier_system_memory_usage_bytes":
                for sample in metric.samples:
                    if sample.name == "newsifier_system_memory_usage_bytes":
                        system_metrics["memory_usage_mb"] = sample.value / (1024 * 1024)

            elif metric.name == "newsifier_system_cpu_usage_percent":
                for sample in metric.samples:
                    if sample.name == "newsifier_system_cpu_usage_percent":
                        system_metrics["cpu_usage_percent"] = sample.value

            elif metric.name == "newsifier_app_info":
                for sample in metric.samples:
                    if sample.name == "newsifier_app_info":
                        system_metrics["app_info"] = sample.labels

        return system_metrics

    def _get_entity_metrics(self, metrics: List[Any]) -> Dict[str, Any]:
        """Extract entity processing metrics."""
        entity_metrics = {
            "total_entities_extracted": 0,
            "entities_by_type": {},
            "average_extraction_time": 0,
        }

        for metric in metrics:
            if metric.name == "newsifier_entities_extracted_total":
                for sample in metric.samples:
                    if sample.name == "newsifier_entities_extracted_total":
                        entity_metrics["total_entities_extracted"] += sample.value
                        entity_type = sample.labels.get("entity_type", "unknown")

                        if entity_type not in entity_metrics["entities_by_type"]:
                            entity_metrics["entities_by_type"][entity_type] = 0
                        entity_metrics["entities_by_type"][entity_type] += sample.value

            elif metric.name == "newsifier_entity_extraction_duration_seconds":
                total_time = 0
                count = 0
                for sample in metric.samples:
                    if sample.name == "newsifier_entity_extraction_duration_seconds_sum":
                        total_time += sample.value
                    elif sample.name == "newsifier_entity_extraction_duration_seconds_count":
                        count += sample.value

                if count > 0:
                    entity_metrics["average_extraction_time"] = total_time / count

        return entity_metrics

    def get_performance_baseline(self) -> Dict[str, Any]:
        """Get performance baseline metrics."""
        summary = self.get_metrics_summary()

        baseline = {
            "timestamp": summary["timestamp"],
            "api": {
                "avg_response_time": summary["api"]["average_duration"],
                "requests_per_minute": self._calculate_rpm(summary["api"]["total_requests"]),
            },
            "database": {
                "avg_query_time": summary["database"]["average_query_time"],
                "slow_query_threshold": 1.0,  # 1 second
                "slow_query_count": summary["database"]["slow_queries"],
            },
            "celery": {
                "avg_task_duration": summary["celery"]["average_task_duration"],
                "success_rate": self._calculate_success_rate(
                    summary["celery"]["successful_tasks"], summary["celery"]["total_tasks"]
                ),
            },
            "system": {
                "memory_usage_mb": summary["system"]["memory_usage_mb"],
                "cpu_usage_percent": summary["system"]["cpu_usage_percent"],
            },
        }

        return baseline

    def _calculate_rpm(self, total_requests: float) -> float:
        """Calculate requests per minute (rough estimate)."""
        # This is a simple calculation - in production you'd want
        # to track this over a specific time window
        return total_requests  # Placeholder

    def _calculate_success_rate(self, successful: float, total: float) -> float:
        """Calculate success rate percentage."""
        if total == 0:
            return 100.0
        return (successful / total) * 100.0
