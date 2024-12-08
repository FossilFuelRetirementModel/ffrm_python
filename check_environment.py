"""
Script to check if all required packages are installed correctly.
"""
import pkg_resources
import sys

def check_requirements():
    # Read requirements file
    with open('requirements.txt', 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Check each requirement
    missing = []
    for requirement in requirements:
        try:
            pkg_resources.require(requirement)
        except pkg_resources.DistributionNotFound:
            missing.append(requirement)
    
    if missing:
        print("Missing packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        return False
    
    print("All required packages are installed!")
    return True

if __name__ == "__main__":
    sys.exit(0 if check_requirements() else 1)