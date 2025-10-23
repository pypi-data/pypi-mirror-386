# Python Script Runner

> **Enterprise-grade Python script execution engine** with real-time monitoring, alerting, analytics, and distributed execution.

[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square&logo=github)](LICENSE)
[![Release](https://img.shields.io/github/v/release/jomardyan/Python-Script-Runner?style=flat-square&logo=github&logoColor=white)](https://github.com/jomardyan/Python-Script-Runner/releases)
[![PyPI Downloads](https://img.shields.io/pypi/dm/python-script-runner?style=flat-square&logo=pypi)](https://pypi.org/project/python-script-runner/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)](https://github.com/jomardyan/Python-Script-Runner)

Transform script execution into a production-ready operation with comprehensive observability, intelligent alerting, CI/CD integration, and advanced analytics.

## 🚀 Quick Install

```bash
pip install python-script-runner
```

## 📖 Quick Links

- **[Full Documentation](https://github.com/jomardyan/Python-Script-Runner#documentation)** - Complete guides and examples
- **[GitHub Repository](https://github.com/jomardyan/Python-Script-Runner)** - Source code and issues
- **[Examples](#usage-examples)** - Common use cases below

## Key Features

- **🔍 Real-Time Monitoring** - CPU, memory, I/O tracking with <2% overhead
- **🔔 Multi-Channel Alerts** - Email, Slack, webhooks with threshold-based logic
- **🚀 CI/CD Integration** - Performance gates, JUnit/TAP reporting, baseline comparison
- **📊 Historical Analytics** - SQLite backend with trend analysis & anomaly detection
- **🔄 Retry Strategies** - Linear, exponential, Fibonacci backoff with smart filtering
- **🎯 Advanced Profiling** - CPU/memory/I/O analysis with bottleneck identification
- **🏢 Enterprise Ready** - Datadog, Prometheus, New Relic integrations
- **🌐 Distributed Execution** - SSH, Docker, Kubernetes support
- **📈 Web Dashboard** - Real-time metrics visualization & RESTful API
- **🤖 ML-Powered** - Anomaly detection, forecasting, correlation analysis

## Installation

### Requirements

- **Python**: 3.6+ (3.8+ recommended)
- **OS**: Linux, macOS, Windows
- **Core Dependency**: psutil

### Install from PyPI

```bash
pip install python-script-runner
```

### Optional Dependencies

For additional features, install with extras:

```bash
# Dashboard with FastAPI
pip install python-script-runner[dashboard]

# Data export and ML features
pip install python-script-runner[export]

# Documentation and development
pip install python-script-runner[dev,docs]
```

### From Source

```bash
git clone https://github.com/jomardyan/Python-Script-Runner.git
cd Python-Script-Runner
pip install -e .
```

## Usage Examples

### Basic Usage

```bash
# Simple script execution
python -m runner myscript.py

# With arguments
python -m runner train.py --epochs 100 --batch-size 32

# With monitoring and alerts
python -m runner myscript.py --alert-config "cpu_high:cpu_max>80" --slack-webhook "<webhook_url>"
```

### Performance Gates (CI/CD)

```bash
# Stop execution if performance threshold exceeded
python -m runner tests/suite.py \
    --add-gate cpu_max:90 \
    --add-gate memory_max_mb:1024 \
    --junit-output results.xml
```

### Historical Analytics

```bash
# Track metrics over time and detect anomalies
python -m runner myscript.py \
    --history-db metrics.db \
    --detect-anomalies \
    --analyze-trend
```

### Remote Execution

```bash
# Execute on remote server via SSH
python -m runner script.py \
    --ssh-host production.example.com \
    --ssh-user deploy \
    --ssh-key ~/.ssh/id_rsa
```

## Configuration

Create a `config.yaml` for advanced setup:

```yaml
alerts:
  - name: cpu_high
    condition: cpu_max > 85
    channels: [slack, email]
    severity: WARNING

performance_gates:
  - metric_name: cpu_max
    max_value: 90
  - metric_name: memory_max_mb
    max_value: 1024

notifications:
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK"
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from: "alerts@company.com"
    to: ["team@company.com"]
    use_tls: true
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Monitoring Overhead | <2% CPU/memory |
| Sampling Speed | 10,000+ metrics/second |
| Query Performance | Sub-second on 1-year data |
| Scalability | Millions of records with SQLite |

## CI/CD Integration

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run with performance gates
  run: |
    pip install python-script-runner
    python -m runner tests/suite.py \
      --add-gate cpu_max:85 \
      --add-gate memory_max_mb:2048 \
      --junit-output test-results.xml
```

### Jenkins

```groovy
sh '''
  pip install python-script-runner
  python -m runner tests/suite.py \
    --junit-output test-results.xml \
    --json-output metrics.json
'''
```

## Collected Metrics

The runner automatically collects and analyzes:

| Category | Metrics |
|----------|---------|
| **Timing** | start_time, end_time, execution_time_seconds |
| **CPU** | cpu_max, cpu_avg, cpu_min, user_time, system_time |
| **Memory** | memory_max_mb, memory_avg_mb, memory_min_mb, page_faults |
| **System** | num_threads, num_fds, context_switches, block_io |
| **Output** | stdout_lines, stderr_lines, exit_code, success |

## Advanced Features

- **Anomaly Detection** - Automatically identify performance regressions
- **Trend Analysis** - Historical performance tracking and forecasting
- **Custom Alerts** - Flexible threshold-based alerting system
- **Remote Execution** - SSH, Docker, and Kubernetes support
- **Enterprise Integrations** - Datadog, Prometheus, New Relic
- **Export Options** - JSON, CSV, Parquet formats

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: psutil` | `pip install psutil` |
| `YAML config not loading` | `pip install pyyaml` |
| `Slack alerts not working` | Verify webhook URL and network access |
| `Database locked error` | Ensure no other processes are using the DB |

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details

## Support & Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/jomardyan/Python-Script-Runner/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/jomardyan/Python-Script-Runner/discussions)
- **GitHub Repository**: [Source code and documentation](https://github.com/jomardyan/Python-Script-Runner)

## Project Status

- **Version**: 6.0.0
- **Status**: Production Ready ✅
- **Python Support**: 3.6 - 3.11 (CPython & PyPy)
- **License**: MIT
- **Last Updated**: October 2025

---

Made with ❤️ by Python Script Runner Contributors

[**Install Now**](https://pypi.org/project/python-script-runner/) • [**GitHub**](https://github.com/jomardyan/Python-Script-Runner) • [**Report Issue**](https://github.com/jomardyan/Python-Script-Runner/issues)
