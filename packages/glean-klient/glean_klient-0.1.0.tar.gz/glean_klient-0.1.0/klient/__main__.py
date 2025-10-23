"""glean-kafka CLI entrypoint for `python -m klient`.

This file contains the full Click-based command-line interface previously in
`main.py`. The standalone `main.py` has been removed in favor of the package
module entrypoint pattern.

Commands are grouped into: admin, produce, consume, load, info.

Environment config usage is OPTIONAL. If no `~/.kafka/config.json` or per-env
file exists we fall back to `localhost:9092` or a `--bootstrap-servers` override.
Config files must only contain connection/client properties (e.g. security,
timeouts, compression) and must never include application topic names.
"""
from __future__ import annotations

import json
import sys
import asyncio
import typing as t

import click

from klient import (
    KafkaConsumer,
    KafkaProducer,
    KafkaAdmin,
    ConsumerConfig,
    ProducerConfig,
    AdminConfig,
    KafkaConsumerError,
    KafkaProducerError,
    KafkaAdminError,
    KafkaTransactionError,
    resolve_env_config,
    split_env_config,
    extract_bootstrap,
)


# ---------- Common Helpers ----------

import re

def _apply_filter(data: t.Any, filter_pattern: str, is_json: bool) -> t.Any:
    """Apply filtering to data based on pattern.
    
    Args:
        data: Data to filter
        filter_pattern: Filter pattern (regex for text, "key:regex" for JSON)
        is_json: Whether data should be treated as JSON
        
    Returns:
        Filtered data or None if no matches
    """
    if not filter_pattern:
        return data
        
    if is_json and isinstance(data, (dict, list)):
        return _filter_json(data, filter_pattern)
    else:
        return _filter_text(str(data), filter_pattern)

def _filter_json(data: t.Any, pattern: str) -> t.Any:
    """Filter JSON data using key:regex pattern or simple regex."""
    if ':' in pattern:
        # Key-specific filtering: "key:regex"
        key_name, regex_pattern = pattern.split(':', 1)
        try:
            regex = re.compile(regex_pattern, re.IGNORECASE)
            return _filter_by_key(data, key_name.strip(), regex)
        except re.error as e:
            click.echo(f"Invalid regex pattern '{regex_pattern}': {e}", err=True)
            return data
    else:
        # Apply regex to entire JSON string
        json_str = json.dumps(data, default=str)
        return _filter_text(json_str, pattern)

def _filter_by_key(data: t.Any, key_name: str, regex: re.Pattern) -> t.Any:
    """Filter JSON data by matching regex against specific key values."""
    if isinstance(data, dict):
        # Filter dictionary entries
        filtered = {}
        for k, v in data.items():
            if k == key_name:
                # Check if this key's value matches the pattern
                value_str = str(v)
                if regex.search(value_str):
                    filtered[k] = v
            elif isinstance(v, (dict, list)):
                # Recursively filter nested structures
                nested_result = _filter_by_key(v, key_name, regex)
                if nested_result is not None:
                    filtered[k] = nested_result
            else:
                # Keep non-matching keys if they don't match the target key
                if k != key_name:
                    filtered[k] = v
        return filtered if filtered else None
    elif isinstance(data, list):
        # Filter list items
        filtered = []
        for item in data:
            result = _filter_by_key(item, key_name, regex)
            if result is not None:
                filtered.append(result)
        return filtered if filtered else None
    else:
        return data

def _filter_text(text: str, pattern: str) -> t.Optional[str]:
    """Filter text using regex pattern."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        # Return original text if it matches, None otherwise
        return text if regex.search(text) else None
    except re.error as e:
        click.echo(f"Invalid regex pattern '{pattern}': {e}", err=True)
        return text

def _ctx_echo(ctx, data: t.Any):
    """Echo data using context settings for output formatting and file destination."""
    _echo(data, ctx.obj['json'], ctx.obj['output_file'], ctx.obj['pretty_json'], ctx.obj['filter_pattern'])

def _format_output(data: t.Any, json_out: bool, pretty_json: bool = True, filter_pattern: t.Optional[str] = None) -> str:
    """Format data for output without printing. Returns formatted string."""
    # Apply filtering if pattern is provided
    if filter_pattern:
        data = _apply_filter(data, filter_pattern, json_out or isinstance(data, (dict, list)))
        
        # If filtering results in no data, return empty string
        if data is None:
            return ""
    
    if json_out or isinstance(data, (dict, list)):
        # JSON output
        if pretty_json:
            return json.dumps(data, indent=2, sort_keys=True, default=str)
        else:
            return json.dumps(data, separators=(',', ':'), default=str)
    else:
        # String output
        return str(data)

def _echo(data: t.Any, json_out: bool, output_file: t.Optional[str] = None, pretty_json: bool = True, filter_pattern: t.Optional[str] = None):
    """Output data to stdout or file with optional JSON formatting and filtering.
    
    Args:
        data: Data to output
        json_out: Force JSON output format
        output_file: Optional file path to write output (None for stdout)
        pretty_json: Whether to format JSON with indentation (default True)
        filter_pattern: Optional regex filter or "key:regex" for JSON filtering
    """
    output_text = _format_output(data, json_out, pretty_json, filter_pattern)
    
    # If filtering results in no data, don't output anything
    if not output_text:
        return
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text + '\n')
            click.echo(f"Output written to {output_file}", err=True)
        except IOError as e:
            click.echo(f"Failed to write to {output_file}: {e}", err=True)
            sys.exit(1)
    else:
        click.echo(output_text)


def build_admin(bootstrap: str, ctx_obj: t.Dict[str, t.Any]) -> KafkaAdmin:
    addl = dict(ctx_obj.get('env_admin') or {})
    addl.pop('bootstrap.servers', None)
    return KafkaAdmin(AdminConfig(bootstrap_servers=bootstrap, additional_config=addl))


def build_consumer(bootstrap: str, group: str, isolation: str, auto_commit: bool, ctx_obj: t.Dict[str, t.Any]) -> KafkaConsumer:
    addl = dict(ctx_obj.get('env_consumer') or {})
    env_group = addl.get('group.id')
    if env_group and group == 'cli-consumer':
        group = env_group
    for k in ['bootstrap.servers', 'group.id']:
        addl.pop(k, None)
    return KafkaConsumer(ConsumerConfig(
        bootstrap_servers=bootstrap,
        group_id=group,
        isolation_level=isolation,
        enable_auto_commit=auto_commit,
        additional_config=addl,
    ))


def build_producer(bootstrap: str, transactional_id: t.Optional[str], ctx_obj: t.Dict[str, t.Any]) -> KafkaProducer:
    addl = dict(ctx_obj.get('env_producer') or {})
    if not transactional_id and 'transactional.id' in addl:
        transactional_id = addl['transactional.id']
    for k in ['bootstrap.servers', 'transactional.id']:
        addl.pop(k, None)
    return KafkaProducer(ProducerConfig(
        bootstrap_servers=bootstrap,
        transactional_id=transactional_id,
        additional_config=addl,
    ))


class AsyncRunner:
    """Utility to run async functions inside click sync commands if needed."""
    @staticmethod
    def run(coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:
            # Already inside event loop (e.g. in some environments)
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)


# (Env config helpers now sourced from klient.__init__ utilities: resolve_env_config, split_env_config, extract_bootstrap)


def _show_kafka_config(ctx_obj: t.Dict[str, t.Any], command_info: t.Optional[t.Dict[str, t.Any]] = None):
    """Display all relevant Kafka configuration and connection details."""
    click.echo("=" * 60, err=True)
    click.echo("KAFKA CONFIGURATION", err=True) 
    click.echo("=" * 60, err=True)
    
    # Connection settings
    click.echo(f"Bootstrap Servers: {ctx_obj['bootstrap']}", err=True)
    if ctx_obj.get('env'):
        click.echo(f"Global Environment: {ctx_obj['env']}", err=True)
    
    # Environment-specific configurations
    env_configs = {
        'Producer Environment': ctx_obj.get('producer_env'),
        'Consumer Environment': ctx_obj.get('consumer_env'), 
        'Admin Environment': ctx_obj.get('admin_env'),
    }
    
    for role, env_name in env_configs.items():
        if env_name:
            click.echo(f"{role}: {env_name}", err=True)
    
    # Command-specific info if provided
    if command_info:
        click.echo("\nCOMMAND DETAILS:", err=True)
        click.echo("-" * 20, err=True)
        for key, value in command_info.items():
            if value is not None:
                click.echo(f"{key.replace('_', ' ').title()}: {value}", err=True)
    
    # Raw configuration sections
    click.echo("\nCONFIGURATION SECTIONS:", err=True)
    click.echo("-" * 25, err=True)
    
    config_sections = {
        'Producer Config': ctx_obj.get('env_producer', {}),
        'Consumer Config': ctx_obj.get('env_consumer', {}),
        'Admin Config': ctx_obj.get('env_admin', {}),
    }
    
    for section_name, config in config_sections.items():
        if config:
            click.echo(f"\n{section_name}:", err=True)
            for key, value in sorted(config.items()):
                # Mask sensitive values
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                    value = "***MASKED***"
                click.echo(f"  {key}: {value}", err=True)
        else:
            click.echo(f"\n{section_name}: (empty/default)", err=True)
    
    # Available environments in config file
    raw_config = ctx_obj.get('env_config_raw', {})
    if isinstance(raw_config, dict) and len(raw_config) > 1:
        available_envs = [k for k in raw_config.keys() if k != 'default']
        if available_envs:
            click.echo(f"\nAvailable Environments: {', '.join(sorted(available_envs))}", err=True)
    
    click.echo("=" * 60, err=True)
    click.echo("", err=True)  # Empty line separator


# ---------- Root CLI ----------

@click.group()
@click.option('--bootstrap-servers', '-b', default=None, help='Kafka bootstrap servers (overrides config file).')
@click.option('--env', '-e', default=None, help='Global environment name (default + env merge from single config file).')
@click.option('--producer-env', default=None, help='Environment name for producer settings (e.g. prod-producer).')
@click.option('--consumer-env', default=None, help='Environment name for consumer settings (e.g. prod-consumer).')
@click.option('--admin-env', default=None, help='Environment name for admin settings (e.g. prod-admin).')
@click.option('--config-file', '-C', type=click.Path(exists=True, dir_okay=False, readable=True), default=None,
              help='Explicit Kafka JSON config file (single file containing default + env sections).')
@click.option('--json', 'json_out', is_flag=True, help='Output JSON where applicable.')
@click.option('--output-file', '-o', type=click.Path(dir_okay=False, writable=True), default=None,
              help='Write output to file instead of stdout.')
@click.option('--pretty-json/--compact-json', default=True, 
              help='Format JSON output with indentation (default: pretty).')
@click.option('--filter', '-f', 'filter_pattern', type=str, default=None,
              help='Filter output with regex. For JSON: use "key:regex" to filter by specific key.')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
@click.option('--show-config', is_flag=True, help='Display all Kafka configuration before executing command.')
@click.pass_context
def cli(ctx, bootstrap_servers: t.Optional[str], env: t.Optional[str], producer_env: t.Optional[str], consumer_env: t.Optional[str], admin_env: t.Optional[str], config_file: t.Optional[str], json_out: bool, output_file: t.Optional[str], pretty_json: bool, filter_pattern: t.Optional[str], verbose: bool, show_config: bool):
    """glean-kafka CLI using a SINGLE config file (default + named envs).

    Role-specific environment overrides can be supplied via --producer-env / --consumer-env / --admin-env.
    Each role env is merged with `default` in the config file (env values override defaults). If a role env
    is omitted, the global --env (if provided) is used. If neither is specified, only the `default` section
    (or raw file) applies.
    """
    ctx.ensure_object(dict)
    # Load full raw mapping once
    combined_raw = resolve_env_config(None, config_file)  # returns default or full mapping
    # Helper to derive role-specific merged config
    def _role_env(name: t.Optional[str]) -> t.Dict[str, t.Any]:
        if name:
            # Re-run resolver with env to get merged default + env
            return resolve_env_config(name, config_file)
        if env:
            return resolve_env_config(env, config_file)
        return combined_raw
    prod_raw = _role_env(producer_env)
    cons_raw = _role_env(consumer_env)
    adm_raw = _role_env(admin_env)

    # split sections for each role independently
    prod_cfg_raw, _, _ = split_env_config(prod_raw)
    _, cons_cfg_raw, _ = split_env_config(cons_raw)
    _, _, adm_cfg_raw = split_env_config(adm_raw)
    effective_bootstrap = bootstrap_servers or extract_bootstrap([prod_cfg_raw, cons_cfg_raw, adm_cfg_raw]) or 'localhost:9092'
    ctx.obj.update({
        'bootstrap': effective_bootstrap,
        'json': json_out,
        'output_file': output_file,
        'pretty_json': pretty_json,
        'filter_pattern': filter_pattern,
        'verbose': verbose,
        'env': env,
        'env_config_raw': combined_raw,
        'env_producer': prod_cfg_raw,
        'env_consumer': cons_cfg_raw,
        'env_admin': adm_cfg_raw,
        'producer_env': producer_env,
        'consumer_env': consumer_env,
        'admin_env': admin_env,
        'show_config': show_config,
    })
    if verbose and combined_raw:
        click.echo(f"[env-config] available envs: {', '.join([k for k in combined_raw.keys() if k != 'default'])}")


# ---------- Admin Commands ----------

@cli.group()
@click.pass_context
def admin(ctx):
    """Administrative operations (topics, cluster)."""


@admin.command('list-topics')
@click.pass_context
def list_topics(ctx):
    # Show configuration if requested
    if ctx.obj.get('show_config'):
        command_info = {
            'command': 'admin list-topics'
        }
        _show_kafka_config(ctx.obj, command_info)
    
    admin_client = build_admin(ctx.obj['bootstrap'], ctx.obj)
    try:
        topics = admin_client.list_topics()
        _ctx_echo(ctx, topics)
    except KafkaAdminError as e:
        click.echo(f"Error listing topics: {e}", err=True)
        sys.exit(1)


@admin.command('describe-topic')
@click.argument('topic')
@click.pass_context
def describe_topic(ctx, topic: str):
    admin_client = build_admin(ctx.obj['bootstrap'], ctx.obj)
    try:
        details = admin_client.describe_topics([topic])
        if topic in details:
            info = details[topic]
            out = {
                'name': info.name,
                'partitions': info.partitions,
                'replication_factor': info.replication_factor,
                'config': info.config,
            }
            _ctx_echo(ctx, out)
        else:
            click.echo(f"Topic '{topic}' not found", err=True)
            sys.exit(2)
    except KafkaAdminError as e:
        click.echo(f"Error describing topic: {e}", err=True)
        sys.exit(1)


@admin.command('create-topic')
@click.argument('name')
@click.option('--partitions', '-p', type=int, default=1, show_default=True)
@click.option('--replication', '-r', type=int, default=1, show_default=True)
@click.option('--config', '-c', multiple=True, help='Topic config entries key=value (repeat).')
@click.pass_context
def create_topic(ctx, name: str, partitions: int, replication: int, config: t.Tuple[str, ...]):
    admin_client = build_admin(ctx.obj['bootstrap'], ctx.obj)
    cfg_dict = {}
    for entry in config:
        if '=' not in entry:
            click.echo(f"Invalid config entry '{entry}' - expected key=value", err=True)
            sys.exit(2)
        k, v = entry.split('=', 1)
        cfg_dict[k] = v
    from klient import TopicMetadata
    try:
        result = admin_client.create_topics([
            TopicMetadata(name=name, partitions=partitions, replication_factor=replication, config=cfg_dict)
        ])
        success = result.get(name)
        _ctx_echo(ctx, {'topic': name, 'created': success})
    except KafkaAdminError as e:
        click.echo(f"Error creating topic: {e}", err=True)
        sys.exit(1)


@admin.command('delete-topic')
@click.argument('name')
@click.pass_context
def delete_topic(ctx, name: str):
    admin_client = build_admin(ctx.obj['bootstrap'], ctx.obj)
    try:
        result = admin_client.delete_topics([name])
        _ctx_echo(ctx, {'topic': name, 'deleted': result.get(name)})
    except KafkaAdminError as e:
        click.echo(f"Error deleting topic: {e}", err=True)
        sys.exit(1)


@admin.command('cluster-metadata')
@click.pass_context
def cluster_metadata(ctx):
    admin_client = build_admin(ctx.obj['bootstrap'], ctx.obj)
    try:
        meta = admin_client.get_cluster_metadata()
        _ctx_echo(ctx, meta)
    except KafkaAdminError as e:
        click.echo(f"Error fetching cluster metadata: {e}", err=True)
        sys.exit(1)


# ---------- Produce Commands ----------

@cli.group()
@click.pass_context
def produce(ctx):
    """Produce messages (sync & transactional)."""


def _parse_headers(header_items: t.Tuple[str, ...]) -> t.Dict[str, str]:
    headers: t.Dict[str, str] = {}
    for itm in header_items:
        if '=' not in itm:
            raise click.ClickException(f"Invalid header '{itm}' - expected key=value")
        k, v = itm.split('=', 1)
        headers[k] = v
    return headers


@produce.command('send')
@click.argument('topic')
@click.option('--key', '-k', default=None)
@click.option('--value', '-v', required=True)
@click.option('--header', '-H', multiple=True, help='Header key=value (repeat).')
@click.option('--partition', '-p', type=int, default=None)
@click.option('--flush/--no-flush', default=True, show_default=True)
@click.option('--transactional-id', '--tx-id', default=None, help='Transactional ID to enable transactions.')
@click.pass_context
def produce_send(ctx, topic, key, value, header, partition, flush, transactional_id):
    # Show configuration if requested
    if ctx.obj.get('show_config'):
        command_info = {
            'command': 'produce send',
            'topic': topic,
            'key': key,
            'value': value[:100] + '...' if value and len(value) > 100 else value,
            'headers': ', '.join([f"{k}={v}" for k, v in _parse_headers(header).items()]) if header else None,
            'partition': partition,
            'flush': flush,
            'transactional_id': transactional_id,
        }
        _show_kafka_config(ctx.obj, command_info)
    
    headers_raw = _parse_headers(header)
    # Normalize header values to bytes for strict typing compatibility
    from typing import Union, Dict, cast
    headers_mixed: Dict[str, Union[str, bytes]] = {k: (v if isinstance(v, str) else v) for k, v in headers_raw.items()}
    headers = cast(Dict[str, Union[str, bytes]], headers_mixed)
    producer = build_producer(ctx.obj['bootstrap'], transactional_id, ctx.obj)
    try:
        if transactional_id:
            producer.begin_transaction()
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            headers=headers,
            partition=partition,
            flush=flush,
        )
        if transactional_id:
            producer.commit_transaction()
        _ctx_echo(ctx, {'status': 'sent', 'topic': topic, 'transactional': bool(transactional_id)})
    except (KafkaProducerError, KafkaTransactionError) as e:
        if transactional_id and producer.in_transaction:
            try:
                producer.abort_transaction()
            except Exception:  # noqa
                pass
        click.echo(f"Produce failed: {e}", err=True)
        sys.exit(1)
    finally:
        producer.close()


@produce.command('transaction')
@click.argument('topic')
@click.option('--count', '-n', type=int, default=5, show_default=True, help='Messages in transactional batch.')
@click.option('--transactional-id', '--tx-id', required=True)
@click.pass_context
def produce_transaction(ctx, topic: str, count: int, transactional_id: str):
    producer = build_producer(ctx.obj['bootstrap'], transactional_id, ctx.obj)
    try:
        producer.begin_transaction()
        for i in range(count):
            producer.produce(
                topic=topic,
                key=f"key-{i}",
                value=f"Transactional message {i}",
                headers={'batch': 'tx', 'index': str(i)},
                flush=False,
            )
        commit_res = producer.commit_transaction()
        _ctx_echo(ctx, {'transaction': transactional_id, 'committed': True, 'duration_ms': commit_res.duration_ms})
    except KafkaTransactionError as e:
        click.echo(f"Transaction failed: {e}", err=True)
        if producer.in_transaction:
            try:
                producer.abort_transaction()
            except Exception:  # noqa
                pass
        sys.exit(1)
    finally:
        producer.close()


@produce.command('from-file')
@click.argument('topic')
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('--transactional-id', '--tx-id', default=None, help='Transactional ID to enable transactions.')
@click.option('--batch-size', '-b', type=int, default=100, show_default=True,
              help='Number of messages to send before committing transaction (transactional mode only).')
@click.option('--key-field', default=None, 
              help='JSON field name to use as message key (optional).')
@click.option('--partition-field', default=None,
              help='JSON field name to use as partition number (optional).')
@click.option('--headers-field', default=None,
              help='JSON field name containing headers as key-value object (optional).')
@click.pass_context
def produce_from_file(ctx, topic: str, json_file: str, transactional_id: t.Optional[str], 
                     batch_size: int, key_field: t.Optional[str], partition_field: t.Optional[str], 
                     headers_field: t.Optional[str]):
    """Produce messages from a JSON file containing an array of message objects.
    
    The JSON file should contain an array of objects: [{"field": "value"}, {"field": "value2"}]
    
    Each object in the array becomes a separate Kafka message. By default, the entire object 
    is serialized as the message value. Use --key-field, --partition-field, and --headers-field
    to extract specific fields for those message properties.
    
    Examples:
      python -m klient produce from-file events messages.json
      python -m klient produce from-file events data.json --key-field id --partition-field shard
      python -m klient produce from-file events batch.json --transactional-id tx-1 --batch-size 50
    """
    # Show configuration if requested
    if ctx.obj.get('show_config'):
        command_info = {
            'command': 'produce from-file',
            'topic': topic,
            'json_file': json_file,
            'transactional_id': transactional_id,
            'batch_size': batch_size,
            'key_field': key_field,
            'partition_field': partition_field,
            'headers_field': headers_field,
        }
        _show_kafka_config(ctx.obj, command_info)
    
    try:
        # Read and parse JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                click.echo(f"Invalid JSON in file {json_file}: {e}", err=True)
                sys.exit(1)
        
        # Validate that data is an array
        if not isinstance(data, list):
            click.echo(f"JSON file must contain an array of objects, got {type(data).__name__}", err=True)
            sys.exit(1)
            
        if not data:
            click.echo("JSON file contains empty array, nothing to send", err=True)
            sys.exit(1)
            
        producer = build_producer(ctx.obj['bootstrap'], transactional_id, ctx.obj)
        
        try:
            message_count = 0
            batch_count = 0
            
            for i, message_data in enumerate(data):
                if not isinstance(message_data, dict):
                    click.echo(f"Message at index {i} is not an object: {type(message_data).__name__}", err=True)
                    continue
                
                # Start transaction if needed
                if transactional_id and batch_count == 0:
                    producer.begin_transaction()
                
                # Extract message components
                key = message_data.pop(key_field, None) if key_field else None
                partition = message_data.pop(partition_field, None) if partition_field else None
                headers_data = message_data.pop(headers_field, None) if headers_field else None
                
                # Convert partition to int if provided
                if partition is not None:
                    try:
                        partition = int(partition)
                    except (ValueError, TypeError):
                        click.echo(f"Invalid partition value at index {i}: {partition}", err=True)
                        partition = None
                
                # Process headers
                headers: t.Optional[t.Dict[str, t.Union[str, bytes]]] = None
                if headers_data and isinstance(headers_data, dict):
                    headers = {str(k): str(v) for k, v in headers_data.items()}
                
                # Use remaining data as message value
                value = json.dumps(message_data, default=str)
                
                # Send message
                producer.produce(
                    topic=topic,
                    key=str(key) if key is not None else None,
                    value=value,
                    headers=headers,
                    partition=partition,
                    flush=False,
                )
                
                message_count += 1
                batch_count += 1
                
                # Handle batch commits for transactions
                if transactional_id and batch_count >= batch_size:
                    producer.commit_transaction()
                    batch_count = 0
            
            # Final transaction commit if needed
            if transactional_id and batch_count > 0:
                producer.commit_transaction()
            
            # Flush all messages
            producer.flush()
            
            _ctx_echo(ctx, {
                'status': 'sent', 
                'topic': topic, 
                'messages': message_count,
                'source_file': json_file,
                'transactional': bool(transactional_id)
            })
            
        except (KafkaProducerError, KafkaTransactionError) as e:
            if transactional_id and producer.in_transaction:
                try:
                    producer.abort_transaction()
                except Exception:  # noqa
                    pass
            click.echo(f"Failed to send messages from {json_file}: {e}", err=True)
            sys.exit(1)
        finally:
            producer.close()
            
    except IOError as e:
        click.echo(f"Failed to read file {json_file}: {e}", err=True)
        sys.exit(1)


# ---------- Consume Commands ----------
@cli.group()
@click.pass_context
def consume(ctx):
    """Consume messages.

    Provides poll, batch, and stream subcommands (see `consume --help`).
    """

@cli.group()
@click.pass_context
def relay(ctx):
    """Relay messages from a source topic to a target topic with optional transformation.

    The stream variant performs continuous consumption from the source, buffering up to a batch size,
    then producing a transactional batch to the target topic. Graceful shutdown semantics mirror
    the consumer stream command (SIGINT/SIGTERM initiate a configurable grace period).
    """

@relay.command('stream')
@click.argument('source_topic')
@click.argument('target_topic')
@click.option('--group', '-g', default='cli-relay', show_default=True, help='Consumer group id for source consumption.')
@click.option('--transactional-id', '--tx-id', default='cli-relay-tx', show_default=True, help='Transactional id for producer batches.')
@click.option('--batch-size', '-b', type=int, default=25, show_default=True, help='Messages per transactional batch.')
@click.option('--max-batches', type=int, default=None, help='Optional maximum number of committed batches before exiting (testing / bounded runs).')
@click.option('--max-in-flight', type=int, default=1, show_default=True, help='Maximum concurrent in-flight transactions (1 for sequential).')
@click.option('--timeout', '-t', type=float, default=0.5, show_default=True, help='Per-poll timeout seconds.')
@click.option('--grace-period', type=float, default=2.0, show_default=True, help='Seconds to wait after shutdown signal before exit.')
@click.option('--isolation', type=click.Choice(['read_committed', 'read_uncommitted']), default='read_committed', help='Isolation level for source consumption.')
@click.option('--transform', '-x', default=None, help='Optional Python expression applied to message value (available name: value).')
@click.pass_context
def relay_stream(ctx, source_topic: str, target_topic: str, group: str, transactional_id: str, batch_size: int, max_in_flight: int, timeout: float, grace_period: float, isolation: str, transform: t.Optional[str], max_batches: t.Optional[int]):
    """Continuous transactional relay from source_topic to target_topic.

    Transformation: if --transform is provided it is evaluated for each message with `value` bound
    to the decoded string value (UTF-8). The result (string) is re-encoded as UTF-8 for output.
    Use carefully—expression is executed via eval.
    """
    consumer = build_consumer(ctx.obj['bootstrap'], group, isolation, auto_commit=False, ctx_obj=ctx.obj)
    consumer.subscribe([source_topic])
    producer = build_producer(ctx.obj['bootstrap'], transactional_id, ctx.obj)

    import time
    import signal
    import json
    from .metrics import inc
    shutdown_requested = False
    start_time = time.time()
    batch: t.List[t.Any] = []
    committed_batches = 0

    def _signal_handler(signum, frame):  # noqa
        nonlocal shutdown_requested
        if not shutdown_requested:
            shutdown_requested = True
            inc('consumer.shutdown.signal')
            click.echo(json.dumps({'event':'shutdown_requested','signal':signum,'source':source_topic,'target':target_topic}))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _signal_handler)
        except Exception:  # noqa
            pass

    try:
        while True:
            if shutdown_requested:
                if (time.time() - start_time) >= grace_period:
                    break
                time.sleep(min(0.05, grace_period))
                continue
            msg = consumer.poll_message(timeout=timeout)
            if msg:
                batch.append(msg)
                if len(batch) >= batch_size:
                    # Process transactional batch
                    try:
                        producer.begin_transaction()
                        for m in batch:
                            raw_val = m.value.decode() if m.value else ''
                            if transform:
                                # Unsafe eval by design for CLI; user assumes risk
                                local_env = {'value': raw_val}
                                try:
                                    new_val = eval(transform, {}, local_env)  # noqa: S307
                                except Exception as e:
                                    raise KafkaProducerError(f'transform expression failed: {e}')
                                if not isinstance(new_val, str):
                                    new_val = str(new_val)
                                out_bytes = new_val.encode()
                            else:
                                out_bytes = raw_val.encode() if isinstance(raw_val, str) else m.value
                            producer.produce(topic=target_topic, key=m.key.decode() if m.key else None, value=out_bytes, flush=False)
                        commit_res = producer.commit_transaction()
                        inc('relay.batch.commit')
                        inc('relay.messages.forwarded', len(batch))
                        consumer.commit()  # commit offsets post successful transaction
                        click.echo(json.dumps({'event':'relay_batch_committed','count':len(batch),'duration_ms':commit_res.duration_ms}))
                        committed_batches += 1
                        if max_batches and committed_batches >= max_batches:
                            break
                    except KafkaTransactionError as e:
                        click.echo(json.dumps({'event':'relay_batch_aborted','error':str(e),'count':len(batch)}))
                        try:
                            if producer.in_transaction:
                                producer.abort_transaction()
                        except Exception:  # noqa
                            pass
                    finally:
                        batch.clear()
            else:
                # If a max_batches limit has been reached we can exit early
                if max_batches and committed_batches >= max_batches:
                    break
                time.sleep(0.01)
    except KafkaConsumerError as e:
        click.echo(f"Relay error: {e}", err=True)
        sys.exit(1)
    finally:
        try:
            consumer.stop()
        except Exception:  # noqa
            pass
        try:
            producer.close()
        except Exception:  # noqa
            pass
        duration = time.time() - start_time
        inc('consumer.shutdown.complete')
        click.echo(json.dumps({'event':'relay_stream_ended','source':source_topic,'target':target_topic,'duration_s':round(duration,3)}))
    """Consume messages.

    Modes:
      poll   Perform a single poll attempt and exit (returns at most one message).
      batch  Fetch up to N messages in one consume call then exit.
      stream Continuous polling until a limit is reached or interrupted (Ctrl+C).

    All modes support an --isolation level for transactional consumption semantics.
    """

@consume.command('poll')
@click.argument('topic')
@click.option('--group', '-g', default='cli-consumer', show_default=True,
              help='Consumer group id. Default is a throwaway group; override to maintain offsets.')
@click.option('--timeout', '-t', type=float, default=5.0, show_default=True,
              help='Max seconds to wait for a single message before returning none.')
@click.option('--isolation', type=click.Choice(['read_committed', 'read_uncommitted']), default='read_committed',
              help='read_committed hides uncommitted transactional messages; read_uncommitted shows all.')
@click.option('--seek-to-offset', type=int, help='Offset to seek to before consuming (seeks all partitions unless --seek-to-partition specified)')
@click.option('--seek-to-partition', type=int, help='Specific partition to seek within (optional, defaults to all partitions)')
@click.pass_context
def consume_poll(ctx, topic: str, group: str, timeout: float, isolation: str, seek_to_offset: int, seek_to_partition: int):
    """Single-shot poll.

    Attempts to retrieve exactly one message within --timeout seconds.
    If no message arrives in that window, prints {'message': None} and exits with code 0.

    Examples:
      python -m klient consume poll my-topic
      python -m klient consume poll my-topic -t 1.5 --group analytics-read
      python -m klient consume poll my-topic --seek-to-offset 1000  # seeks all partitions
      python -m klient consume poll my-topic --seek-to-offset 1000 --seek-to-partition 0  # specific partition
    """
    # Validate seek options (partition can be specified without offset but not the reverse)
    if seek_to_partition is not None and seek_to_offset is None:
        click.echo("Error: --seek-to-partition requires --seek-to-offset", err=True)
        sys.exit(2)
    
    # Show configuration if requested
    if ctx.obj.get('show_config'):
        command_info = {
            'command': 'consume poll',
            'topic': topic,
            'consumer_group': group,
            'timeout': timeout,
            'isolation_level': isolation,
            'seek_to_offset': seek_to_offset,
            'seek_to_partition': seek_to_partition,
        }
        _show_kafka_config(ctx.obj, command_info)
    
    consumer = build_consumer(ctx.obj['bootstrap'], group, isolation, auto_commit=True, ctx_obj=ctx.obj)
    consumer.subscribe([topic])
    
    # Perform seek if requested
    if seek_to_offset is not None:
        try:
            consumer.seek_to_offset(topic, seek_to_offset, seek_to_partition)
        except KafkaConsumerError as e:
            click.echo(f"Seek failed: {e}", err=True)
            sys.exit(1)
    
    try:
        msg = consumer.poll_message(timeout=timeout)
        if not msg:
            _ctx_echo(ctx, {'message': None})
        else:
            out = {
                'topic': msg.topic,
                'partition': msg.partition,
                'offset': msg.offset,
                'key': msg.key.decode() if msg.key else None,
                'value': msg.value.decode() if msg.value else None,
                'transactional': msg.is_transactional,
                'transaction_id': msg.transaction_id,
            }
            _ctx_echo(ctx, out)
    except KafkaConsumerError as e:
        click.echo(f"Poll failed: {e}", err=True)
        sys.exit(1)
    finally:
        consumer.stop()

@consume.command('batch')
@click.argument('topic')
@click.option('--group', '-g', default='cli-consumer', show_default=True,
              help='Consumer group id used for batch fetch.')
@click.option('--count', '-n', type=int, default=10, show_default=True,
              help='Maximum number of messages to pull in one fetch cycle.')
@click.option('--timeout', '-t', type=float, default=5.0, show_default=True,
              help='Maximum wait for the underlying consume call.')
@click.option('--isolation', type=click.Choice(['read_committed', 'read_uncommitted']), default='read_committed',
              help='Transactional isolation level.')
@click.option('--seek-to-offset', type=int, help='Offset to seek to before consuming (optional --seek-to-partition for specific partition)')
@click.option('--seek-to-partition', type=int, help='Specific partition to seek within (optional, defaults to all partitions)')
@click.pass_context
def consume_batch(ctx, topic: str, group: str, count: int, timeout: float, isolation: str, seek_to_offset: int, seek_to_partition: int):
    """Fetch a bounded batch then exit.

    Performs a single Consumer.consume(count, timeout) call and outputs all received
    messages (possibly fewer than --count). Commits offsets at end when auto-commit is disabled.

    Examples:
      python -m klient consume batch events --count 50 --group nightly-loader
      python -m klient consume batch events --seek-to-offset 1000  # seeks all partitions
      python -m klient consume batch events --seek-to-offset 1000 --seek-to-partition 0  # specific partition
    """
    # Validate seek options (partition can be specified without offset but not the reverse)
    if seek_to_partition is not None and seek_to_offset is None:
        click.echo("Error: --seek-to-partition requires --seek-to-offset", err=True)
        sys.exit(2)
    
    # Show configuration if requested
    if ctx.obj.get('show_config'):
        command_info = {
            'command': 'consume batch',
            'topic': topic,
            'consumer_group': group,
            'count': count,
            'timeout': timeout,
            'isolation_level': isolation,
            'seek_to_offset': seek_to_offset,
            'seek_to_partition': seek_to_partition,
        }
        _show_kafka_config(ctx.obj, command_info)
    
    consumer = build_consumer(ctx.obj['bootstrap'], group, isolation, auto_commit=False, ctx_obj=ctx.obj)
    consumer.subscribe([topic])
    
    # Perform seek if requested
    if seek_to_offset is not None:
        try:
            consumer.seek_to_offset(topic, seek_to_offset, seek_to_partition)
        except KafkaConsumerError as e:
            click.echo(f"Seek failed: {e}", err=True)
            sys.exit(1)
    
    try:
        msgs = consumer.consume_messages(count=count, timeout=timeout)
        out = []
        for m in msgs:
            out.append({
                'topic': m.topic,
                'partition': m.partition,
                'offset': m.offset,
                'key': m.key.decode() if m.key else None,
                'value': m.value.decode() if m.value else None,
                'transactional': m.is_transactional,
                'transaction_id': m.transaction_id,
            })
        consumer.commit()
        _ctx_echo(ctx, out)
    except KafkaConsumerError as e:
        click.echo(f"Batch consume failed: {e}", err=True)
        sys.exit(1)
    finally:
        consumer.stop()

@consume.command('stream')
@click.argument('topic')
@click.option('--group', '-g', default='cli-stream', show_default=True,
              help='Consumer group id for streaming (maintains offsets across runs).')
@click.option('--limit', '-l', type=int, default=None,
              help='Optional max messages to emit; omit or use 0 for unlimited until Ctrl+C.')
@click.option('--timeout', '-t', type=float, default=1.0, show_default=True,
              help='Per-poll timeout in seconds (kept small to stay responsive).')
@click.option('--isolation', type=click.Choice(['read_committed', 'read_uncommitted']), default='read_committed',
              help='Transactional isolation level for the stream.')
@click.option('--grace-period', type=float, default=2.0, show_default=True,
              help='Seconds to allow in-flight processing to finish after shutdown signal before closing.')
@click.option('--seek-to-offset', type=int, help='Offset to seek to before consuming (seeks all partitions unless --seek-to-partition specified)')
@click.option('--seek-to-partition', type=int, help='Specific partition to seek within (optional, defaults to all partitions)')
@click.pass_context
def consume_stream(ctx, topic: str, group: str, limit: t.Optional[int], timeout: float, isolation: str, grace_period: float, seek_to_offset: int, seek_to_partition: int):
    """Continuous stream (unlimited by default, stop with Ctrl+C).

    Repeatedly polls for messages and prints them immediately. Designed for quick
    inspection or lightweight tailing of a topic.

    If --limit is provided (>0) the stream stops after that many messages. Without --limit
    (or if set to 0) it runs indefinitely until interrupted.

    Examples:
      python -m klient consume stream metrics              # unlimited
      python -m klient consume stream metrics --limit 100  # bounded
      python -m klient consume stream events --group realtime --isolation read_committed
      python -m klient consume stream events --seek-to-offset 1000  # seeks all partitions
      python -m klient consume stream events --seek-to-offset 1000 --seek-to-partition 0  # specific partition
    """
    # Validate seek options (partition can be specified without offset but not the reverse)
    if seek_to_partition is not None and seek_to_offset is None:
        click.echo("Error: --seek-to-partition requires --seek-to-offset", err=True)
        sys.exit(2)
    
    # Show configuration if requested
    if ctx.obj.get('show_config'):
        command_info = {
            'command': 'consume stream',
            'topic': topic,
            'consumer_group': group,
            'timeout': timeout,
            'isolation_level': isolation,
            'limit': limit if limit else 'unlimited',
            'grace_period': grace_period,
            'seek_to_offset': seek_to_offset,
            'seek_to_partition': seek_to_partition,
        }
        _show_kafka_config(ctx.obj, command_info)
    
    consumer = build_consumer(ctx.obj['bootstrap'], group, isolation, auto_commit=True, ctx_obj=ctx.obj)
    consumer.subscribe([topic])
    
    # Perform seek if requested
    if seek_to_offset is not None:
        try:
            consumer.seek_to_offset(topic, seek_to_offset, seek_to_partition)
        except KafkaConsumerError as e:
            click.echo(f"Seek failed: {e}", err=True)
            sys.exit(1)
    
    consumer._is_running = True
    seen = 0

    # Graceful shutdown setup
    shutdown_requested = False
    import signal
    import json
    import time
    start_time = time.time()
    def _signal_handler(signum, frame):  # noqa
        nonlocal shutdown_requested
        if not shutdown_requested:
            shutdown_requested = True
            from .metrics import inc
            inc('consumer.shutdown.signal')
            click.echo(json.dumps({'event':'shutdown_requested','signal':signum,'topic':topic}))
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _signal_handler)
        except Exception:  # noqa
            pass

    try:
        while consumer._is_running:
            if shutdown_requested:
                # Allow grace period for in-flight loop completion
                if (time.time() - start_time) >= grace_period:
                    break
                # brief sleep to avoid tight loop during grace period
                time.sleep(min(0.05, grace_period))
                continue
            msg = consumer.poll_message(timeout=timeout)
            if msg:
                # Try to parse message value as JSON for pretty printing
                message_value = msg.value.decode() if msg.value else None
                if message_value:
                    try:
                        # Parse JSON and use context formatting
                        parsed_json = json.loads(message_value)
                        formatted_message = _format_output(parsed_json, True, ctx.obj['pretty_json'], ctx.obj.get('filter_pattern'))
                        if formatted_message:
                            # For multi-line JSON, put on new line after prefix
                            if '\n' in formatted_message:
                                click.echo(f"{msg.topic}[{msg.partition}]@{msg.offset}:")
                                click.echo(formatted_message)
                            else:
                                click.echo(f"{msg.topic}[{msg.partition}]@{msg.offset}: {formatted_message}")
                        else:
                            # Message was filtered out
                            continue
                    except json.JSONDecodeError:
                        # Not JSON, output as plain text
                        click.echo(f"{msg.topic}[{msg.partition}]@{msg.offset}: {message_value}")
                else:
                    click.echo(f"{msg.topic}[{msg.partition}]@{msg.offset}: {message_value}")
                seen += 1
                if limit and limit > 0 and seen >= limit:
                    break
            else:
                # idle pause to reduce CPU
                time.sleep(0.01)
    except KafkaConsumerError as e:
        click.echo(f"Stream error: {e}", err=True)
        sys.exit(1)
    finally:
        consumer.stop()
        duration = time.time() - start_time
        try:
            from .metrics import inc
            inc('consumer.shutdown.complete')
        except Exception:  # noqa
            pass
        click.echo(json.dumps({'event':'stream_ended','reason':'signal' if shutdown_requested else 'limit_or_exit','messages':seen,'duration_s':round(duration,3)}))


# ---------- Load Test Data ----------

@cli.group()
@click.pass_context
def load(ctx):
    """Load helper data for demos."""


@load.command('test-data')
@click.argument('topic')
@click.option('--count', '-n', type=int, default=10, show_default=True)
@click.option('--prefix', default='sample', show_default=True)
@click.pass_context
def load_test_data(ctx, topic: str, count: int, prefix: str):
    # Include env-based additional config by passing ctx.obj
    producer = build_producer(ctx.obj['bootstrap'], transactional_id=None, ctx_obj=ctx.obj)
    try:
        for i in range(count):
            producer.produce(
                topic=topic,
                key=f"{prefix}-key-{i}",
                value=f"{prefix}-value-{i}",
                headers={'loader': 'cli'},
                flush=False,
            )
        producer.flush()
        _ctx_echo(ctx, {'loaded': count, 'topic': topic})
    except KafkaProducerError as e:
        click.echo(f"Load failed: {e}", err=True)
        sys.exit(1)
    finally:
        producer.close()


# ---------- Info Commands ----------

@cli.group()
@click.pass_context
def info(ctx):
    """Informational commands."""


@info.command('version')
def version():
    from klient import __version__
    click.echo(__version__)


@info.command('config-dump')
@click.option('--transactional-id', '--tx-id', default=None)
@click.pass_context
def config_dump(ctx, transactional_id: t.Optional[str]):
    # Build producer config with env overrides
    prod_addl = dict(ctx.obj.get('env_producer') or {})
    if transactional_id is None and 'transactional.id' in prod_addl:
        transactional_id = prod_addl['transactional.id']
    for k in ['bootstrap.servers', 'transactional.id']:
        prod_addl.pop(k, None)
    producer_cfg = ProducerConfig(bootstrap_servers=ctx.obj['bootstrap'], transactional_id=transactional_id, additional_config=prod_addl)

    # Build consumer config with env overrides
    cons_addl = dict(ctx.obj.get('env_consumer') or {})
    env_group = cons_addl.get('group.id')
    group_id = env_group or 'config-dump-group'
    for k in ['bootstrap.servers', 'group.id']:
        cons_addl.pop(k, None)
    consumer_cfg = ConsumerConfig(bootstrap_servers=ctx.obj['bootstrap'], group_id=group_id, additional_config=cons_addl)

    # Build admin config with env overrides
    adm_addl = dict(ctx.obj.get('env_admin') or {})
    adm_addl.pop('bootstrap.servers', None)
    admin_cfg = AdminConfig(bootstrap_servers=ctx.obj['bootstrap'], additional_config=adm_addl)

    out = {
        'env': ctx.obj.get('env'),
        'bootstrap': ctx.obj['bootstrap'],
        'sections': {
            'producer': producer_cfg.to_confluent_config(),
            'consumer': consumer_cfg.to_confluent_config(),
            'admin': admin_cfg.to_confluent_config(),
        },
        'env_raw_keys': list((ctx.obj.get('env_config_raw') or {}).keys()),
        'env_raw': ctx.obj.get('env_config_raw'),
    }
    _ctx_echo(ctx, out)


def main():  # Allows `python -m klient` execution
    cli()


if __name__ == '__main__':
    main()
