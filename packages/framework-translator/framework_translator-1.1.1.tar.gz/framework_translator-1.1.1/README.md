# Framework Translator

A powerful CLI tool and Python SDK for seamlessly translating code between machine learning frameworks using advanced AI models. Convert your code between PyTorch, TensorFlow, JAX, and Scikit-learn with ease.

## 🚀 Features

- **Multi-Framework Support**: Translate between PyTorch, TensorFlow, JAX, and Scikit-learn
- **CLI Interface**: Easy-to-use command-line tool with interactive prompts
- **Python SDK**: Programmatic access for integration into your workflows
- **Authentication**: Secure user authentication with credential management
- **Translation History**: Track and download your translation history
- **Smart Inference**: Automatic source framework detection when not specified
- **File & Interactive Input**: Support for both file-based and interactive code input

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install framework-translator
```

### From Source

```bash
git clone <repository-url>
cd pypi-tool
pip install .
```

## 🔧 Quick Start

### 1. Register an Account

Before using the tool, you need to register at:
[https://code-translation-frontend-283805296028.us-central1.run.app/register](https://code-translation-frontend-283805296028.us-central1.run.app/register)

### 2. Login

```bash
ft login
```

### 3. Translate Code

```bash
ft translate
```

Follow the interactive prompts to translate your code!

## 🖥️ CLI Usage

### Commands Overview

```bash
ft --help                 # Show all available commands
ft login                  # Login to the service
ft logout                 # Logout from the service
ft translate              # Interactive code translation
ft history                # View translation history
ft history -d             # Download history as JSON
ft version                # Show version information
```

### Interactive Translation Workflow

When you run `ft translate`, you'll be guided through:

1. **Language Selection**: Choose your programming language (currently supports Python)
2. **Source Framework**: Specify source framework or let the AI infer it
3. **Framework Group**: Select framework category (e.g., "ml" for machine learning)
4. **Target Framework**: Choose your target framework
5. **Code Input**: Provide code via interactive input or file path

### Example Translation Session

```bash
$ ft translate
Translate: Framework Translator
Choose a language -> Languages supported [python]: python
Give us your framework: (Enter to let the model infer): pytorch
Choose a framework group -> Framework groups supported for language python [ml]: ml
Choose a target framework -> Target frameworks supported for group ml [jax, pytorch, scikit-learn, tensorflow]: tensorflow
Provide source code via one of the options:
1) Paste (end with 'END' on its own line)
2) File path
Select [1/2]: 1
Enter source code (end with a single line containing only 'END'):
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 1)
    
    def forward(self, x):
        return self.fc(x)
END

Translating code to tensorflow...
--------------------------------------
----------Translation Result----------
--------------------------------------
import tensorflow as tf

class SimpleNet(tf.keras.Model):
    def __init__(self):
        super().__init__()
        self.fc = tf.keras.layers.Dense(1)
    
    def call(self, x):
        return self.fc(x)
--------------------------------------
Translation completed successfully.
```

### File-Based Translation

You can also translate code from files:

```bash
ft translate
# ... follow prompts ...
Select [1/2]: 2
Enter file path: /path/to/your/code.py
```

### View Translation History

```bash
# View history in terminal
ft history

# Download history as JSON file
ft history -d
```

## 🐍 Python SDK Usage

The Framework Translator also provides a Python SDK for programmatic access:

### Basic SDK Usage

```python
import framework_translator.sdk as ft

# Check login status
if not ft.is_logged_in():
    # Login (you can also use environment variables)
    success = ft.login("your_username", "your_password")
    if not success:
        print("Login failed!")
        exit(1)

# Translate code
pytorch_code = """
import torch
import torch.nn as nn

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(784, 10)
    
    def forward(self, x):
        return self.fc(x)
"""

# Translate to TensorFlow
tensorflow_code = ft.translate(
    code=pytorch_code,
    target_framework="tensorflow",
    source_framework="pytorch"  # Optional - can be inferred
)

print("Translated code:")
print(tensorflow_code)
```

### SDK Reference

#### Authentication

```python
# Check if logged in
ft.is_logged_in() -> bool

# Login
ft.login(username: str, password: str) -> bool

# Logout
ft.logout() -> None
```

#### Translation

```python
# Translate code
ft.translate(
    code: str,
    target_framework: str,
    source_framework: Optional[str] = None
) -> str
```

#### Framework Information

```python
# Get supported frameworks
ft.get_supported_frameworks(group: Optional[str] = None) -> list[str]
ft.get_supported_groups() -> list[str]
ft.get_supported_languages() -> list[str]

# Get framework details
ft.get_framework_info(framework_name: str) -> dict
```

#### History

```python
# Get translation history
ft.get_history(page: int = 1, per_page: int = 50) -> list[dict]
```

### Advanced SDK Example

```python
import framework_translator.sdk as ft

def translate_project_files():
    """Example: Translate multiple files in a project"""
    
    if not ft.is_logged_in():
        print("Please login first")
        return
    
    # Get list of supported frameworks
    frameworks = ft.get_supported_frameworks("ml")
    print(f"Supported ML frameworks: {frameworks}")
    
    # Read source file
    with open("model.py", "r") as f:
        source_code = f.read()
    
    # Translate to multiple frameworks
    for target in ["tensorflow", "jax"]:
        try:
            translated = ft.translate(
                code=source_code,
                target_framework=target,
                source_framework="pytorch"
            )
            
            # Save translated code
            with open(f"model_{target}.py", "w") as f:
                f.write(translated)
            
            print(f"✅ Translated to {target}")
            
        except Exception as e:
            print(f"❌ Failed to translate to {target}: {e}")

# Get translation history
history = ft.get_history()
print(f"You have {len(history)} translations in history")
```

## 🛠️ Supported Frameworks

Currently supported machine learning frameworks:

| Framework | Status | Description |
|-----------|--------|-------------|
| **PyTorch** | ✅ | Popular deep learning framework |
| **TensorFlow** | ✅ | Google's machine learning platform |
| **JAX** | ✅ | NumPy-compatible library for ML research |
| **Scikit-learn** | ✅ | Machine learning library for Python |

## 🔐 Authentication & Security

- **Secure Authentication**: User credentials are encrypted and stored locally
- **Token-Based**: Uses JWT tokens for API communication
- **Session Management**: Automatic token refresh and session handling
- **Privacy**: Your code and translations are associated with your account

## 📊 Translation History

The tool automatically tracks all your translations:

- **Persistent Storage**: All translations are saved to your account
- **Metadata Tracking**: Includes timestamps, models used, and performance metrics
- **Download Options**: Export your history as JSON for analysis
- **Search & Filter**: View recent translations in the CLI

## ⚙️ Configuration

The tool stores configuration in platform-appropriate directories:

- **Linux/macOS**: `~/.config/framework_translator/`
- **Windows**: `%APPDATA%\strasta\framework_translator\`

Configuration includes:
- Encrypted user credentials
- User preferences
- Cache data

## 🚨 Error Handling

Common issues and solutions:

### Authentication Errors
```bash
# If you get authentication errors:
ft logout
ft login
```

### Network Issues
- Check your internet connection
- Verify the backend service is accessible
- Try again after a few moments

### Invalid Framework
- Use `ft translate` to see supported frameworks interactively
- Check spelling of framework names

## 📝 Examples

### Example 1: PyTorch to TensorFlow CNN

**Input (PyTorch):**
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)
```

**Output (TensorFlow):**
```python
import tensorflow as tf

class CNN(tf.keras.Model):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = tf.keras.layers.Conv2D(32, 3, activation='relu')
        self.conv2 = tf.keras.layers.Conv2D(64, 3, activation='relu')
        self.pool = tf.keras.layers.MaxPooling2D(2)
        self.flatten = tf.keras.layers.Flatten()
        self.fc1 = tf.keras.layers.Dense(128, activation='relu')
        self.fc2 = tf.keras.layers.Dense(10)

    def call(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.pool(x)
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.fc2(x)
        return tf.nn.log_softmax(x, axis=1)
```

### Example 2: Scikit-learn to PyTorch

**Input (Scikit-learn):**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

# Create and train model
scaler = StandardScaler()
model = LogisticRegression()

X_scaled = scaler.fit_transform(X_train)
model.fit(X_scaled, y_train)

# Make predictions
X_test_scaled = scaler.transform(X_test)
predictions = model.predict(X_test_scaled)
```

**Output (PyTorch):**
```python
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

class LogisticRegression(nn.Module):
    def __init__(self, input_dim):
        super(LogisticRegression, self).__init__()
        self.linear = nn.Linear(input_dim, 1)
        
    def forward(self, x):
        return torch.sigmoid(self.linear(x))

# Create and train model
scaler = StandardScaler()
model = LogisticRegression(X_train.shape[1])
criterion = nn.BCELoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

X_scaled = scaler.fit_transform(X_train)
X_tensor = torch.FloatTensor(X_scaled)
y_tensor = torch.FloatTensor(y_train).reshape(-1, 1)

# Training loop
for epoch in range(100):
    optimizer.zero_grad()
    outputs = model(X_tensor)
    loss = criterion(outputs, y_tensor)
    loss.backward()
    optimizer.step()

# Make predictions
X_test_scaled = scaler.transform(X_test)
X_test_tensor = torch.FloatTensor(X_test_scaled)
with torch.no_grad():
    predictions = model(X_test_tensor).numpy()
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for more information.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs or request features on our GitHub issues page
- **Documentation**: This README and built-in help (`ft help`)
- **Community**: Join our community discussions

## 🔄 Changelog

### Version 1.1.0
- Added comprehensive SDK support
- Improved authentication and session management
- Enhanced error handling and user feedback
- Added translation history tracking
- Support for file-based input

### Version 1.0.0
- Initial release
- Basic CLI functionality
- Support for PyTorch, TensorFlow, JAX, and Scikit-learn
- User authentication and backend integration

---

**Happy Translating! 🚀**

Transform your machine learning code across frameworks with the power of AI.