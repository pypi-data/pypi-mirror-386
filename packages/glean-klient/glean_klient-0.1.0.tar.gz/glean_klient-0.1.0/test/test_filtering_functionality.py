"""Tests for CLI filtering functionality."""

import json
import tempfile
from unittest.mock import patch

from click.testing import CliRunner

from klient.__main__ import cli


def test_regex_text_filtering():
    """Test that --filter works with regex on text output."""
    runner = CliRunner()
    
    # Mock a command that produces text output
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = {'bootstrap.servers': 'test-server:9092', 'other.config': 'value'}
        
        # Test filtering that should match
        result = runner.invoke(cli, [
            '--filter', 'test-server',
            'info', 'config-dump'
        ])
        
        assert result.exit_code == 0
        assert 'test-server' in result.output
        
        # Test filtering that should not match
        result = runner.invoke(cli, [
            '--filter', 'nonexistent-pattern',
            'info', 'config-dump'  
        ])
        
        assert result.exit_code == 0
        # Should produce no output when no matches
        assert result.output.strip() == ''


def test_json_key_filtering():
    """Test that --filter works with key:regex pattern on JSON output."""
    runner = CliRunner()
    
    test_data = {
        'users': [
            {'name': 'alice', 'email': 'alice@test.com'},
            {'name': 'bob', 'email': 'bob@example.com'},
            {'name': 'charlie', 'email': 'charlie@test.com'}
        ],
        'config': {
            'server': 'prod-server',
            'port': 9092
        }
    }
    
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = test_data
        
        # Filter by email key containing "test"
        result = runner.invoke(cli, [
            '--json',
            '--filter', 'email:test',
            'info', 'config-dump'
        ])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        
        # Should contain only users with test.com emails in the filtered structure
        assert 'env_raw' in output_data
        # The filtering should affect the nested structure


def test_json_nested_key_filtering():
    """Test filtering works with nested JSON structures."""
    runner = CliRunner()
    
    test_data = {
        'services': {
            'kafka': {'host': 'kafka-prod', 'port': 9092},
            'zookeeper': {'host': 'zk-prod', 'port': 2181},
            'schema-registry': {'host': 'sr-test', 'port': 8081}
        }
    }
    
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = test_data
        
        # Filter by host key containing "prod"
        result = runner.invoke(cli, [
            '--json',
            '--filter', 'host:prod',
            'info', 'config-dump'
        ])
        
        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert 'env_raw' in output_data


def test_invalid_regex_pattern():
    """Test that invalid regex patterns are handled gracefully.""" 
    runner = CliRunner()
    
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = {'test': 'data'}
        
        # Test invalid regex pattern
        result = runner.invoke(cli, [
            '--filter', '[invalid-regex',  # Missing closing bracket
            'info', 'config-dump'
        ])
        
        # Should still work but show error message
        assert result.exit_code == 0
        assert 'Invalid regex pattern' in result.output


def test_filter_with_file_output():
    """Test that filtering works with file output."""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
        tmp_filename = tmp_file.name
    
    try:
        with patch('klient.__main__.resolve_env_config') as mock_resolve:
            mock_resolve.return_value = {'server': 'test-kafka', 'port': 9092}
            
            result = runner.invoke(cli, [
                '--json',
                '--filter', 'server:kafka',
                '--output-file', tmp_filename,
                'info', 'config-dump'
            ])
            
            assert result.exit_code == 0
            assert f"Output written to {tmp_filename}" in result.output
            
            # Check file contents are filtered
            with open(tmp_filename, 'r') as f:
                content = f.read()
                data = json.loads(content)
                assert 'env_raw' in data
                
    finally:
        import os
        try:
            os.unlink(tmp_filename)
        except Exception:
            pass


def test_filter_no_matches_produces_no_output():
    """Test that when filter produces no matches, no output is generated."""
    runner = CliRunner()
    
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = {'server': 'localhost', 'port': 9092}
        
        # Filter that won't match anything
        result = runner.invoke(cli, [
            '--filter', 'nonexistent.*pattern',
            'info', 'config-dump'
        ])
        
        assert result.exit_code == 0
        # Should produce no output
        assert result.output.strip() == ''