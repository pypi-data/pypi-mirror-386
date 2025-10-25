from setuptools import setup, find_packages
import os

# Lire le README
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Vue.js-like framework for Python - Build modern web apps with Python syntax"

# Dépendances principales - DIRECTEMENT dans le code pour éviter les problèmes
install_requires = [
    "watchdog>=2.0.0",
    "click>=8.0.0",
]

# Fonction pour trouver automatiquement tous les fichiers de templates
def find_template_files():
    template_files = []
    template_dir = os.path.join("tala", "cli", "templates")
    
    if os.path.exists(template_dir):
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                # Chemin relatif depuis le dossier tala
                rel_path = os.path.relpath(os.path.join(root, file), "tala")
                template_files.append(rel_path)
    
    return template_files

setup(
    name="tala-frame",
    version="1.0.0",
    author="Tala Team",
    author_email="hello@tala.dev",
    description="Vue.js-like framework for Python - Build modern web apps with Python syntax",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tala/tala",
    project_urls={
        "Homepage": "https://tala.dev",
        "Documentation": "https://docs.tala.dev", 
        "Repository": "https://github.com/tala/tala",
        "Bug Reports": "https://github.com/tala/tala/issues",
        "Changelog": "https://github.com/tala/tala/releases",
    },
    packages=find_packages(include=["tala", "tala.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content", 
        "Topic :: Software Development :: User Interfaces",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,  # ✅ Utilise la liste directe
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=3.0", 
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
            "twine>=4.0",
            "build>=0.7",
        ],
        "docs": [
            "mkdocs>=1.4",
            "mkdocs-material>=8.0",
        ],
        "full": [  # ✅ Option "full" avec toutes les dépendances
            "watchdog>=2.0.0",
            "aiohttp>=3.8.0",
            "Jinja2>=3.0.0",
            "click>=8.0.0",
            "colorama>=0.4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "tala=tala.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "tala": [
            "cli/templates/**/*",           # Tous les fichiers
            "cli/templates/**/.*",          # Fichiers cachés
            "cli/templates/**/*.tala",      # Fichiers .tala
            "cli/templates/**/*.py",        # Fichiers Python
            "cli/templates/**/*.toml",      # Fichiers de configuration
            "cli/templates/**/*.css",       # Fichiers CSS
            "cli/templates/**/*.md",        # Documentation
            "cli/templates/**/*.html",      # Fichiers HTML
            "cli/templates/**/*.js",        # Fichiers JavaScript
        ],
    },
    keywords=[
        "vue", 
        "frontend", 
        "framework", 
        "reactive", 
        "web", 
        "components",
        "python",
        "javascript", 
        "spa",
        "router"
    ],
    license="MIT",
    platforms=["any"],
    zip_safe=False,
)