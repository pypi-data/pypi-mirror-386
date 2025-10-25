#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test OpenAI Speech-to-Text Models
Tests all 4 models: whisper-1, gpt-4o-mini-transcribe, gpt-4o-transcribe, gpt-4o-transcribe-diarize
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from isa_model.inference.services.audio.openai_stt_service import OpenAISTTService


# ANSI Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

test_results = []


def print_section(title):
    """Print section header"""
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")


def print_result(passed, test_name, details=""):
    """Print test result"""
    if passed:
        print(f"{GREEN}✓ PASSED{NC}: {test_name}")
        test_results.append((test_name, True))
    else:
        print(f"{RED}✗ FAILED{NC}: {test_name}")
        test_results.append((test_name, False))

    if details:
        print(f"  {CYAN}{details}{NC}")


async def test_model(model_name: str, audio_file: str, enable_diarization: bool = False):
    """Test a specific STT model"""
    print_section(f"Testing: {model_name}")

    try:
        # Create service
        print(f"Initializing {model_name}...")
        service = OpenAISTTService(provider_name="openai", model_name=model_name)

        # Check model capabilities
        capabilities = service.model_capabilities
        print(f"Model capabilities:")
        print(f"  - Streaming: {capabilities.get('supports_streaming')}")
        print(f"  - Prompting: {capabilities.get('supports_prompting')}")
        print(f"  - Diarization: {capabilities.get('supports_diarization')}")
        print(f"  - Formats: {', '.join(capabilities.get('response_formats', []))}")
        print()

        # Test transcription
        print(f"Transcribing {audio_file}...")
        start_time = asyncio.get_event_loop().time()

        result = await service.transcribe(
            audio_file=audio_file,
            enable_diarization=enable_diarization,
            prompt="This is a test of speech recognition accuracy" if capabilities.get('supports_prompting') else None
        )

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Print results
        print(f"\n{CYAN}Results:{NC}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Language: {result.get('language', 'unknown')}")
        print(f"  Audio duration: {result.get('duration', 'N/A')}s")
        print(f"  Text length: {len(result.get('text', ''))} chars")
        print(f"\n{CYAN}Transcription:{NC}")
        print(f"  {result.get('text', 'N/A')[:200]}...")

        # Check usage info
        usage = result.get('usage', {})
        if usage:
            print(f"\n{CYAN}Usage:{NC}")
            print(f"  Input units: {usage.get('input_units', 'N/A')}")
            print(f"  Output tokens: {usage.get('output_tokens', 'N/A')}")

        # Check diarization segments if enabled
        if enable_diarization and 'diarized_segments' in result:
            print(f"\n{CYAN}Diarized Segments: {len(result['diarized_segments'])}{NC}")
            for i, segment in enumerate(result['diarized_segments'][:5]):
                print(f"  [{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['speaker']}: {segment['text'][:50]}...")
            if len(result['diarized_segments']) > 5:
                print(f"  ... and {len(result['diarized_segments']) - 5} more segments")

        # Cleanup
        await service.close()

        # Verify result
        if result.get('text') and len(result['text']) > 10:
            print_result(True, f"{model_name} transcription", f"Processed in {duration:.2f}s")
            return True
        else:
            print_result(False, f"{model_name} transcription", "Text too short or empty")
            return False

    except Exception as e:
        print(f"{RED}Error: {e}{NC}")
        import traceback
        traceback.print_exc()
        print_result(False, f"{model_name} transcription", f"Exception: {str(e)}")
        return False


async def test_streaming(model_name: str, audio_file: str):
    """Test streaming transcription"""
    print_section(f"Testing Streaming: {model_name}")

    try:
        service = OpenAISTTService(provider_name="openai", model_name=model_name)

        # Check if streaming is supported
        if not service.model_capabilities.get('supports_streaming'):
            print(f"{YELLOW}Streaming not supported for {model_name}, skipping{NC}")
            return True

        print(f"Starting streaming transcription...")

        # Note: Current implementation doesn't stream, but we can test the parameter
        result = await service.transcribe(
            audio_file=audio_file,
            stream=True  # Enable streaming
        )

        print(f"\n{CYAN}Streaming Result:{NC}")
        print(f"  Text: {result.get('text', 'N/A')[:200]}...")

        await service.close()

        if result.get('text'):
            print_result(True, f"{model_name} streaming", "Streaming parameter accepted")
            return True
        else:
            print_result(False, f"{model_name} streaming", "No text returned")
            return False

    except Exception as e:
        print(f"{RED}Error: {e}{NC}")
        print_result(False, f"{model_name} streaming", f"Exception: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print(f"{BLUE}{'='*70}{NC}")
    print(f"{BLUE}OpenAI Speech-to-Text Model Tests{NC}")
    print(f"{BLUE}{'='*70}{NC}")

    # Test audio file
    audio_file = str(project_root / "tests" / "test_data" / "harvard.wav")

    if not os.path.exists(audio_file):
        print(f"{RED}Error: Test audio file not found: {audio_file}{NC}")
        return

    print(f"\n{CYAN}Test Audio:{NC} {audio_file}")
    print(f"{CYAN}File Size:{NC} {os.path.getsize(audio_file) / 1024:.1f} KB")
    print()

    # Test all models
    models_to_test = [
        ("whisper-1", False),  # Legacy model
        ("gpt-4o-mini-transcribe", False),  # NEW DEFAULT
        ("gpt-4o-transcribe", False),  # Highest quality
        ("gpt-4o-transcribe-diarize", True),  # With diarization
    ]

    for model_name, enable_diarization in models_to_test:
        await test_model(model_name, audio_file, enable_diarization)
        print()

    # Test streaming on the new models
    print_section("Streaming Tests")
    for model_name in ["gpt-4o-mini-transcribe", "gpt-4o-transcribe"]:
        await test_streaming(model_name, audio_file)
        print()

    # Print summary
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")

    passed = sum(1 for _, result in test_results if result)
    failed = sum(1 for _, result in test_results if not result)
    total = len(test_results)

    print(f"{GREEN}✓ Passed: {passed}{NC}")
    print(f"{RED}✗ Failed: {failed}{NC}")
    print(f"Total: {total}")

    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\n{CYAN}Success Rate: {success_rate:.1f}%{NC}")

    print()

    # Print individual results
    print(f"{CYAN}Individual Results:{NC}")
    for test_name, result in test_results:
        status = f"{GREEN}✓{NC}" if result else f"{RED}✗{NC}"
        print(f"  {status} {test_name}")

    print()

    if failed == 0:
        print(f"{GREEN}🎉 All tests passed! STT models are working correctly.{NC}")
        return 0
    else:
        print(f"{RED}⚠️  Some tests failed. Please review the output above.{NC}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
