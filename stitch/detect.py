from pathlib import Path


STACK_SIGNALS = {
    "requirements.txt": "Python",
    "setup.py": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "package.json": "Node.js",
    "tsconfig.json": "TypeScript",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby",
    "pom.xml": "Java",
    "build.gradle": "Java",
    "build.gradle.kts": "Kotlin",
    "composer.json": "PHP",
    "mix.exs": "Elixir",
    "pubspec.yaml": "Dart/Flutter",
    "CMakeLists.txt": "C/C++",
    "Makefile": "C/C++",
    "*.csproj": "C#/.NET",
    "*.sln": "C#/.NET",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
    ".terraform": "Terraform",
    "main.tf": "Terraform",
}

FRAMEWORK_SIGNALS = {
    "manage.py": "Django",
    "app.py": "Flask",
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "next.config.ts": "Next.js",
    "nuxt.config.ts": "Nuxt",
    "angular.json": "Angular",
    "svelte.config.js": "SvelteKit",
    "tailwind.config.js": "Tailwind CSS",
    "tailwind.config.ts": "Tailwind CSS",
    "vite.config.ts": "Vite",
    "vite.config.js": "Vite",
    "webpack.config.js": "Webpack",
    "prisma": "Prisma",
    ".env": "dotenv",
}


def detect_project_name(project_dir: Path) -> str:
    return project_dir.name


def detect_tech_stack(project_dir: Path) -> list[str]:
    stack = set()
    entries = {e.name for e in project_dir.iterdir()}

    for filename, tech in STACK_SIGNALS.items():
        if filename.startswith("*"):
            ext = filename[1:]
            if any(e.endswith(ext) for e in entries):
                stack.add(tech)
        elif filename in entries:
            stack.add(tech)

    for filename, tech in FRAMEWORK_SIGNALS.items():
        if filename in entries:
            stack.add(tech)

    if not stack:
        src_files = list(project_dir.glob("*.py"))
        if src_files:
            stack.add("Python")
        src_files = list(project_dir.glob("*.js"))
        if src_files:
            stack.add("JavaScript")

    return sorted(stack)
