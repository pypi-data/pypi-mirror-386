
import setuptools

setuptools.setup(
    name="certora-cli-alpha-master",
    version="20251023.10.8.551987",
    author="Certora",
    author_email="support@certora.com",
    description="Runner for the Certora Prover",
    long_description="Commit cae2704.                    Build and Run scripts for executing the Certora Prover on Solidity smart contracts.",
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/certora-cli-alpha-master",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['click', 'json5', 'pycryptodome', 'requests', 'rich', 'sly', 'tabulate', 'tqdm', 'StrEnum', 'universalmutator', 'jinja2', 'wcmatch', 'typing_extensions'],
    project_urls={
        'Documentation': 'https://docs.certora.com/en/latest/',
        'Source': 'https://github.com/Certora/CertoraProver',
    },
    license="GPL-3.0-only",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "certoraRun = certora_cli.certoraRun:entry_point",
            "certoraMutate = certora_cli.certoraMutate:mutate_entry_point",
            "certoraEqCheck = certora_cli.certoraEqCheck:equiv_check_entry_point",
            "certoraSolanaProver = certora_cli.certoraSolanaProver:entry_point",
            "certoraSorobanProver = certora_cli.certoraSorobanProver:entry_point",
            "certoraEVMProver = certora_cli.certoraEVMProver:entry_point",
            "certoraRanger = certora_cli.certoraRanger:entry_point",
            "certoraSuiProver = certora_cli.certoraSuiProver:entry_point",
            "certoraCVLFormatter = certora_cli.certoraCVLFormatter:entry_point"
        ]
    },
    python_requires='>=3.9',
)
