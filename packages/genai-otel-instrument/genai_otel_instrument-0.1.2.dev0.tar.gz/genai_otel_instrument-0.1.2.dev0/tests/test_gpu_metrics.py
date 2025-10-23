import sys
import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# Skip all GPU tests if nvidia-ml-py is not installed
pytest.importorskip("pynvml", reason="nvidia-ml-py (pynvml) not installed")


# Configure pytest
def pytest_configure(config):
    # No global module-level mocks here. Use patch in fixtures/tests instead.
    pass


# Common fixtures


@pytest.fixture
def mock_otel_config():
    """Fixture for a mock OTelConfig."""
    config = Mock()
    config.enable_co2_tracking = True
    config.carbon_intensity = 0.4  # gCO2e/kWh
    return config


@pytest.fixture
def mock_meter():
    """Fixture for a mock OpenTelemetry Meter."""
    meter = Mock()
    meter.create_counter.return_value = Mock()  # Only CO2 counter now
    # Return a new Mock() each time create_observable_gauge is called
    meter.create_observable_gauge.return_value = Mock()
    return meter


@pytest.fixture
def mock_pynvml_gpu_available():
    """Fixture to mock pynvml when GPUs are available."""
    with patch("genai_otel.gpu_metrics.pynvml") as mock_pynvml:
        import genai_otel.gpu_metrics

        genai_otel.gpu_metrics.NVML_AVAILABLE = True
        mock_pynvml.nvmlInit.return_value = None
        mock_pynvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = Mock()
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = b"NVIDIA GeForce RTX 3080"
        mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = Mock(gpu=50, memory=60)
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = Mock(
            total=10000000000, used=5000000000, free=5000000000
        )  # Bytes
        mock_pynvml.nvmlDeviceGetTemperature.return_value = 65
        mock_pynvml.NVML_TEMPERATURE_GPU = 0  # Mock constant
        mock_pynvml.nvmlDeviceGetPowerUsage.return_value = 150000  # mW
        mock_pynvml.nvmlShutdown.return_value = None
        yield mock_pynvml


@pytest.fixture
def mock_pynvml_no_gpu():
    """Fixture to mock pynvml when no GPUs are available."""
    with patch("genai_otel.gpu_metrics.pynvml") as mock_pynvml:
        import genai_otel.gpu_metrics

        genai_otel.gpu_metrics.NVML_AVAILABLE = True
        mock_pynvml.nvmlInit.return_value = None
        mock_pynvml.nvmlDeviceGetCount.return_value = 0
        mock_pynvml.nvmlShutdown.return_value = None
        yield mock_pynvml


class TestGPUMetricsCollector:
    @patch("genai_otel.gpu_metrics.logger")
    @patch.dict(sys.modules, {"pynvml": None})
    @patch("genai_otel.gpu_metrics.NVML_AVAILABLE", False)
    def test_init_nvml_not_available(self, mock_logger, mock_meter, mock_otel_config):
        import genai_otel.gpu_metrics

        # NVML_AVAILABLE is already False due to patch
        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert not collector.gpu_available
        mock_logger.warning.assert_called_with(
            "GPU metrics collection not available - nvidia-ml-py not installed. "
            "Install with: pip install genai-otel-instrument[gpu]"
        )
        mock_meter.create_counter.assert_called_once()  # co2 counter is always created
        mock_meter.create_observable_gauge.assert_not_called()  # other gauges not created

    @patch("genai_otel.gpu_metrics.logger")
    def test_init_nvml_init_fails(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        mock_pynvml_gpu_available.nvmlInit.side_effect = Exception("NVML init failed")
        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert not collector.gpu_available
        # Only CO2 counter is created (before GPU availability check)
        mock_meter.create_counter.assert_called_once_with(
            "gen_ai.co2.emissions",  # Fixed metric name
            description="Cumulative CO2 equivalent emissions in grams",
            unit="gCO2e",
        )
        # GPU gauges are created even if no GPUs available
        assert mock_meter.create_observable_gauge.call_count == 4

    @patch("genai_otel.gpu_metrics.logger")
    def test_init_no_gpus(self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_no_gpu):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert not collector.gpu_available
        assert collector.device_count == 0
        mock_pynvml_no_gpu.nvmlInit.assert_called_once()
        mock_pynvml_no_gpu.nvmlDeviceGetCount.assert_called_once()
        mock_logger.warning.assert_not_called()  # No warning if NVML is available but no GPUs

    @patch("genai_otel.gpu_metrics.logger")
    def test_init_with_gpus(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert collector.gpu_available
        assert collector.device_count == 1
        mock_pynvml_gpu_available.nvmlInit.assert_called_once()
        # Only CO2 counter is created
        mock_meter.create_counter.assert_called_once_with(
            "gen_ai.co2.emissions",  # Fixed metric name
            description="Cumulative CO2 equivalent emissions in grams",
            unit="gCO2e",
        )
        # All four metrics are now ObservableGauges
        assert (
            mock_meter.create_observable_gauge.call_count == 4
        )  # utilization, memory, temperature, power

    @patch("genai_otel.gpu_metrics.logger")
    def test_init_metric_instrument_creation_fails(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        # Make create_observable_gauge fail
        mock_meter.create_observable_gauge.side_effect = StopIteration()
        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert collector.gpu_available
        mock_logger.error.assert_called_with(
            "Failed to create GPU metrics instruments: %s",
            mock_meter.create_observable_gauge.side_effect,
            exc_info=True,
        )

    @patch("genai_otel.gpu_metrics.logger")
    @patch.dict(sys.modules, {"pynvml": None})
    @patch("genai_otel.gpu_metrics.NVML_AVAILABLE", False)
    def test_observe_gpu_utilization_nvml_not_available(
        self, mock_logger, mock_meter, mock_otel_config
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        # ObservableGauge callbacks return generators, should return empty if NVML not available
        observations = list(collector._observe_gpu_utilization(None))
        assert observations == []

    @patch("genai_otel.gpu_metrics.logger")
    def test_observe_gpu_utilization_nvml_init_fails(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        # Reset and make nvmlInit fail in callback
        mock_pynvml_gpu_available.nvmlInit.reset_mock()
        mock_pynvml_gpu_available.nvmlInit.side_effect = Exception(
            "NVML init failed during observe"
        )

        observations = list(collector._observe_gpu_utilization(None))
        assert observations == []
        mock_logger.error.assert_called_with(
            "Error observing GPU utilization: %s", mock_pynvml_gpu_available.nvmlInit.side_effect
        )

    @patch("genai_otel.gpu_metrics.logger")
    def test_observe_gpu_utilization_successful(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        from opentelemetry.metrics import Observation

        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        # Reset mocks from init
        mock_pynvml_gpu_available.nvmlInit.reset_mock()
        mock_pynvml_gpu_available.nvmlDeviceGetCount.reset_mock()

        observations = list(collector._observe_gpu_utilization(None))

        assert len(observations) == 1
        assert isinstance(observations[0], Observation)
        assert observations[0].value == 50
        assert observations[0].attributes == {"gpu_id": "0", "gpu_name": "NVIDIA GeForce RTX 3080"}

        mock_pynvml_gpu_available.nvmlInit.assert_called_once()
        mock_pynvml_gpu_available.nvmlShutdown.assert_called_once()

    @patch("genai_otel.gpu_metrics.logger")
    def test_observe_gpu_metrics_partial_failures(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        from opentelemetry.metrics import Observation

        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)

        # Reset mocks from init
        mock_pynvml_gpu_available.nvmlInit.reset_mock()
        mock_pynvml_gpu_available.nvmlDeviceGetCount.reset_mock()

        # Mock memory info to fail
        mock_pynvml_gpu_available.nvmlDeviceGetMemoryInfo.side_effect = Exception("Memory error")

        observations = list(collector._observe_gpu_memory(None))

        # Should get no observations but no crash
        assert observations == []
        mock_logger.debug.assert_called_with(
            "Failed to get GPU memory for GPU %d: %s",
            0,
            mock_pynvml_gpu_available.nvmlDeviceGetMemoryInfo.side_effect,
        )

    @patch("genai_otel.gpu_metrics.logger")
    def test_observe_gpu_power_successful(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        from opentelemetry.metrics import Observation

        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        # Reset mocks from init
        mock_pynvml_gpu_available.nvmlInit.reset_mock()
        mock_pynvml_gpu_available.nvmlDeviceGetCount.reset_mock()

        observations = list(collector._observe_gpu_power(None))

        assert len(observations) == 1
        assert isinstance(observations[0], Observation)
        # Power usage is 150000 mW = 150 W
        assert observations[0].value == 150.0
        assert observations[0].attributes == {"gpu_id": "0", "gpu_name": "NVIDIA GeForce RTX 3080"}

        mock_pynvml_gpu_available.nvmlInit.assert_called_once()
        mock_pynvml_gpu_available.nvmlShutdown.assert_called_once()

    @patch("genai_otel.gpu_metrics.threading.Thread")
    @patch("genai_otel.gpu_metrics.logger")
    @patch.dict(sys.modules, {"pynvml": None})
    @patch("genai_otel.gpu_metrics.NVML_AVAILABLE", False)
    def test_start_nvml_not_available(self, mock_logger, mock_thread, mock_meter, mock_otel_config):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        collector.start()
        mock_logger.warning.assert_any_call(
            "Cannot start GPU metrics collection - nvidia-ml-py not available"
        )
        mock_thread.assert_not_called()

    @patch("genai_otel.gpu_metrics.threading.Thread")
    @patch("genai_otel.gpu_metrics.logger")
    def test_start_gpu_not_available(
        self, mock_logger, mock_thread, mock_meter, mock_otel_config, mock_pynvml_no_gpu
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert not collector.gpu_available  # From mock_pynvml_no_gpu
        collector.start()
        mock_logger.info.assert_not_called()
        mock_thread.assert_not_called()

    @patch("genai_otel.gpu_metrics.threading.Thread")
    @patch("genai_otel.gpu_metrics.logger")
    def test_start_metrics_not_initialized(
        self, mock_logger, mock_thread, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        # With new implementation, start() always works - ObservableGauges handle collection
        collector.start()
        # Only CO2 collection thread is started
        mock_thread.assert_called_once_with(target=collector._collect_loop, daemon=True)
        mock_thread.return_value.start.assert_called_once()

    @patch("genai_otel.gpu_metrics.threading.Thread")
    @patch("genai_otel.gpu_metrics.logger")
    def test_start_successful(
        self, mock_logger, mock_thread, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        collector.start()
        # Only CO2 collection thread started (no more _run thread)
        mock_thread.assert_called_once_with(target=collector._collect_loop, daemon=True)
        mock_thread.return_value.start.assert_called_once()
        mock_logger.info.assert_called_with("Starting GPU metrics collection (CO2 tracking)")

    @patch("genai_otel.gpu_metrics.time.time", return_value=1000.0)
    @patch("genai_otel.gpu_metrics.logger")
    def test_collect_loop_co2_enabled(
        self, mock_logger, mock_time, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        collector.device_count = 1
        collector.last_timestamp = [990.0]  # 10 seconds ago
        collector.interval = 1  # Short interval for testing

        # Mock _stop_event.wait to return True after one iteration
        collector._stop_event.wait = Mock(side_effect=[False, True])

        collector._collect_loop()

        mock_pynvml_gpu_available.nvmlDeviceGetPowerUsage.assert_called_once_with(
            mock_pynvml_gpu_available.nvmlDeviceGetHandleByIndex.return_value
        )
        # Power usage is 150W (150000 mW)
        # delta_time_hours = (1000 - 990) / 3600 = 10 / 3600 hours
        # delta_energy_wh = (150 / 1000) * (10 / 3600 * 3600) = 0.15 * 10 = 1.5 Wh
        # delta_co2_g = (1.5 / 1000) * 0.4 = 0.0006 gCO2e
        collector.co2_counter.add.assert_called_once_with(pytest.approx(0.0006), {"gpu_id": "0"})
        assert collector.cumulative_energy_wh[0] == pytest.approx(1.5)
        assert collector.last_timestamp[0] == pytest.approx(1000.0)
        assert collector._stop_event.wait.call_count == 2
        collector._stop_event.wait.assert_has_calls([call(1), call(1)])

    @patch("genai_otel.gpu_metrics.time.time", return_value=1000.0)
    @patch("genai_otel.gpu_metrics.logger")
    def test_collect_loop_co2_disabled(
        self, mock_logger, mock_time, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        mock_otel_config.enable_co2_tracking = False
        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        collector.device_count = 1
        collector.last_timestamp = [990.0]
        collector.interval = 1

        collector._stop_event.wait = Mock(side_effect=[False, True])

        collector._collect_loop()

        collector.co2_counter.add.assert_not_called()
        assert collector.cumulative_energy_wh[0] == 1.5
        assert collector.last_timestamp[0] == 1000.0

    @patch("genai_otel.gpu_metrics.time.time", return_value=1000.0)
    @patch("genai_otel.gpu_metrics.logger")
    def test_collect_loop_error_handling(
        self, mock_logger, mock_time, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        collector.device_count = 1
        collector.last_timestamp = [990.0]
        collector.interval = 1

        mock_pynvml_gpu_available.nvmlDeviceGetPowerUsage.side_effect = Exception(
            "Power usage error"
        )
        collector._stop_event.wait = Mock(side_effect=[False, True])

        collector._collect_loop()

        mock_logger.error.assert_called_once_with(
            "Error collecting GPU 0 metrics: Power usage error"
        )
        collector.co2_counter.add.assert_not_called()
        assert collector.cumulative_energy_wh[0] == 0.0  # No energy added due to error
        assert collector.last_timestamp[0] == 990.0  # Timestamp not updated due to error

    @patch("genai_otel.gpu_metrics.logger")
    @patch("genai_otel.gpu_metrics.threading.Event")
    def test_stop_no_threads_running(
        self, mock_event_class, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        collector._thread = None
        collector._stop_event = mock_event_class.return_value  # Assign the mock instance
        collector.stop()
        mock_logger.info.assert_not_called()
        collector._stop_event.set.assert_called_once()
        mock_pynvml_gpu_available.nvmlShutdown.assert_called_once()

    @patch("genai_otel.gpu_metrics.logger")
    @patch("genai_otel.gpu_metrics.threading.Event")
    def test_stop_threads_running(
        self, mock_event_class, mock_logger, mock_meter, mock_otel_config, mock_pynvml_gpu_available
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        # With new implementation, there's no self.running or self.thread attributes
        collector._thread = Mock()
        collector._thread.is_alive.return_value = True
        collector._stop_event = mock_event_class.return_value  # Assign the mock instance

        collector.stop()

        # Only CO2 collection thread
        collector._thread.join.assert_called_once_with(timeout=5)
        mock_logger.info.assert_called_once_with("GPU CO2 metrics collection thread stopped.")
        collector._stop_event.set.assert_called_once()
        mock_pynvml_gpu_available.nvmlShutdown.assert_called_once()

    @patch("genai_otel.gpu_metrics.logger")
    def test_stop_gpu_not_available(
        self, mock_logger, mock_meter, mock_otel_config, mock_pynvml_no_gpu
    ):
        import genai_otel.gpu_metrics

        collector = genai_otel.gpu_metrics.GPUMetricsCollector(mock_meter, mock_otel_config)
        assert not collector.gpu_available  # From mock_pynvml_no_gpu
        collector.stop()
        mock_pynvml_no_gpu.nvmlShutdown.assert_not_called()  # Should not be called if no GPU
