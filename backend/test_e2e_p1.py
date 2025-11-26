#!/usr/bin/env python
"""End-to-end test for P1 refactoring (Service separation)."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.extraction_agent import ExtractionAgent
from agents.generation_agent import GenerationAgent
from core.llm_provider import MockLLMProvider
from services.job_normalizer import JobNormalizer
from services.language_detector import LanguageDetector
from services.score_extractor import ScoreExtractor
from services.scraper import ScrapedJob


def test_job_normalizer():
    """Test JobNormalizer service."""
    print("\n[TEST] JobNormalizer Service")
    print("-" * 60)

    normalizer = JobNormalizer()

    # Test deduplication
    skills = ["Python", "python", "JavaScript", "Python", "JS", "js", "JavaScript"]
    deduped = normalizer.dedupe_strings(skills)

    assert len(deduped) == 3, f"Expected 3 unique skills, got {len(deduped)}"
    assert "Python" in deduped, "Python should be in deduped list"
    assert "JavaScript" in deduped, "JavaScript should be in deduped list"
    print("[OK] Deduplication works correctly")

    # Test merge_with_llm_output
    original = ScrapedJob(
        url="https://example.com/job/123",
        board="generic",
        title="Developer",
        company="Example Inc",
        description="Looking for a developer with Python experience to join our team and build amazing applications.",
        skills=["Python", "JavaScript"],
        raw_html="<html>job content</html>",
    )

    llm_output = {
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "description": "Looking for an experienced Python developer to join our team and build scalable applications.",
        "skills": ["Python", "Django", "PostgreSQL"],
        "highlights": ["Fast paced", "Remote"],
    }

    merged = normalizer.merge_with_llm_output(original, llm_output)

    assert merged.title == "Senior Python Developer", "LLM output should take precedence"
    assert merged.company == "Tech Corp", "LLM output should take precedence"
    assert len(merged.skills) == 3, "Skills should be merged"
    print("[OK] Merge with LLM output works correctly")

    return True


def test_language_detector():
    """Test LanguageDetector service."""
    print("\n[TEST] LanguageDetector Service")
    print("-" * 60)

    detector = LanguageDetector()

    # Test Portuguese detection
    pt_text = "Você será responsável pelo desenvolvimento de sistemas utilizando conhecimento e experiência em Python."
    detected = detector.detect(pt_text)
    assert detected == "pt", f"Expected Portuguese (pt), got {detected}"
    print("[OK] Portuguese detection works")

    # Test Spanish detection
    es_text = "Usted será responsable del desarrollo de sistemas utilizando conocimiento y experiencia en Python."
    detected = detector.detect(es_text)
    assert detected == "es", f"Expected Spanish (es), got {detected}"
    print("[OK] Spanish detection works")

    # Test French detection
    fr_text = "Vous serez responsable du développement de systèmes utilisant la connaissance et l'expérience en Python."
    detected = detector.detect(fr_text)
    assert detected == "fr", f"Expected French (fr), got {detected}"
    print("[OK] French detection works")

    # Test English default
    en_text = "You will be responsible for developing applications in Python."
    detected = detector.detect(en_text)
    assert detected == "en", f"Expected English (en), got {detected}"
    print("[OK] English default works")

    # Test format_language_name
    name = detector.format_language_name("pt")
    assert name == "Portuguese", f"Expected 'Portuguese', got {name}"
    print("[OK] Language name formatting works")

    return True


def test_score_extractor():
    """Test ScoreExtractor service."""
    print("\n[TEST] ScoreExtractor Service")
    print("-" * 60)

    extractor = ScoreExtractor()

    # Test Portuguese score extraction
    pt_insights = "Compatibilidade: 85/100\nVoce e um excelente candidato para esta posicao."
    score = extractor.extract(pt_insights)
    assert score == 85, f"Expected score 85, got {score}"
    print("[OK] Portuguese score extraction works")

    # Test English score extraction
    en_insights = "Compatibility: 92/100\nYou are an excellent candidate for this position."
    score = extractor.extract(en_insights)
    assert score == 92, f"Expected score 92, got {score}"
    print("[OK] English score extraction works")

    # Test score clamping
    invalid_insights = "Score: 150/100\nThis score is out of range."
    score = extractor.extract(invalid_insights)
    assert score == 100, f"Expected clamped score 100, got {score}"
    print("[OK] Score clamping works")

    # Test empty text returns 0
    score = extractor.extract("")
    assert score == 0, f"Expected score 0 for empty text, got {score}"
    print("[OK] Empty text returns 0")

    # Test score formatting
    formatted = extractor.format_score(85)
    assert "85/100" in formatted, f"Expected '85/100' in formatted score, got {formatted}"
    assert "Excellent" in formatted, f"Expected 'Excellent' interpretation, got {formatted}"
    print("[OK] Score formatting works")

    return True


async def test_extraction_agent_with_normalizer():
    """Test ExtractionAgent with JobNormalizer."""
    print("\n[TEST] ExtractionAgent with JobNormalizer")
    print("-" * 60)

    # Create mock provider with valid JSON response
    mock_provider = MockLLMProvider(
        response='{"title": "Senior Python Developer", "company": "Tech Corp", "description": "Looking for an experienced Python developer to join our team and build scalable web applications with modern technologies.", "skills": ["Python", "Django", "PostgreSQL"], "highlights": ["Fast paced", "Remote", "Great team"]}'
    )

    # Create agent with mock
    agent = ExtractionAgent(llm_provider=mock_provider)
    print("[OK] ExtractionAgent created with mock provider")

    # Create a sample job
    job = ScrapedJob(
        url="https://example.com/job/456",
        board="generic",
        title="Developer",
        company="Example Inc",
        description="We are looking for a Python developer with experience in Django to build scalable web applications and work with modern technologies.",
        skills=["Python", "Django"],
        raw_html="<html>job content</html>",
    )

    # Run extraction
    try:
        result = await agent.run(job)
        print("[OK] Extraction completed successfully")
        assert result.job.title == "Senior Python Developer", "Title should be from LLM"
        assert result.job.company == "Tech Corp", "Company should be from LLM"
        assert len(result.job.skills) > 0, "Skills should be extracted"
        print(f"  - Title: {result.job.title}")
        print(f"  - Company: {result.job.company}")
        print(f"  - Skills count: {len(result.job.skills)}")
        print(f"  - Highlights: {len(result.highlights)} extracted")
        return True
    except Exception as e:
        print(f"[FAIL] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_generation_agent_with_services():
    """Test GenerationAgent with LanguageDetector and ScoreExtractor."""
    print("\n[TEST] GenerationAgent with Language and Score Services")
    print("-" * 60)

    # Create mock provider that returns insights with score
    mock_response = "Generated material with Compatibility: 78/100"
    mock_provider = MockLLMProvider(response=mock_response)

    # Create language detector and score extractor
    language_detector = LanguageDetector()
    score_extractor = ScoreExtractor()

    # Create agent with services
    agent = GenerationAgent(
        llm_provider=mock_provider,
        language_detector=language_detector,
        score_extractor=score_extractor,
    )
    print("[OK] GenerationAgent created with services")

    # Create sample data
    job_data = {
        "title": "Senior Developer",
        "company": "Tech Corp",
        "description": "Você será responsável pelo desenvolvimento de aplicações Python com Django e experiência em sistemas distribuídos.",
        "skills": ["Python", "Django", "PostgreSQL"],
    }
    cv_text = "5 years of Python development experience with Django framework"

    # Test language detection with Portuguese job
    try:
        result = await agent.generate_all(job_data, cv_text, language="auto")
        print("[OK] Generation completed with language auto-detection")

        # Check that score was extracted
        assert result.match_score > 0, "Match score should be extracted from insights"
        assert result.match_score <= 100, "Match score should be within valid range"
        print(f"  - Match score: {result.match_score}/100")
        print(f"  - Generated CV length: {len(result.cv)} chars")
        print(f"  - Generated cover letter length: {len(result.cover_letter)} chars")

        return True
    except Exception as e:
        print(f"[FAIL] Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backward_compatibility_with_services():
    """Test that agents work without explicit service parameters."""
    print("\n[TEST] Backward Compatibility (Default Services)")
    print("-" * 60)

    try:
        # Create agents without explicitly passing services
        # They should create default services internally

        # ExtractionAgent should create default JobNormalizer
        extraction_agent = ExtractionAgent(
            llm_provider=MockLLMProvider(
                response='{"title": "Dev", "company": "Corp", "description": "Looking for developers with experience in building scalable systems.", "skills": ["Python"], "highlights": []}'
            )
        )
        print("[OK] ExtractionAgent created without explicit normalizer")

        # GenerationAgent should create default services
        generation_agent = GenerationAgent(
            llm_provider=MockLLMProvider(response="Generated text with Compatibility: 75/100")
        )
        print("[OK] GenerationAgent created without explicit services")

        # Verify internal services are created
        assert hasattr(extraction_agent, "_normalizer"), "ExtractionAgent should have normalizer"
        assert hasattr(generation_agent, "_language_detector"), "GenerationAgent should have language detector"
        assert hasattr(generation_agent, "_score_extractor"), "GenerationAgent should have score extractor"
        print("[OK] Default services are properly initialized")

        return True
    except Exception as e:
        print(f"[FAIL] Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all P1 tests."""
    print("=" * 60)
    print("P1 REFACTORING - END-TO-END TESTS")
    print("Testing: Service Separation and Responsibility Distribution")
    print("=" * 60)

    results = []

    # Test 1: JobNormalizer Service
    try:
        results.append(("JobNormalizer Service", test_job_normalizer()))
    except Exception as e:
        print(f"[FAIL] JobNormalizer test failed with exception: {e}")
        results.append(("JobNormalizer Service", False))

    # Test 2: LanguageDetector Service
    try:
        results.append(("LanguageDetector Service", test_language_detector()))
    except Exception as e:
        print(f"[FAIL] LanguageDetector test failed with exception: {e}")
        results.append(("LanguageDetector Service", False))

    # Test 3: ScoreExtractor Service
    try:
        results.append(("ScoreExtractor Service", test_score_extractor()))
    except Exception as e:
        print(f"[FAIL] ScoreExtractor test failed with exception: {e}")
        results.append(("ScoreExtractor Service", False))

    # Test 4: ExtractionAgent with Normalizer
    results.append(
        ("ExtractionAgent with Normalizer", await test_extraction_agent_with_normalizer())
    )

    # Test 5: GenerationAgent with Services
    results.append(
        ("GenerationAgent with Services", await test_generation_agent_with_services())
    )

    # Test 6: Backward Compatibility
    results.append(
        ("Backward Compatibility (Default Services)", await test_backward_compatibility_with_services())
    )

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
