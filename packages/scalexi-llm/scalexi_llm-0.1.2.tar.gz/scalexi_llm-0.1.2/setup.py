from setuptools import setup, find_packages

# Read README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="scalexi_llm",
    version="0.1.2",
    author="scalex_innovation",
    description="A comprehensive multi-provider LLM proxy library with unified interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scalexi/scalexi_llm",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "openai",
        "anthropic",
        "google-genai",
        "groq",
        "pymupdf",
        "xai-sdk",
        "python-docx",
        "pydantic",
        "python-dotenv",
        "exa_py",
        "google-search-results"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    keywords="llm, ai, openai, anthropic, gemini, groq, deepseek, grok, qwen, exa, proxy, api",
)