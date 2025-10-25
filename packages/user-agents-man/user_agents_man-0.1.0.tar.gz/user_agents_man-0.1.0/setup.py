from setuptools import setup, find_packages
import os

setup(
    name='user-agents-man',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pyTelegramBotAPI>=4.0.0',
        'psutil>=5.0.0',
        'requests>=2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'user-agents-man = user_agents_man.bot:main',
        ]
    },
    author='fakeobelix',  # Ganti dengan nama Anda
    author_email='kintilkiris@gmail.com',  # Ganti dengan email Anda
    description='Bot Telegram untuk mengelola file dan info server.',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Pilih license sesuai keinginan
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)