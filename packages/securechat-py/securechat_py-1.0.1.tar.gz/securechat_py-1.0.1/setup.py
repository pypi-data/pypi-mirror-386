from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='secure-chat',
    version='1.0.0',
    author='Soumyaranjan Sahoo',
    author_email='sahoosoumya242004@gmail.com',
    description='Ultra-secure terminal-based chat with end-to-end encryption and decentralized networking',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/i-soumya18/securechat',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications :: Chat',
        'Topic :: Security :: Cryptography',
    ],
    python_requires='>=3.8',
    install_requires=[
        'cryptography>=3.4.0',
    ],
    entry_points={
        'console_scripts': [
            'securechat=securechat.cli:main',
        ],
    },
    keywords='chat encryption security terminal decentralized messaging',
    project_urls={
        'Bug Reports': 'https://github.com/i-soumya18/securechat/issues',
        'Source': 'https://github.com/i-soumya18/securechat',
        'Documentation': 'https://github.com/i-soumya18/securechat#readme',
    },
)