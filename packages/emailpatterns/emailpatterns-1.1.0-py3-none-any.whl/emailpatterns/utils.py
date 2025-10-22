"""
Email pattern generation utility.
"""


def generate_pattern_email(pattern, domain, firstname, lastname):
    """
    Generate email address based on pattern, domain, and name.

    Args:
        pattern (str): Pattern identifier (e.g., 'pattern1', 'pattern2', etc.)
        domain (str): Email domain
        firstname (str): First name
        lastname (str): Last name

    Returns:
        str: Generated email address

    Examples:
        >>> generate_pattern_email('pattern1', 'example.com', 'John', 'Doe')
        'john.doe@example.com'
        >>> generate_pattern_email('pattern5', 'example.com', 'John', 'Doe')
        'john@example.com'
    """
    if not pattern or not domain or not firstname or not lastname:
        return ''

    # Normalize inputs
    firstname = firstname.lower().strip()
    lastname = lastname.lower().strip()
    domain = domain.lower().strip()

    # Pattern mapping
    patterns = {
        'pattern1': f'{firstname}.{lastname}@{domain}',  # john.doe@example.com
        'pattern2': f'{firstname}{lastname}@{domain}',  # johndoe@example.com
        'pattern3': f'{firstname}_{lastname}@{domain}',  # john_doe@example.com
        'pattern4': f'{lastname}_{firstname}@{domain}',  # doe_john@example.com
        'pattern5': f'{firstname}@{domain}',  # john@example.com
        'pattern6': f'{lastname}@{domain}',  # doe@example.com
        'pattern7': f'{firstname}-{lastname}@{domain}',  # john-doe@example.com
        'pattern8': f'{firstname[0]}.{lastname}@{domain}',  # j.doe@example.com
        'pattern9': f'{firstname[0]}{lastname}@{domain}',  # jdoe@example.com
        'pattern10': f'{lastname}{firstname[0]}@{domain}',  # doej@example.com
        'pattern11': f'{firstname}{lastname[0]}@{domain}',  # johnd@example.com
        'pattern12': f'{firstname[0]}{lastname[0]}@{domain}',  # jd@example.com
        'pattern13': f'{lastname}.{firstname[0]}@{domain}',  # doe.j@example.com
        'pattern14': f'{lastname}{firstname}@{domain}',  # doejohn@example.com
        'pattern15': f'{firstname}.{lastname[0]}@{domain}',  # john.d@example.com
        'pattern16': f'{lastname}.{firstname}@{domain}',  # doe.john@example.com
        'pattern17': f'{lastname}-{firstname}@{domain}',  # doe-john@example.com
        'pattern18': f'{lastname}_{firstname[0]}@{domain}',  # doe_j@example.com
        'pattern19': f'{lastname}-{firstname[0]}@{domain}',  # doe-j@example.com
        'pattern20': f'{firstname}_{lastname[0]}@{domain}',  # john_d@example.com
        'pattern21': f'{firstname}-{lastname[0]}@{domain}',  # john-d@example.com
    }

    return patterns.get(pattern, '')


def generate_all_pattern_emails(domain, firstname, lastname):
    """
    Generate all possible email patterns for a given domain and name.

    Args:
        domain (str): Email domain
        firstname (str): First name
        lastname (str): Last name

    Returns:
        dict: Dictionary with pattern as key and email as value

    Example:
        >>> generate_all_pattern_emails('example.com', 'John', 'Doe')
        {
            'pattern1': 'john.doe@example.com',
            'pattern2': 'johndoe@example.com',
            ...
        }
    """
    emails = {}
    for i in range(1, 22):
        pattern = f'pattern{i}'
        email = generate_pattern_email(pattern, domain, firstname, lastname)
        if email:
            emails[pattern] = email

    return emails


def get_pattern_description(pattern):
    """
    Get human-readable description of a pattern.

    Args:
        pattern (str): Pattern identifier

    Returns:
        str: Description of the pattern
    """
    descriptions = {
        'pattern1': 'firstname.lastname@domain.com',
        'pattern2': 'firstnamelastname@domain.com',
        'pattern3': 'firstname_lastname@domain.com',
        'pattern4': 'lastname_firstname@domain.com',
        'pattern5': 'firstname@domain.com',
        'pattern6': 'lastname@domain.com',
        'pattern7': 'firstname-lastname@domain.com',
        'pattern8': 'f.lastname@domain.com',
        'pattern9': 'flastname@domain.com',
        'pattern10': 'lastnamef@domain.com',
        'pattern11': 'firstnamel@domain.com',
        'pattern12': 'fl@domain.com',
        'pattern13': 'lastname.f@domain.com',
        'pattern14': 'lastnamefirstname@domain.com',
        'pattern15': 'firstname.l@domain.com',
        'pattern16': 'lastname.firstname@domain.com',
        'pattern17': 'lastname-firstname@domain.com',
        'pattern18': 'lastname_f@domain.com',
        'pattern19': 'lastname-f@domain.com',
        'pattern20': 'firstname_l@domain.com',
        'pattern21': 'firstname-l@domain.com',
    }

    return descriptions.get(pattern, 'Unknown pattern')


# Example usage in your view or management command
if __name__ == '__main__':
    # Test the function
    email = generate_pattern_email('pattern1', 'example.com', 'John', 'Doe')
    print(f"Generated email: {email}")

    # Generate all patterns
    all_emails = generate_all_pattern_emails('example.com', 'John', 'Doe')
    for pattern, email in all_emails.items():
        print(f"{pattern}: {email}")