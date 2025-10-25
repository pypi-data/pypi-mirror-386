#!/usr/bin/env python3
"""
Test script for PostgreSQL Inference Repository

Tests basic CRUD operations and verifies PostgreSQL integration.
"""

import sys
import os
from datetime import datetime, timezone

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from isa_model.inference.repositories.inference_repository import InferenceRepository
from isa_model.inference.models.inference_record import InferenceStatus, ServiceType

def test_connection():
    """Test 1: Database Connection"""
    print("\n" + "=" * 80)
    print("Test 1: Database Connection")
    print("=" * 80)

    try:
        repo = InferenceRepository(
            host='isa-postgres-grpc',
            port=50061,
            user_id='test-inference-service'
        )

        if repo.check_connection():
            print("✅ PostgreSQL connection successful!")
            return repo
        else:
            print("❌ PostgreSQL connection failed")
            return None

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_create_request(repo: InferenceRepository):
    """Test 2: Create Inference Request"""
    print("\n" + "=" * 80)
    print("Test 2: Create Inference Request")
    print("=" * 80)

    try:
        request_data = {
            "messages": [{"role": "user", "content": "Hello, world!"}],
            "temperature": 0.7,
            "max_tokens": 100
        }

        request_id = repo.create_inference_request(
            service_type=ServiceType.LLM,
            model_id="gpt-4",
            provider="openai",
            endpoint="/v1/chat/completions",
            request_data=request_data,
            user_id="test-user-123",
            metadata={"test": True, "environment": "development"}
        )

        print(f"✅ Created inference request: {request_id}")
        return request_id

    except Exception as e:
        print(f"❌ Create request failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_request(repo: InferenceRepository, request_id: str):
    """Test 3: Get Inference Request"""
    print("\n" + "=" * 80)
    print("Test 3: Get Inference Request")
    print("=" * 80)

    try:
        request = repo.get_inference_request(request_id)

        if request:
            print(f"✅ Retrieved request: {request.request_id}")
            print(f"   Status: {request.status}")
            print(f"   Service Type: {request.service_type}")
            print(f"   Model: {request.model_id}")
            print(f"   Provider: {request.provider}")
            print(f"   User ID: {request.user_id}")
            return True
        else:
            print(f"❌ Request not found: {request_id}")
            return False

    except Exception as e:
        print(f"❌ Get request failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_status(repo: InferenceRepository, request_id: str):
    """Test 4: Update Request Status"""
    print("\n" + "=" * 80)
    print("Test 4: Update Request Status")
    print("=" * 80)

    try:
        # Update to processing
        success = repo.update_inference_status(
            request_id=request_id,
            status=InferenceStatus.PROCESSING
        )

        if success:
            print(f"✅ Updated status to PROCESSING")
        else:
            print(f"❌ Failed to update status to PROCESSING")
            return False

        # Update to completed with results
        response_data = {
            "choices": [{"message": {"role": "assistant", "content": "Hello! How can I help you?"}}]
        }

        success = repo.update_inference_status(
            request_id=request_id,
            status=InferenceStatus.COMPLETED,
            response_data=response_data,
            execution_time_ms=1250,
            tokens_used=50,
            input_tokens=10,
            output_tokens=40,
            cost_usd=0.00025
        )

        if success:
            print(f"✅ Updated status to COMPLETED with results")
            return True
        else:
            print(f"❌ Failed to update status to COMPLETED")
            return False

    except Exception as e:
        print(f"❌ Update status failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_requests(repo: InferenceRepository):
    """Test 5: List Recent Requests"""
    print("\n" + "=" * 80)
    print("Test 5: List Recent Requests")
    print("=" * 80)

    try:
        requests = repo.list_recent_requests(
            service_type=ServiceType.LLM,
            hours=24,
            limit=10
        )

        print(f"✅ Retrieved {len(requests)} recent requests")
        for req in requests[:3]:  # Show first 3
            print(f"   • {req.request_id}: {req.status} - {req.model_id}")

        return True

    except Exception as e:
        print(f"❌ List requests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_usage_statistics(repo: InferenceRepository):
    """Test 6: Record Usage Statistics"""
    print("\n" + "=" * 80)
    print("Test 6: Record Usage Statistics")
    print("=" * 80)

    try:
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        period_start = now - timedelta(hours=1)
        period_end = now

        stat_id = repo.record_usage_statistics(
            period_start=period_start,
            period_end=period_end,
            service_type=ServiceType.LLM,
            model_id="gpt-4",
            provider="openai",
            user_id="test-user-123",
            total_requests=10,
            successful_requests=9,
            failed_requests=1,
            total_tokens=500,
            total_cost_usd=0.0025
        )

        print(f"✅ Recorded usage statistics: {stat_id}")
        return True

    except Exception as e:
        print(f"❌ Record statistics failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_snapshot(repo: InferenceRepository):
    """Test 7: Update Model Snapshot"""
    print("\n" + "=" * 80)
    print("Test 7: Update Model Snapshot")
    print("=" * 80)

    try:
        snapshot_id = repo.update_model_snapshot(
            model_id="gpt-4",
            provider="openai",
            hourly_requests=50,
            daily_requests=1200,
            weekly_requests=8400,
            monthly_requests=36000,
            total_tokens_hour=2500,
            total_tokens_day=60000,
            total_cost_hour=0.125,
            total_cost_day=3.0,
            avg_response_time_hour=850.5,
            avg_response_time_day=920.3,
            success_rate_hour=98.5,
            success_rate_day=97.8
        )

        print(f"✅ Updated model snapshot: {snapshot_id}")
        return True

    except Exception as e:
        print(f"❌ Update snapshot failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PostgreSQL Inference Repository Tests")
    print("=" * 80)
    print("Connecting to: isa-postgres-grpc:50061")
    print("Schema: model_inference")

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0
    }

    # Test 1: Connection
    repo = test_connection()
    results["total"] += 1
    if repo:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("\n❌ Cannot proceed without database connection")
        return

    # Test 2: Create Request
    request_id = test_create_request(repo)
    results["total"] += 1
    if request_id:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("\n⚠️  Skipping remaining tests due to create failure")
        return

    # Test 3: Get Request
    results["total"] += 1
    if test_get_request(repo, request_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 4: Update Status
    results["total"] += 1
    if test_update_status(repo, request_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 5: List Requests
    results["total"] += 1
    if test_list_requests(repo):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 6: Usage Statistics
    results["total"] += 1
    if test_usage_statistics(repo):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 7: Model Snapshot
    results["total"] += 1
    if test_model_snapshot(repo):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {results['passed']/results['total']*100:.1f}%")
    print("=" * 80)

    if results['failed'] == 0:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
