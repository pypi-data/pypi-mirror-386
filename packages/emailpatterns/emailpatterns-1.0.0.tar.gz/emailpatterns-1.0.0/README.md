# Email Patterns

Python utility to generate email addresses based on common patterns.

## Usage

```python
from emailpatterns.utils import generate_pattern_email, generate_all_pattern_emails

email = generate_pattern_email("pattern1", "example.com", "John", "Doe")
print(email)  # john.doe@example.com

all_emails = generate_all_pattern_emails("example.com", "John", "Doe")
print(all_emails)
