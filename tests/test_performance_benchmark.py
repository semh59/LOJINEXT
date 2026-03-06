"""
Performance Benchmark Tests

Measures and validates performance characteristics:
- API response times
- Database query performance
- Memory usage patterns
- Throughput under load

Run with: pytest tests/test_performance_benchmark.py -v
"""

import pytest
import asyncio
import time
import statistics
from datetime import date, timedelta
from typing import List, Tuple
from httpx import AsyncClient, ASGITransport

from app.main import app


class PerformanceMetrics:
    """Collects and analyzes performance metrics."""

    def __init__(self):
        self.response_times: List[float] = []
        self.errors: int = 0

    def record(self, duration: float, success: bool = True):
        """Record a measurement."""
        self.response_times.append(duration)
        if not success:
            self.errors += 1

    @property
    def avg_ms(self) -> float:
        """Average response time in milliseconds."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times) * 1000

    @property
    def p95_ms(self) -> float:
        """95th percentile response time in milliseconds."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)] * 1000

    @property
    def p99_ms(self) -> float:
        """99th percentile response time in milliseconds."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)] * 1000

    @property
    def min_ms(self) -> float:
        """Minimum response time in milliseconds."""
        return min(self.response_times) * 1000 if self.response_times else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum response time in milliseconds."""
        return max(self.response_times) * 1000 if self.response_times else 0.0

    @property
    def error_rate(self) -> float:
        """Error rate as percentage."""
        if not self.response_times:
            return 0.0
        return (self.errors / len(self.response_times)) * 100

    def summary(self) -> dict:
        """Return metrics summary."""
        return {
            "count": len(self.response_times),
            "avg_ms": round(self.avg_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "error_rate": round(self.error_rate, 2),
        }


# ============================================
# Performance Thresholds (SLA)
# ============================================

THRESHOLDS = {
    "list_vehicles": {"avg_ms": 500, "p95_ms": 1000},
    "list_drivers": {"avg_ms": 500, "p95_ms": 1000},
    "list_trips": {"avg_ms": 1000, "p95_ms": 2000},
    "list_fuel": {"avg_ms": 500, "p95_ms": 1000},
    "dashboard": {"avg_ms": 2000, "p95_ms": 5000},
    "fuel_stats": {"avg_ms": 1000, "p95_ms": 2000},
}


# ============================================
# Benchmark Tests
# ============================================


class TestAPIPerformance:
    """API endpoint performance benchmarks."""

    @pytest.fixture
    async def client(self):
        """Create test client with auth."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Login
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "skara", "password": "!23efe25ali!"},
            )
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                client.headers["Authorization"] = f"Bearer {token}"
            yield client

    async def _benchmark_endpoint(
        self, client: AsyncClient, method: str, url: str, iterations: int = 10, **kwargs
    ) -> PerformanceMetrics:
        """Run benchmark for an endpoint."""
        metrics = PerformanceMetrics()

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                if method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                elif method.upper() == "POST":
                    response = await client.post(url, **kwargs)
                else:
                    response = await client.request(method, url, **kwargs)

                duration = time.perf_counter() - start
                metrics.record(duration, response.status_code < 400)
            except Exception:
                duration = time.perf_counter() - start
                metrics.record(duration, success=False)

        return metrics

    @pytest.mark.asyncio
    async def test_list_vehicles_performance(self, client):
        """Benchmark GET /vehicles/ endpoint."""
        metrics = await self._benchmark_endpoint(
            client, "GET", "/api/v1/vehicles/", iterations=20
        )

        summary = metrics.summary()
        print(f"\nVehicles List Performance: {summary}")

        threshold = THRESHOLDS["list_vehicles"]
        assert metrics.avg_ms < threshold["avg_ms"], (
            f"Avg response time {metrics.avg_ms}ms exceeds threshold {threshold['avg_ms']}ms"
        )
        assert metrics.p95_ms < threshold["p95_ms"], (
            f"P95 response time {metrics.p95_ms}ms exceeds threshold {threshold['p95_ms']}ms"
        )

    @pytest.mark.asyncio
    async def test_list_drivers_performance(self, client):
        """Benchmark GET /drivers/ endpoint."""
        metrics = await self._benchmark_endpoint(
            client, "GET", "/api/v1/drivers/", iterations=20
        )

        summary = metrics.summary()
        print(f"\nDrivers List Performance: {summary}")

        threshold = THRESHOLDS["list_drivers"]
        assert metrics.avg_ms < threshold["avg_ms"]
        assert metrics.p95_ms < threshold["p95_ms"]

    @pytest.mark.asyncio
    async def test_list_trips_performance(self, client):
        """Benchmark GET /trips/ endpoint."""
        metrics = await self._benchmark_endpoint(
            client, "GET", "/api/v1/trips/", iterations=20
        )

        summary = metrics.summary()
        print(f"\nTrips List Performance: {summary}")

        threshold = THRESHOLDS["list_trips"]
        assert metrics.avg_ms < threshold["avg_ms"]
        assert metrics.p95_ms < threshold["p95_ms"]

    @pytest.mark.asyncio
    async def test_fuel_list_performance(self, client):
        """Benchmark GET /fuel/ endpoint."""
        metrics = await self._benchmark_endpoint(
            client, "GET", "/api/v1/fuel/", iterations=20
        )

        summary = metrics.summary()
        print(f"\nFuel List Performance: {summary}")

        threshold = THRESHOLDS["list_fuel"]
        assert metrics.avg_ms < threshold["avg_ms"]
        assert metrics.p95_ms < threshold["p95_ms"]

    @pytest.mark.asyncio
    async def test_dashboard_performance(self, client):
        """Benchmark GET /reports/dashboard endpoint."""
        metrics = await self._benchmark_endpoint(
            client, "GET", "/api/v1/reports/dashboard", iterations=10
        )

        summary = metrics.summary()
        print(f"\nDashboard Performance: {summary}")

        threshold = THRESHOLDS["dashboard"]
        assert metrics.avg_ms < threshold["avg_ms"]
        assert metrics.p95_ms < threshold["p95_ms"]

    @pytest.mark.asyncio
    async def test_fuel_stats_performance(self, client):
        """Benchmark GET /fuel/stats endpoint."""
        metrics = await self._benchmark_endpoint(
            client, "GET", "/api/v1/fuel/stats", iterations=20
        )

        summary = metrics.summary()
        print(f"\nFuel Stats Performance: {summary}")

        threshold = THRESHOLDS["fuel_stats"]
        assert metrics.avg_ms < threshold["avg_ms"]
        assert metrics.p95_ms < threshold["p95_ms"]


class TestConcurrencyPerformance:
    """Tests for concurrent request handling."""

    @pytest.fixture
    async def client(self):
        """Create test client with auth."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "skara", "password": "!23efe25ali!"},
            )
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_concurrent_vehicle_requests(self, client):
        """Test handling 10 concurrent vehicle list requests."""

        async def fetch_vehicles():
            start = time.perf_counter()
            response = await client.get("/api/v1/vehicles/")
            duration = time.perf_counter() - start
            return (response.status_code, duration)

        # Run 10 concurrent requests
        tasks = [fetch_vehicles() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        status_codes = [r[0] for r in results]
        durations = [r[1] for r in results]

        success_rate = sum(1 for s in status_codes if s == 200) / len(status_codes)
        avg_duration = statistics.mean(durations) * 1000

        print(f"\nConcurrent Vehicles: {len(results)} requests")
        print(f"Success Rate: {success_rate * 100}%")
        print(f"Avg Duration: {avg_duration:.2f}ms")

        assert success_rate >= 0.9, f"Success rate {success_rate} below 90%"
        assert avg_duration < 2000, f"Avg duration {avg_duration}ms exceeds 2000ms"

    @pytest.mark.asyncio
    async def test_mixed_concurrent_requests(self, client):
        """Test handling mixed concurrent requests."""

        async def fetch_endpoint(url: str) -> Tuple[str, int, float]:
            start = time.perf_counter()
            response = await client.get(url)
            duration = time.perf_counter() - start
            return (url, response.status_code, duration)

        endpoints = [
            "/api/v1/vehicles/",
            "/api/v1/drivers/",
            "/api/v1/trips/",
            "/api/v1/fuel/",
            "/api/v1/reports/dashboard",
        ]

        # Run all endpoints 2 times each concurrently
        tasks = []
        for endpoint in endpoints:
            tasks.extend([fetch_endpoint(endpoint) for _ in range(2)])

        results = await asyncio.gather(*tasks)

        # Analyze results by endpoint
        by_endpoint = {}
        for url, status, duration in results:
            if url not in by_endpoint:
                by_endpoint[url] = {"success": 0, "fail": 0, "durations": []}
            if status == 200:
                by_endpoint[url]["success"] += 1
            else:
                by_endpoint[url]["fail"] += 1
            by_endpoint[url]["durations"].append(duration)

        print("\nMixed Concurrent Requests Results:")
        for url, data in by_endpoint.items():
            avg_ms = statistics.mean(data["durations"]) * 1000
            print(
                f"  {url}: {data['success']}/{data['success'] + data['fail']} success, avg {avg_ms:.2f}ms"
            )

        # Total success rate should be high
        total = len(results)
        successes = sum(1 for _, s, _ in results if s == 200)
        assert successes / total >= 0.8, "Overall success rate below 80%"


class TestDatabaseQueryPerformance:
    """Tests for database query performance."""

    @pytest.mark.asyncio
    async def test_auth_performance(self, async_client):
        """Authentication performans testi."""
        durations = []
        for _ in range(5):
            start = time.time()
            await async_client.post(
                "/api/v1/auth/token",
                data={"username": "admin", "password": "admin_password"},
            )
            durations.append(time.time() - start)

    @pytest.mark.asyncio
    async def test_filtered_trip_query_performance(self):
        """Test performance of filtered trip queries."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Login
            login = await client.post(
                "/api/v1/auth/token",
                data={"username": "skara", "password": "!23efe25ali!"},
            )
            if login.status_code == 200:
                client.headers["Authorization"] = (
                    f"Bearer {login.json()['access_token']}"
                )

            # Test date range filter
            start_date = (date.today() - timedelta(days=30)).isoformat()
            end_date = date.today().isoformat()

            metrics = PerformanceMetrics()

            for _ in range(10):
                start = time.perf_counter()
                response = await client.get(
                    f"/api/v1/trips/?baslangic_tarih={start_date}&bitis_tarih={end_date}"
                )
                duration = time.perf_counter() - start
                metrics.record(duration, response.status_code == 200)

            print(f"\nFiltered Trip Query Performance: {metrics.summary()}")

            assert metrics.avg_ms < 2000, "Filtered trip query too slow"
