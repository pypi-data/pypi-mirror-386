"""Tests for output file and JSON formatting functionality."""
import json
import tempfile
import os
from unittest.mock import patch
from click.testing import CliRunner

from klient.__main__ import cli


def test_output_to_file():
    """Test that --output-file writes output to specified file."""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
        tmp_filename = tmp_file.name
    
    try:
        # Mock the info config-dump command to avoid needing actual config
        with patch('klient.__main__.resolve_env_config') as mock_resolve:
            mock_resolve.return_value = {'test': 'data'}
            
            result = runner.invoke(cli, [
                '--output-file', tmp_filename,
                'info', 'config-dump'
            ])
            
            # Should succeed and write to file
            assert result.exit_code == 0
            assert f"Output written to {tmp_filename}" in result.output
            
            # Check file contents
            with open(tmp_filename, 'r') as f:
                content = f.read()
                data = json.loads(content)
                # The config-dump command returns more than just the raw config
                assert 'env_raw' in data
                assert data['env_raw'] == {'test': 'data'}
    
    finally:
        # Clean up
        if os.path.exists(tmp_filename):
            os.unlink(tmp_filename)


def test_pretty_json_formatting():
    """Test that pretty JSON formatting works correctly."""
    runner = CliRunner()
    
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = {'test': 'data', 'nested': {'key': 'value'}}
        
        # Test pretty JSON (default)
        result = runner.invoke(cli, ['--json', 'info', 'config-dump'])
        assert result.exit_code == 0
        
        # Should be formatted with indentation and sorted keys
        assert '{\n  "bootstrap": "localhost:9092"' in result.output  # Pretty formatting with indents and sorted keys
        
        # Test compact JSON
        result = runner.invoke(cli, ['--json', '--compact-json', 'info', 'config-dump'])
        assert result.exit_code == 0
        
        # Should be compact (no extra whitespace between keys)
        assert '{"env":null,' in result.output  # Compact formatting


def test_file_write_error_handling():
    """Test that file write errors are handled gracefully."""
    runner = CliRunner()
    
    with patch('klient.__main__.resolve_env_config') as mock_resolve:
        mock_resolve.return_value = {'test': 'data'}
        
        # Try to write to an invalid directory
        result = runner.invoke(cli, [
            '--output-file', '/nonexistent/directory/file.json',
            'info', 'config-dump'
        ])
        
        # Should exit with error
        assert result.exit_code == 1
        assert "Failed to write to" in result.output


def test_json_formatting_with_complex_data():
    """Test JSON formatting with complex data structures."""
    from klient.__main__ import _echo
    import sys
    from io import StringIO
    
    complex_data = {
        'messages': [
            {'topic': 'events', 'partition': 0, 'offset': 123},
            {'topic': 'events', 'partition': 1, 'offset': 456}
        ],
        'metadata': {
            'timestamp': '2025-10-21T12:00:00Z',
            'producer_id': 'test-producer'
        }
    }
    
    # Test pretty formatting
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        _echo(complex_data, json_out=True, pretty_json=True)
        pretty_output = sys.stdout.getvalue()
        
        # Reset capture
        sys.stdout = StringIO()
        
        _echo(complex_data, json_out=True, pretty_json=False)
        compact_output = sys.stdout.getvalue()
        
        # Pretty output should have indentation and newlines
        assert '  "messages"' in pretty_output
        assert '\n' in pretty_output
        
        # Compact output should be on single line with no extra spaces
        assert '"messages":[' in compact_output
        assert compact_output.count('\n') == 1  # Only the final newline
        
    finally:
        sys.stdout = old_stdout