# MSG91 Python Client

[![CI](https://github.com/karambir/msg91-py/actions/workflows/ci.yml/badge.svg)](https://github.com/karambir/msg91-py/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/msg91-py.svg)](https://pypi.org/project/msg91-py/)
[![Python Versions](https://img.shields.io/pypi/pyversions/msg91-py.svg)](https://pypi.org/project/msg91-py/)

A Python client library for the [MSG91 API](https://docs.msg91.com/overview).

## Installation

```bash
pip install msg91-py
```

> **Note:** The package name on PyPI is `msg91-py`, but the module name for imports is still `msg91`.

## Usage

### Initialize the client

```python
from msg91 import Client

# Initialize client with your auth key
client = Client("your_auth_key")
```

### Sending SMS

```python
# Send SMS using the standard API
response = client.sms.send(
    mobile="919XXXXXXXXX",
    message="Hello, this is a test message from MSG91!",
    sender="SENDER",
    route="4",
    country="91"
)
print(response)

# Send bulk SMS
response = client.sms.send(
    mobile=["919XXXXXXXXX", "918XXXXXXXXX"],
    message="Hello, this is a bulk message!",
    sender="SENDER",
    route="4"
)
print(response)

# Send SMS using a template (Flow API)
response = client.sms.send_template(
    template_id="your_template_id",
    mobile="919XXXXXXXXX",
    variables={"var1": "value1", "var2": "value2"},
    sender_id="SENDER"
)
print(response)
```

### Managing Templates

```python
# Create a new template
response = client.template.create(
    template_name="Welcome",
    template_body="Welcome to our service, {{var1}}!",
    sender_id="SENDER",
    sms_type="NORMAL"  # Options: NORMAL, UNICODE
)
print(response)

# Get template versions
template_versions = client.template.get("template_id")
print(template_versions)

# Add a new version to an existing template
response = client.template.add_version(
    template_id="template_id",
    template_body="Welcome to our service, {{var1}}! New version.",
    sender_id="SENDER"
)
print(response)

# Set a template version as default
response = client.template.set_default(
    template_id="template_id",
    version_id="version_id"
)
print(response)
```

### OTP (One-Time Password)

```python
# Send OTP
response = client.otp.send(
    mobile="919XXXXXXXXX"
)
print(response)
session_id = response.get("message")

# Send OTP with custom settings
response = client.otp.send(
    mobile="919XXXXXXXXX",
    message="Your login code is ##OTP##. Valid for 5 minutes.",
    sender="MYAPP",
    otp_length=6,
    otp_expiry=5
)
print(response)

# Verify OTP
response = client.otp.verify(
    mobile="919XXXXXXXXX",
    otp="123456"
)
print(response)

if response.get("type") == "success":
    print("OTP verified successfully!")

# Resend OTP via SMS
response = client.otp.resend(
    mobile="919XXXXXXXXX",
    retrytype="text"
)
print(response)

# Resend OTP via Voice
response = client.otp.resend(
    mobile="919XXXXXXXXX",
    retrytype="voice"
)
print(response)
```

### Logs and Analytics

```python
# Get SMS logs
logs = client.sms.get_logs(
    start_date="2023-01-01",
    end_date="2023-01-31"
)
print(logs)

# Get analytics
analytics = client.sms.get_analytics()
print(analytics)

# Get analytics for specific date range
analytics = client.sms.get_analytics(
    start_date="2023-01-01",
    end_date="2023-01-31"
)
print(analytics)
```

## API Endpoints

The client uses the following MSG91 API endpoints:

**SMS:**
- Send SMS: `http://api.msg91.com/api/v2/sendsms` (v2 API)
- Send Template SMS: `flow` (v5 API)
- SMS Logs: `report/logs/p/sms`
- SMS Analytics: `report/analytics/p/sms`

**Templates:**
- Create Template: `sms/addTemplate`
- Add Template Version: `sms/addTemplateVersion`
- Get Template Versions: `sms/getTemplateVersions`
- Mark Template as Default: `sms/markActive`

**OTP:**
- Send OTP: `http://api.msg91.com/api/sendotp.php`
- Verify OTP: `http://api.msg91.com/api/verifyRequestOTP.php`
- Resend OTP: `http://api.msg91.com/api/retryotp.php`

## Requirements

- Python 3.9+
- httpx

## License

This project is licensed under the MIT License - see the LICENSE file for details.
