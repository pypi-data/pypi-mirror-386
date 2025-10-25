import pytest
from moonito import VisitorTrafficFiltering, Config

# ============================================
# CONFIGURATION - Update these values once
# ============================================
TEST_API_PUBLIC_KEY = "your_public_key_here"
TEST_API_SECRET_KEY = "your_secret_key_here"


# ============================================
# Pytest Fixtures (shared setup)
# ============================================

@pytest.fixture
def config():
    """Create a config instance that can be reused across tests"""
    return Config(
        is_protected=True,
        api_public_key=TEST_API_PUBLIC_KEY,
        api_secret_key=TEST_API_SECRET_KEY
    )


@pytest.fixture
def vtf(config):
    """Create a VisitorTrafficFiltering instance that can be reused across tests"""
    return VisitorTrafficFiltering(config)


# ============================================
# Tests
# ============================================

def test_config_creation(config):
    """Test that config is created correctly"""
    assert config.is_protected == True
    assert config.api_public_key == TEST_API_PUBLIC_KEY
    assert config.api_secret_key == TEST_API_SECRET_KEY


def test_vtf_initialization(vtf):
    """Test that VisitorTrafficFiltering initializes correctly"""
    assert vtf.config.is_protected == True
    assert vtf.bypass_token is not None
    assert len(vtf.bypass_token) == 64  # 32 bytes = 64 hex chars


def test_ip_validation(vtf):
    """Test IP address validation"""
    # Valid IPv4
    assert vtf._is_valid_ip("192.168.1.1") == True
    assert vtf._is_valid_ip("8.8.8.8") == True
    
    # Valid IPv6
    assert vtf._is_valid_ip("2001:0db8::1") == True
    assert vtf._is_valid_ip("::1") == True
    
    # Invalid IPs
    assert vtf._is_valid_ip("invalid") == False
    assert vtf._is_valid_ip("999.999.999.999") == False
    assert vtf._is_valid_ip("") == False


def test_bypass_token_validation(vtf):
    """Test bypass token validation"""
    # Valid token
    assert vtf._is_valid_bypass_token(vtf.bypass_token) == True
    
    # Invalid tokens
    assert vtf._is_valid_bypass_token("wrong_token") == False
    assert vtf._is_valid_bypass_token(None) == False
    assert vtf._is_valid_bypass_token("") == False


def test_protection_disabled():
    """Test behavior when protection is disabled"""
    config_disabled = Config(
        is_protected=False,
        api_public_key=TEST_API_PUBLIC_KEY,
        api_secret_key=TEST_API_SECRET_KEY
    )
    vtf_disabled = VisitorTrafficFiltering(config_disabled)
    
    # When protection is disabled, should not block
    result = vtf_disabled.evaluate_visitor_manually(
        ip="192.168.1.1",
        user_agent="Test",
        event="/test",
        domain="example.com"
    )
    assert result['need_to_block'] == False
    assert result['detect_activity'] == None
    assert result['content'] == None


def test_url_matching(vtf):
    """Test URL matching logic"""
    # Test full URL matching
    assert vtf._urls_match(
        "https://example.com/blocked",
        "https://example.com/blocked"
    ) == True
    
    # Test path matching
    assert vtf._urls_match(
        "https://example.com/blocked",
        "/blocked"
    ) == True
    
    # Test non-matching
    assert vtf._urls_match(
        "https://example.com/allowed",
        "/blocked"
    ) == False


def test_blocked_content_status_code():
    """Test blocked content returns status code"""
    config_with_status = Config(
        is_protected=True,
        api_public_key=TEST_API_PUBLIC_KEY,
        api_secret_key=TEST_API_SECRET_KEY,
        unwanted_visitor_to="403"
    )
    vtf_status = VisitorTrafficFiltering(config_with_status)
    
    content = vtf_status._get_blocked_content()
    assert content == 403


def test_blocked_content_iframe():
    """Test blocked content returns iframe"""
    config_with_iframe = Config(
        is_protected=True,
        api_public_key=TEST_API_PUBLIC_KEY,
        api_secret_key=TEST_API_SECRET_KEY,
        unwanted_visitor_to="https://example.com/blocked",
        unwanted_visitor_action=2
    )
    vtf_iframe = VisitorTrafficFiltering(config_with_iframe)
    
    content = vtf_iframe._get_blocked_content()
    assert '<iframe' in content
    assert 'https://example.com/blocked' in content


def test_blocked_content_redirect():
    """Test blocked content returns redirect HTML"""
    config_with_redirect = Config(
        is_protected=True,
        api_public_key=TEST_API_PUBLIC_KEY,
        api_secret_key=TEST_API_SECRET_KEY,
        unwanted_visitor_to="https://example.com/blocked",
        unwanted_visitor_action=1
    )
    vtf_redirect = VisitorTrafficFiltering(config_with_redirect)
    
    content = vtf_redirect._get_blocked_content()
    assert 'window.location.href' in content
    assert 'https://example.com/blocked' in content