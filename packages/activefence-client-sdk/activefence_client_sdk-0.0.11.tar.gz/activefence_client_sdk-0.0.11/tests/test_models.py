from activefence_client_sdk.models import AnalysisContext, CustomField


def test_custom_field_hash_with_arrays() -> None:
    """Test that CustomField instances with equal array values have the same hash."""
    # Create arrays with the same content
    array1 = ["test", "1"]
    array2 = ["test", "1"]

    # Create CustomField instances with these arrays
    field1 = CustomField(name="test_field", value=array1)
    field2 = CustomField(name="test_field", value=array2)

    # Test equality
    assert field1 == field2, "CustomField instances with equal arrays should be equal"

    # Test hash equality
    hash1 = hash(field1)
    hash2 = hash(field2)
    assert hash1 == hash2, "CustomField instances with equal arrays should have the same hash"

    # Test that they can be used in a set (which requires hashable objects)
    test_set = {field1, field2}
    assert len(test_set) == 1, "Set should contain only one unique CustomField"

    # Test with different arrays
    array3 = ["different"]
    field3 = CustomField(name="test_field", value=array3)

    # Should not be equal
    assert field1 != field3, "CustomField instances with different arrays should not be equal"

    # Should have different hashes
    hash3 = hash(field3)
    assert hash1 != hash3, "CustomField instances with different arrays should have different hashes"


def test_analysis_context_creation() -> None:
    """Test that AnalysisContext is created correctly."""
    context = AnalysisContext(
        session_id="test_session_id",
    )
    assert context.session_id == "test_session_id"
    assert context.user_id is None
    assert context.provider is None
    assert context.model_name is None
    assert context.model_version is None
    assert context.platform is None
