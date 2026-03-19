import json
import logging

from fastapi.testclient import TestClient
from app import JSONFormatter, app


client = TestClient(app)


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_status_code(self):
        """Verify root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_is_json(self):
        """Verify root endpoint returns JSON content"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_has_service_section(self):
        """Verify response contains service information"""
        response = client.get("/")
        data = response.json()
        assert "service" in data
        assert isinstance(data["service"], dict)

    def test_root_service_fields(self):
        """Verify service section has required fields"""
        response = client.get("/")
        service = response.json()["service"]
        required_fields = ["name", "version", "description", "framework"]
        for field in required_fields:
            assert field in service, f"Missing field: {field}"
            assert isinstance(service[field], str)

    def test_root_service_name(self):
        """Verify service name is correct"""
        response = client.get("/")
        service = response.json()["service"]
        assert service["name"] == "devops-info-service"

    def test_root_service_framework(self):
        """Verify service uses FastAPI"""
        response = client.get("/")
        service = response.json()["service"]
        assert service["framework"] == "FastAPI"

    def test_root_has_system_section(self):
        """Verify response contains system information"""
        response = client.get("/")
        data = response.json()
        assert "system" in data
        assert isinstance(data["system"], dict)

    def test_root_system_fields(self):
        """Verify system section has required fields"""
        response = client.get("/")
        system = response.json()["system"]
        required_fields = [
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version",
        ]
        for field in required_fields:
            assert field in system, f"Missing field: {field}"

    def test_root_system_cpu_count_is_positive(self):
        """Verify CPU count is a positive integer"""
        response = client.get("/")
        system = response.json()["system"]
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

    def test_root_has_runtime_section(self):
        """Verify response contains runtime information"""
        response = client.get("/")
        data = response.json()
        assert "runtime" in data
        assert isinstance(data["runtime"], dict)

    def test_root_runtime_fields(self):
        """Verify runtime section has required fields"""
        response = client.get("/")
        runtime = response.json()["runtime"]
        required_fields = ["uptime_seconds", "uptime_human", "current_time", "timezone"]
        for field in required_fields:
            assert field in runtime, f"Missing field: {field}"

    def test_root_uptime_seconds_is_non_negative(self):
        """Verify uptime seconds is a non-negative integer"""
        response = client.get("/")
        runtime = response.json()["runtime"]
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0

    def test_root_has_request_section(self):
        """Verify response contains request information"""
        response = client.get("/")
        data = response.json()
        assert "request" in data
        assert isinstance(data["request"], dict)

    def test_root_request_fields(self):
        """Verify request section has required fields"""
        response = client.get("/")
        request_data = response.json()["request"]
        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in request_data, f"Missing field: {field}"

    def test_root_request_method_is_get(self):
        """Verify request method is correctly captured"""
        response = client.get("/")
        request_data = response.json()["request"]
        assert request_data["method"] == "GET"

    def test_root_request_path_is_root(self):
        """Verify request path is correctly captured"""
        response = client.get("/")
        request_data = response.json()["request"]
        assert request_data["path"] == "/"

    def test_root_has_endpoints_list(self):
        """Verify response includes list of available endpoints"""
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0

    def test_root_endpoints_have_required_fields(self):
        """Verify each endpoint entry has required fields"""
        response = client.get("/")
        endpoints = response.json()["endpoints"]
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""

    def test_health_status_code(self):
        """Verify health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_is_json(self):
        """Verify health endpoint returns JSON content"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_has_status_field(self):
        """Verify health response has status field"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_status_is_healthy(self):
        """Verify health status is 'healthy'"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self):
        """Verify health response has timestamp"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_health_has_uptime_seconds(self):
        """Verify health response has uptime seconds"""
        response = client.get("/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_required_fields(self):
        """Verify health endpoint has all required fields"""
        response = client.get("/health")
        data = response.json()
        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestMetricsEndpoint:
    """Tests for GET /metrics endpoint and custom metrics."""

    def test_metrics_status_code(self):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self):
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_contains_custom_metric_names(self):
        client.get("/")
        client.get("/health")

        response = client.get("/metrics")
        body = response.text

        assert "app_http_requests_total" in body
        assert "app_http_request_duration_seconds" in body
        assert "app_http_active_requests" in body
        assert "app_root_requests_total" in body
        assert "app_system_info_duration_seconds" in body
        assert "app_uptime_seconds" in body

    def test_metrics_contains_root_endpoint_labels(self):
        client.get("/")

        response = client.get("/metrics")
        assert 'app_http_requests_total{endpoint="/",method="GET",status_code="200"}' in response.text


class TestErrorHandling:
    """Tests for error handling"""

    def test_nonexistent_endpoint(self):
        """Verify 404 error for nonexistent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_error_response_is_html(self):
        """Verify error responses are HTML"""
        response = client.get("/nonexistent")
        # FastAPI returns 404 HTML by default
        assert response.status_code == 404


class TestMultipleRequests:
    """Tests for multiple sequential requests"""

    def test_uptime_increases(self):
        """Verify uptime increases between requests"""
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]

        # Make another request
        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]

        # Uptime should be equal or slightly greater
        assert uptime2 >= uptime1

    def test_root_and_health_consistency(self):
        """Verify consistency between root and health endpoints"""
        root_response = client.get("/")
        health_response = client.get("/health")

        root_data = root_response.json()
        health_data = health_response.json()

        # Both should have uptime (may differ slightly due to time)
        root_uptime = root_data["runtime"]["uptime_seconds"]
        health_uptime = health_data["uptime_seconds"]

        # Should be approximately equal (within 1 second)
        assert abs(root_uptime - health_uptime) <= 1


class TestLogging:
    """Tests for JSON logging formatter"""

    def test_json_formatter_outputs_required_fields(self):
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.method = "GET"
        record.path = "/"
        record.status_code = 200
        record.client_ip = "127.0.0.1"

        formatted = JSONFormatter().format(record)
        payload = json.loads(formatted)

        assert payload["level"] == "INFO"
        assert payload["logger"] == "test.logger"
        assert payload["message"] == "hello"
        assert payload["method"] == "GET"
        assert payload["path"] == "/"
        assert payload["status_code"] == 200
        assert payload["client_ip"] == "127.0.0.1"
        assert "timestamp" in payload
