"""Minimal embedding test to verify the system works.

Uses a tiny model to avoid resource constraints.
"""


def test_embedding_import():
    """Test that we can import the embedding module."""
    from cert.embeddings import EmbeddingComparator

    assert EmbeddingComparator is not None


def test_embedding_initialization_lightweight():
    """Test embedding initialization with a lightweight model.

    Uses paraphrase-MiniLM-L3-v2 (60MB) instead of all-MiniLM-L6-v2 (420MB).
    """
    from cert.embeddings import EmbeddingComparator

    # Use smallest possible model for testing
    comparator = EmbeddingComparator(
        model_name="paraphrase-MiniLM-L3-v2",  # Much smaller: ~60MB
        threshold=0.75,
    )

    # Basic sanity check
    result = comparator.compare("hello", "hello")
    assert result.matched is True
    assert result.confidence > 0.95

    # Different texts
    result = comparator.compare("hello", "goodbye")
    assert result.matched is False


def test_embedding_vocabulary_substitutions():
    """Test that embeddings handle vocabulary substitutions.

    These are the failures from Apple 10-K that rules couldn't handle.
    """
    from cert.embeddings import EmbeddingComparator

    # Use lightweight model
    comparator = EmbeddingComparator(
        model_name="paraphrase-MiniLM-L3-v2",
        threshold=0.50,  # Lower threshold for smaller model
    )

    # Test vocabulary substitutions
    # Note: Mini model has lower accuracy, so we test basic capability
    test_cases = [
        ("smartphones", "phones", True),  # Should match
        ("weather", "stock market", False),  # Should not match
    ]

    results = []
    for expected, actual, should_match in test_cases:
        result = comparator.compare(expected, actual)
        matched = result.matched
        confidence = result.confidence

        status = "✓" if matched == should_match else "✗"
        print(
            f"{status} '{expected}' vs '{actual}': {matched} (conf: {confidence:.3f})"
        )

        results.append(matched == should_match)

    # Mini model should get at least these 2 basic cases right
    accuracy = sum(results) / len(results)
    print(f"\nAccuracy: {accuracy:.1%}")
    assert accuracy >= 1.0, f"Mini model failed basic tests: {accuracy:.1%}"


if __name__ == "__main__":
    """Run tests manually."""
    print("Testing minimal embedding model...\n")

    try:
        test_embedding_import()
        print("✓ Import successful\n")

        test_embedding_initialization_lightweight()
        print("✓ Lightweight model works\n")

        test_embedding_vocabulary_substitutions()
        print("\n✓ All tests passed!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
