"""Test suite for JSON file producer functionality."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from klient import __main__


class TestJsonFileProducer:
    """Test JSON file producer command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.test_config = {
            'bootstrap_servers': 'localhost:9092',
            'security_protocol': 'PLAINTEXT',
        }

    def create_temp_json_file(self, data):
        """Helper to create temporary JSON file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f)
            return path
        except Exception:
            os.close(fd)
            raise

    def test_produce_from_json_array_success(self):
        """Test successful message production from JSON array."""
        test_data = [
            {"id": 1, "message": "hello", "status": "active"},
            {"id": 2, "message": "world", "status": "inactive"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file
                ])
                
                assert result.exit_code == 0
                assert 'sent' in result.output
                assert 'test-topic' in result.output
                assert '2' in result.output  # message count
                
                # Verify producer calls
                assert mock_producer.produce.call_count == 2
                mock_producer.flush.assert_called_once()
                mock_producer.close.assert_called_once()
        finally:
            os.unlink(json_file)

    def test_produce_with_key_field_extraction(self):
        """Test message production with key field extraction."""
        test_data = [
            {"user_id": "user1", "data": "message1"},
            {"user_id": "user2", "data": "message2"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file,
                    '--key-field', 'user_id'
                ])
                
                assert result.exit_code == 0
                
                # Check that produce was called with keys
                calls = mock_producer.produce.call_args_list
                assert len(calls) == 2
                assert calls[0][1]['key'] == 'user1'
                assert calls[1][1]['key'] == 'user2'
                
                # Verify that key field was removed from message value
                value1 = json.loads(calls[0][1]['value'])
                value2 = json.loads(calls[1][1]['value'])
                assert 'user_id' not in value1
                assert 'user_id' not in value2
                assert value1['data'] == 'message1'
                assert value2['data'] == 'message2'
        finally:
            os.unlink(json_file)

    def test_produce_with_partition_field_extraction(self):
        """Test message production with partition field extraction."""
        test_data = [
            {"shard": 0, "data": "message1"},
            {"shard": 1, "data": "message2"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file,
                    '--partition-field', 'shard'
                ])
                
                assert result.exit_code == 0
                
                # Check that produce was called with correct partitions
                calls = mock_producer.produce.call_args_list
                assert len(calls) == 2
                assert calls[0][1]['partition'] == 0
                assert calls[1][1]['partition'] == 1
        finally:
            os.unlink(json_file)

    def test_produce_with_headers_field_extraction(self):
        """Test message production with headers field extraction."""
        test_data = [
            {"headers": {"type": "event", "version": "1.0"}, "data": "message1"},
            {"headers": {"type": "command", "version": "2.0"}, "data": "message2"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file,
                    '--headers-field', 'headers'
                ])
                
                assert result.exit_code == 0
                
                # Check that produce was called with correct headers
                calls = mock_producer.produce.call_args_list
                assert len(calls) == 2
                assert calls[0][1]['headers'] == {"type": "event", "version": "1.0"}
                assert calls[1][1]['headers'] == {"type": "command", "version": "2.0"}
        finally:
            os.unlink(json_file)

    def test_produce_with_transactional_mode(self):
        """Test message production in transactional mode with batching."""
        test_data = [{"id": i, "data": f"message{i}"} for i in range(5)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file,
                    '--transactional-id', 'tx-test',
                    '--batch-size', '2'
                ])
                
                assert result.exit_code == 0
                
                # Verify transaction handling
                assert mock_producer.begin_transaction.call_count >= 1
                assert mock_producer.commit_transaction.call_count >= 1
                assert mock_producer.produce.call_count == 5
        finally:
            os.unlink(json_file)

    def test_invalid_json_file_error(self):
        """Test error handling for invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content')  # Invalid JSON
            json_file = f.name

        try:
            result = self.runner.invoke(__main__.cli, [
                '--bootstrap-servers', 'localhost:9092',
                'produce', 'from-file', 'test-topic', json_file
            ])
            
            assert result.exit_code == 1
            assert 'Invalid JSON' in result.output
        finally:
            os.unlink(json_file)

    def test_non_array_json_error(self):
        """Test error handling for JSON that is not an array."""
        test_data = {"single": "object"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            result = self.runner.invoke(__main__.cli, [
                '--bootstrap-servers', 'localhost:9092',
                'produce', 'from-file', 'test-topic', json_file
            ])
            
            assert result.exit_code == 1
            assert 'must contain an array' in result.output
        finally:
            os.unlink(json_file)

    def test_empty_array_handling(self):
        """Test handling of empty JSON array."""
        test_data = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            result = self.runner.invoke(__main__.cli, [
                '--bootstrap-servers', 'localhost:9092',
                'produce', 'from-file', 'test-topic', json_file
            ])
            
            assert result.exit_code == 1
            assert 'empty array' in result.output
        finally:
            os.unlink(json_file)

    def test_non_object_array_elements_warning(self):
        """Test handling of array elements that are not objects."""
        test_data = [
            {"valid": "object"},
            "invalid_string",
            42,
            {"another_valid": "object"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file
                ])
                
                assert result.exit_code == 0
                # Should only process the valid objects (2 out of 4)
                assert mock_producer.produce.call_count == 2
        finally:
            os.unlink(json_file)

    def test_missing_file_error(self):
        """Test error handling for missing file."""
        result = self.runner.invoke(__main__.cli, [
            '--bootstrap-servers', 'localhost:9092',
            'produce', 'from-file', 'test-topic', '/nonexistent/file.json'
        ])
        
        assert result.exit_code == 2  # Click file validation error
        assert 'does not exist' in result.output

    def test_invalid_partition_value_handling(self):
        """Test handling of invalid partition values."""
        test_data = [
            {"partition": "not_a_number", "data": "message1"},
            {"partition": 1, "data": "message2"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            with patch('klient.__main__.build_producer') as mock_build_producer:
                mock_producer = MagicMock()
                mock_build_producer.return_value = mock_producer
                
                result = self.runner.invoke(__main__.cli, [
                    '--bootstrap-servers', 'localhost:9092',
                    'produce', 'from-file', 'test-topic', json_file,
                    '--partition-field', 'partition'
                ])
                
                assert result.exit_code == 0
                
                # Check that first message has no partition (invalid), second has partition 1
                calls = mock_producer.produce.call_args_list
                assert len(calls) == 2
                assert calls[0][1]['partition'] is None
                assert calls[1][1]['partition'] == 1
        finally:
            os.unlink(json_file)