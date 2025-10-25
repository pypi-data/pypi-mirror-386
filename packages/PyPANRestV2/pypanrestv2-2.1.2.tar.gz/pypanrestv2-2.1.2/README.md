# PyPanRestV2

**PyPanRestV2** is a Python library designed to simplify interactions with Palo Alto Networks firewalls and Panorama via their REST API. It provides a higher level of abstraction, allowing users to manage firewalls and Panorama without needing to construct REST requests manually or work with XML for areas of the firewall configuration that still require it.

---

## Features

- **High-Level Abstraction**: Simplifies interaction with the Palo Alto Networks API.
- **Support for Firewalls and Panorama**: Manage both individual firewalls and Panorama devices.
- **REST API Integration**: Allows seamless communication with devices using REST API.
- **XML API Support**: Handles XML API calls for configurations not yet available in REST API.
- **Convenient Pythonic Objects**: Intuitive Python objects for interacting with specific sections of Palo Alto firewall configurations.
- **Error Handling**: Custom exceptions for better error management and troubleshooting.

---

## Installation

You can install `PyPanRestV2` using pip:

```bash
pip install pypanrestv2
```

Alternatively, you can clone the repository and install it as a package for development:

```bash
# Clone the repository
git clone https://github.com/mrzepa/pypanrestv2.git

# Navigate to the project directory
cd pypanrestv2

# Install the package in development mode
pip install -e .
```

This will install the package and all required dependencies automatically. The `-e` flag installs the package in "editable" mode, which is useful if you plan to modify the code or contribute to the project.

---

## Basic Usage

### Import the Required Classes
Start by importing the necessary classes from the library:

```python
from pypanrestv2 import Firewall, Panorama
```

### Connect to a Firewall or Panorama Device
Create a `Firewall` or `Panorama` object by providing the required connection details:

For a **Firewall**:
```python
firewall = Firewall(base_url="192.168.1.1", api_key="12345")
```

For **Panorama**:
```python
panorama = Panorama(base_url="192.168.2.1", username="admin", password="my_password")
```

### Common Use Cases

#### 1. Managing Security Rules
```python
from pypanrestv2.Policies import SecurityRules

# Create a new security rule
security_rule = SecurityRules(firewall, name='allow_web')
security_rule.from_ = {'member': ['trust']}
security_rule.to = {'member': ['untrust']}
security_rule.source = {'member': ['any']}
security_rule.destination = {'member': ['any']}
security_rule.application = {'member': ['web-browsing']}
security_rule.service = {'member': ['application-default']}
security_rule.action = 'allow'
security_rule.create()

# Modify an existing rule
existing_rule = SecurityRules(firewall, name='existing_rule')
existing_rule.refresh()  # Load current configuration
existing_rule.action = 'deny'
existing_rule.update()
```

#### 2. Managing Address Objects
```python
from pypanrestv2.Objects import Addresses

# Create a new address object
address = Addresses(firewall, name='web_server')
address.value = '192.168.1.100'
address.type = 'ip-netmask'
address.create()

# Get all address objects
all_addresses = Addresses.get_all(firewall)
```

#### 3. Working with Panorama Policies and Rulebase
```python
from pypanrestv2 import Panorama
from pypanrestv2.Policies import SecurityRules

# Initialize Panorama connection
panorama = Panorama(base_url='panorama.example.com', api_key='YOUR_API_KEY')

# Create a security rule in the pre-rulebase of a device group
security_rule = SecurityRules(panorama, name='allow_internal', rulebase='Pre')
security_rule.from_ = {'member': ['trust']}
security_rule.to = {'member': ['untrust']}
security_rule.source = {'member': ['any']}
security_rule.destination = {'member': ['any']}
security_rule.application = {'member': ['web-browsing']}
security_rule.service = {'member': ['application-default']}
security_rule.action = 'allow'
security_rule.create()
```

---

## Repository

Visit the project's GitHub repository for source code, documentation, enhancements, and contributions:

[PyPanRestV2 Repository on GitHub](https://github.com/mrzepa/pypanrestv2.git)

---

## Requirements

- **Python 3.11+**
- **Palo Alto Networks Devices** running PAN-OS 9.0+ or Panorama
- Python dependencies:
  - dnspython
  - icecream
  - pycountry
  - python-dotenv
  - requests
  - tqdm
  - validators

---

## API Documentation

The SDK provides access to the following main components:

### Core Modules
- `Firewall/Panorama`: Base connection and authentication
- `Policies`: Security rules, NAT rules, and policy management
- `Objects`: Address objects, service objects, and security profiles
- `Network`: Interfaces, zones, and routing configuration
- `Device`: System settings and device management

### Error Handling

The SDK uses custom exceptions for better error handling:

```python
from pypanrestv2.Exceptions import PANConnectionError, PANConfigError

try:
    firewall = Firewall(base_url='192.168.1.1', api_key='invalid_key')
    firewall.test_connection()
except PANConnectionError as e:
    print(f'Connection failed: {e}')
except PANConfigError as e:
    print(f'Configuration error: {e}')
```

Common errors and solutions:
- `PANConnectionError`: Check network connectivity and API credentials
- `PANConfigError`: Verify object names and configuration values
- `PANNotFoundError`: Ensure referenced objects exist

## Status and Updates

This SDK is actively maintained and regularly updated to support new PAN-OS versions. While not all API endpoints are implemented, core functionality is stable and production-ready. Check the GitHub repository for the latest updates and supported features.

## Contributing

Contributions are welcome! If you want to report issues, request features, or contribute to the library:

1. Fork the repository.
2. Create a feature branch: `git checkout -b my-feature`.
3. Commit your changes: `git commit -m "Add detailed description of changes"`.
4. Push to the branch: `git push origin my-feature`.
5. Submit a pull request.

Be sure to check the documentation, if provided, before starting contributions.

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://opensource.org/license/mit) file for details.

---

## Author

Mark Rzepa
mark@rzepa.com

---
