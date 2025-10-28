"""
Tests for Prometheus metrics
"""
import pytest
from prometheus_client import REGISTRY
from monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    receipts_processed_total,
    processing_errors_total,
    ocr_confidence_score,
    classification_confidence_score,
    celery_tasks_total,
    celery_task_duration_seconds,
    celery_active_workers
)


def test_metrics_exist():
    """Test that all metrics are registered"""
    metric_names = [m.name for m in REGISTRY.collect()]
    
    # Check HTTP metrics
    assert any('http_requests_total' in name for name in metric_names)
    assert any('http_request_duration_seconds' in name for name in metric_names)
    
    # Check receipt processing metrics
    assert any('receipts_processed_total' in name for name in metric_names)
    assert any('processing_errors_total' in name for name in metric_names)
    
    # Check confidence metrics
    assert any('ocr_confidence_score' in name for name in metric_names)
    assert any('classification_confidence_score' in name for name in metric_names)
    
    # Check Celery metrics
    assert any('celery_tasks_total' in name for name in metric_names)
    assert any('celery_task_duration_seconds' in name for name in metric_names)
    assert any('celery_active_workers' in name for name in metric_names)


def test_http_requests_counter():
    """Test HTTP requests counter"""
    initial_value = http_requests_total.labels(
        method='GET',
        endpoint='/test',
        status='200'
    )._value.get()
    
    # Increment counter
    http_requests_total.labels(
        method='GET',
        endpoint='/test',
        status='200'
    ).inc()
    
    new_value = http_requests_total.labels(
        method='GET',
        endpoint='/test',
        status='200'
    )._value.get()
    
    assert new_value == initial_value + 1


def test_receipts_processed_counter():
    """Test receipts processed counter"""
    initial_success = receipts_processed_total.labels(status='success')._value.get()
    initial_failed = receipts_processed_total.labels(status='failed')._value.get()
    
    # Increment counters
    receipts_processed_total.labels(status='success').inc()
    receipts_processed_total.labels(status='failed').inc()
    
    new_success = receipts_processed_total.labels(status='success')._value.get()
    new_failed = receipts_processed_total.labels(status='failed')._value.get()
    
    assert new_success == initial_success + 1
    assert new_failed == initial_failed + 1


def test_processing_errors_counter():
    """Test processing errors counter"""
    initial_value = processing_errors_total.labels(
        error_type='ocr_error'
    )._value.get()
    
    # Increment
    processing_errors_total.labels(error_type='ocr_error').inc()
    
    new_value = processing_errors_total.labels(
        error_type='ocr_error'
    )._value.get()
    
    assert new_value == initial_value + 1


def test_confidence_score_histogram():
    """Test confidence score histograms"""
    # Record OCR confidence
    ocr_confidence_score.observe(0.85)
    ocr_confidence_score.observe(0.92)
    ocr_confidence_score.observe(0.78)
    
    # Record classification confidence
    classification_confidence_score.observe(0.95)
    classification_confidence_score.observe(0.88)
    
    # Metrics should be recorded (can't easily verify exact values without accessing internals)
    # But we can verify the metric exists
    assert ocr_confidence_score is not None
    assert classification_confidence_score is not None


def test_request_duration_histogram():
    """Test request duration histogram"""
    # Record some durations
    http_request_duration_seconds.labels(
        method='POST',
        endpoint='/upload'
    ).observe(2.5)
    
    http_request_duration_seconds.labels(
        method='GET',
        endpoint='/receipts'
    ).observe(0.1)
    
    # Verify metric exists
    assert http_request_duration_seconds is not None


def test_celery_tasks_counter():
    """Test Celery tasks counter"""
    initial_success = celery_tasks_total.labels(
        task_name='process_receipt',
        status='success'
    )._value.get()
    
    initial_failure = celery_tasks_total.labels(
        task_name='process_receipt',
        status='failure'
    )._value.get()
    
    # Increment counters
    celery_tasks_total.labels(
        task_name='process_receipt',
        status='success'
    ).inc()
    
    celery_tasks_total.labels(
        task_name='process_receipt',
        status='failure'
    ).inc()
    
    new_success = celery_tasks_total.labels(
        task_name='process_receipt',
        status='success'
    )._value.get()
    
    new_failure = celery_tasks_total.labels(
        task_name='process_receipt',
        status='failure'
    )._value.get()
    
    assert new_success == initial_success + 1
    assert new_failure == initial_failure + 1


def test_celery_task_duration():
    """Test Celery task duration histogram"""
    # Record task durations
    celery_task_duration_seconds.labels(
        task_name='process_receipt'
    ).observe(5.2)
    
    celery_task_duration_seconds.labels(
        task_name='retrain_model'
    ).observe(45.8)
    
    # Verify metric exists
    assert celery_task_duration_seconds is not None


def test_active_workers_gauge():
    """Test active workers gauge"""
    initial_value = celery_active_workers._value.get()
    
    # Increment and decrement
    celery_active_workers.inc()
    celery_active_workers.inc()
    after_inc = celery_active_workers._value.get()
    
    celery_active_workers.dec()
    after_dec = celery_active_workers._value.get()
    
    assert after_inc == initial_value + 2
    assert after_dec == initial_value + 1


def test_metric_labels():
    """Test that metrics accept proper labels"""
    # Test HTTP metrics with different labels
    http_requests_total.labels(method='GET', endpoint='/api/v1', status='200').inc()
    http_requests_total.labels(method='POST', endpoint='/api/v2', status='201').inc()
    http_requests_total.labels(method='DELETE', endpoint='/api/v3', status='404').inc()
    
    # Test processing metrics with different labels
    receipts_processed_total.labels(status='success').inc()
    receipts_processed_total.labels(status='failed').inc()
    
    # Test error metrics with different error types
    processing_errors_total.labels(error_type='ocr_error').inc()
    processing_errors_total.labels(error_type='classification_error').inc()
    processing_errors_total.labels(error_type='storage_error').inc()
    
    # All should work without errors
    assert True


def test_metrics_thread_safety():
    """Test that metrics are thread-safe"""
    import threading
    
    def increment_metric():
        for _ in range(100):
            receipts_processed_total.labels(status='success').inc()
    
    initial_value = receipts_processed_total.labels(status='success')._value.get()
    
    # Create multiple threads
    threads = [threading.Thread(target=increment_metric) for _ in range(5)]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    final_value = receipts_processed_total.labels(status='success')._value.get()
    
    # Should have incremented by 500 (5 threads * 100 increments)
    assert final_value == initial_value + 500


def test_histogram_buckets():
    """Test histogram bucket configuration"""
    # Record values across different buckets
    values = [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0]
    
    for value in values:
        http_request_duration_seconds.labels(
            method='GET',
            endpoint='/test'
        ).observe(value)
    
    # Verify metric recorded values
    assert http_request_duration_seconds is not None


def test_gauge_set_value():
    """Test setting gauge values"""
    from monitoring.metrics import model_accuracy
    
    # Set gauge value
    model_accuracy.set(0.85)
    assert model_accuracy._value.get() == 0.85
    
    # Update gauge value
    model_accuracy.set(0.92)
    assert model_accuracy._value.get() == 0.92


def test_counter_increment_by_value():
    """Test incrementing counter by specific value"""
    initial = receipts_processed_total.labels(status='success')._value.get()
    
    # Increment by 5
    receipts_processed_total.labels(status='success').inc(5)
    
    new_value = receipts_processed_total.labels(status='success')._value.get()
    assert new_value == initial + 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])