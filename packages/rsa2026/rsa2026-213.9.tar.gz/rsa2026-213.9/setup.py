from setuptools import setup, find_packages

# قراءة محتوى README.md لاستخدامه كـ long_description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='rsa2026',
    version='213.9',
    packages=find_packages(),
    install_requires=[
        'pycryptodome>=3.19.0',
        'pyfiglet>=0.8.post1',
        'psutil'
    ],
    entry_points={
        'console_scripts': [
            'rsa2026 = rsa2026.main:main',
        ],
    },
    author='IMAD 213',
    author_email='imad213.official@gmail.com',
    description='High-security encryption tool using RSA-4096 and AES-256 with anti-debug and self-destruct.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Security :: Cryptography',
    ],
    python_requires='>=3.6',
)
