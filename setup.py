from setuptools import find_packages, setup


classifiers = [
    "Development Status :: 1 - Planning",
    # "Development Status :: 2 - Pre-Alpha",
    # "Development Status :: 3 - Alpha",
    # "Development Status :: 4 - Beta",
    # "Development Status :: 5 - Production/Stable",
    # "Development Status :: 6 - Mature",
    # "Development Status :: 7 - Inactive",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
    "Topic :: Software Development :: Libraries",
    "License :: OSI Approved :: MIT License",
]

# Read requirements
with open("requirements.txt") as f:
    package_requirements = f.read().splitlines()


setup(
    name="falcon_idempotency",
    author="Bhargav R. Patel",
    author_email="bhargav@colloquial.me",
    url="https://github.com/bhargavrpatel/falcon-idempotency",
    version="0.0.1",
    classifiers=classifiers,
    description="Idempotent requests for Falcon",
    long_description=open("README.rst").read(),
    keywords="falcon api idempotency idempotent endpoints ",
    packages=find_packages(include=("falcon_idempotency*",)),
    install_requires=package_requirements,
    include_package_data=True,
    license="MIT",
)
