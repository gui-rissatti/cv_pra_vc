#!/usr/bin/env python
"""End-to-end test for P0 refactoring (LLMProvider abstraction)."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.llm_provider import MockLLMProvider, get_llm_provider
from agents.extraction_agent import ExtractionAgent
from agents.generation_agent import GenerationAgent
from services.scraper import ScrapedJob


async def test_extraction_agent_with_mock():
    """Test ExtractionAgent with MockLLMProvider."""
    print("\n[TEST] ExtractionAgent with MockLLMProvider")
    print("-" * 60)

    # Create mock provider
    mock_provider = MockLLMProvider(
        response='{"title": "Senior Developer", "company": "Tech Corp", "description": "We are seeking an experienced Python developer to join our team and build scalable applications. You will work with modern technologies and collaborate with talented engineers from around the world.", "skills": ["Python", "JavaScript"], "highlights": ["Fast", "Smart"]}'
    )

    # Create agent with mock provider
    agent = ExtractionAgent(llm_provider=mock_provider)
    print("[OK] ExtractionAgent created with MockLLMProvider")

    # Create a sample job
    job = ScrapedJob(
        url="https://example.com/job/123",
        board="generic",
        title="Developer",
        company="Example Inc",
        description="We are looking for an experienced Python developer to join our team and build amazing applications. You will work with cutting-edge technologies and collaborate with talented engineers.",
        skills=["Python"],
        raw_html="<html>job content</html>",
    )

    # Run extraction
    try:
        result = await agent.run(job)
        print(f"[OK] Extraction completed")
        print(f"  - Job ID: {result.job.url}")
        print(f"  - Title: {result.job.title}")
        print(f"  - Company: {result.job.company}")
        print(f"  - Skills: {result.job.skills}")
        print(f"  - Highlights: {result.highlights}")
        return True
    except Exception as e:
        print(f"[FAIL] Extraction failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_generation_agent_with_mock():
    """Test GenerationAgent with MockLLMProvider."""
    print("\n[TEST] GenerationAgent with MockLLMProvider")
    print("-" * 60)

    # Create mock provider
    mock_provider = MockLLMProvider(response="Generated material content")

    # Create agent with mock provider
    agent = GenerationAgent(llm_provider=mock_provider)
    print("[OK] GenerationAgent created with MockLLMProvider")

    # Create sample data
    job_data = {
        "title": "Senior Developer",
        "company": "Tech Corp",
        "description": "Build Python applications",
        "skills": ["Python", "Django", "PostgreSQL"],
    }
    cv_text = "5 years of Python experience"

    # Run generation
    try:
        result = await agent.generate_all(job_data, cv_text)
        print(f"[OK] Generation completed")
        print(f"  - CV length: {len(result.cv)} chars")
        print(f"  - Cover letter length: {len(result.cover_letter)} chars")
        print(f"  - Networking tips length: {len(result.networking)} chars")
        print(f"  - Insights length: {len(result.insights)} chars")
        print(f"  - Match score: {result.match_score}")
        return True
    except Exception as e:
        print(f"[FAIL] Generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_llm_provider_factory():
    """Test LLMProvider factory."""
    print("\n[TEST] LLMProvider Factory")
    print("-" * 60)

    # Test mock provider creation
    try:
        mock = get_llm_provider("mock", response="Test response")
        print("[OK] MockLLMProvider created via factory")

        # Test mock generation
        result = await mock.generate("Test prompt")
        assert result == "Test response"
        print("[OK] MockLLMProvider.generate() works")

        # Test parallel generation
        results = await mock.generate_parallel(["prompt1", "prompt2"])
        assert len(results) == 2
        print("[OK] MockLLMProvider.generate_parallel() works")
        return True
    except Exception as e:
        print(f"[FAIL] Factory test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_backward_compatibility():
    """Test that agents still work without explicit LLMProvider (uses default)."""
    print("\n[TEST] Backward Compatibility (Default Provider)")
    print("-" * 60)

    try:
        # Create agents without explicitly passing LLMProvider
        # They should use get_llm_provider("gemini") by default
        # But this will fail without GOOGLE_API_KEY set

        # Instead, test that we can create them with kwargs
        extraction = ExtractionAgent()
        print("[OK] ExtractionAgent created with default provider (configured)")

        generation = GenerationAgent()
        print("[OK] GenerationAgent created with default provider (configured)")

        return True
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e):
            print("[OK] Correctly fails without GOOGLE_API_KEY (expected)")
            return True
        else:
            print(f"[FAIL] Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("P0 REFACTORING - END-TO-END TESTS")
    print("Testing: LLMProvider abstraction")
    print("=" * 60)

    results = []

    # Test 1: LLMProvider Factory
    results.append(("LLMProvider Factory", await test_llm_provider_factory()))

    # Test 2: ExtractionAgent with Mock
    results.append(("ExtractionAgent with Mock", await test_extraction_agent_with_mock()))

    # Test 3: GenerationAgent with Mock
    results.append(("GenerationAgent with Mock", await test_generation_agent_with_mock()))

    # Test 4: Backward Compatibility
    results.append(("Backward Compatibility", await test_backward_compatibility()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return all(result for _, result in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
