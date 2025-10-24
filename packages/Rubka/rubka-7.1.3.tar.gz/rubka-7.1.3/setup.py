from setuptools import setup, find_packages

try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ''

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='Rubka',
    version='7.1.3',
    description='rubika A Python library for interacting with Rubika Bot API.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Mahdi Ahmadi',
    author_email='mahdiahmadi.1208@gmail.com',
    maintainer='Mahdi Ahmadi',
    maintainer_email='mahdiahmadi.1208@gmail.com',
    url='https://github.com/Mahdy-Ahmadi/Rubka',
    download_url='https://github.com/Mahdy-Ahmadi/rubka/archive/refs/tags/v6.6.4.zip',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
        'Natural Language :: Persian',
    ],
    python_requires='>=3.6',
    install_requires=[
        "requests",
        "Pillow",
        "websocket-client",
        'pycryptodome',
        'aiohttp',
        'httpx',
        'tqdm',
        'mutagen',
        'filetype',
        'aiofiles'
    ],
    entry_points={
        "console_scripts": [
            "rubka=rubka.__main__:main",
        ],
    },
    keywords="rubika bot api library chat messaging rubpy pyrubi rubigram",
    project_urls={
        "Bug Tracker": "https://t.me/Bprogrammer",
        "Documentation": "https://github.com/Mahdy-Ahmadi/rubka/blob/main/README.md",
        "Source Code": "https://github.com/Mahdy-Ahmadi/Rubka",
    },
    license="MIT",
    zip_safe=False
)