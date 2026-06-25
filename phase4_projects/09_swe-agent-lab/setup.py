from setuptools import find_packages, setup

setup(
    name="mini-swe-agent",
    version="0.1.0",
    description="轻量级 SWE-agent 学习实现 — 代码修复 Agent",
    author="cxllm",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "openai>=1.55.0",
        "anthropic>=0.47.0",
        "pyyaml>=6.0",
        "rich>=13.0",
        "requests>=2.32.0",
    ],
    extras_require={
        "dev": ["pytest>=8.0", "pytest-cov>=5.0"],
    },
)
