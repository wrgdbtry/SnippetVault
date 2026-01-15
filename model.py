import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class Snippet:

    id: int
    title: str
    language: str
    code: str
    tags: List[str]

    def matches_search(self, query: str) -> bool:
        query = query.lower()
        return (
            query in self.title.lower() or
            query in self.language.lower() or
            any(query in tag.lower() for tag in self.tags)
        )


class SnippetManager:

    def __init__(self, filepath: str = "snippets.json"):
        self.filepath = Path(filepath)
        self.snippets: List[Snippet] = []
        self._load_snippets()

    def _load_snippets(self) -> None:
        if not self.filepath.exists():
            self._create_default_snippets()
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.snippets = [Snippet(**item) for item in data]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка загрузки: {e}")
            self.snippets = []

    def _save_to_file(self) -> None:
        with open(self.filepath, 'w', encoding='utf-8') as f:
            data = [asdict(s) for s in self.snippets]
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _create_default_snippets(self) -> None:
        self.snippets = [
            Snippet(
                id=1,
                title="Распаковка tar.gz",
                language="bash",
                code="tar -xzvf archive.tar.gz",
                tags=["linux", "archive", "compression"]
            ),
            Snippet(
                id=2,
                title="Python HTTP сервер",
                language="bash",
                code="python -m http.server 8000",
                tags=["python", "server", "quick"]
            ),
            Snippet(
                id=3,
                title="Git отмена последнего коммита",
                language="bash",
                code="git reset --soft HEAD~1",
                tags=["git", "undo"]
            ),
            Snippet(
                id=4,
                title="Docker Compose шаблон",
                language="yaml",
                code='''version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DEBUG=true''',
                tags=["docker", "template"]
            ),
            Snippet(
                id=5,
                title="Python virtualenv",
                language="bash",
                code='''# Создание
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\\Scripts\\activate''',
                tags=["python", "venv", "environment"]
            ),
            Snippet(
                id=6,
                title="SQL выборка с JOIN",
                language="sql",
                code='''SELECT 
    u.name,
    o.order_date,
    o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.total > 100
ORDER BY o.order_date DESC;''',
                tags=["sql", "join", "query"]
            ),
            Snippet(
                id=7,
                title="Python декоратор таймера",
                language="python",
                code='''import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)''',
                tags=["python", "decorator", "performance"]
            ),
            Snippet(
                id=8,
                title="Найти большие файлы Linux",
                language="bash",
                code="find / -type f -size +100M 2>/dev/null | head -20",
                tags=["linux", "find", "disk"]
            ),
        ]
        self._save_to_file()

    def get_all(self) -> List[Snippet]:
        return self.snippets

    def get_by_id(self, snippet_id: int) -> Optional[Snippet]:
        for snippet in self.snippets:
            if snippet.id == snippet_id:
                return snippet
        return None

    def get_languages(self) -> List[str]:
        languages = set(s.language for s in self.snippets)
        return sorted(languages)

    def get_by_language(self, language: str) -> List[Snippet]:
        if language.lower() == "all":
            return self.snippets
        return [s for s in self.snippets if s.language.lower() == language.lower()]

    def search(self, query: str, language: Optional[str] = None) -> List[Snippet]:
        if not query:
            if language:
                return self.get_by_language(language)
            return self.snippets

        results = [s for s in self.snippets if s.matches_search(query)]

        if language and language.lower() != "all":
            results = [s for s in results if s.language.lower() == language.lower()]

        return results

    def add(self, title: str, language: str, code: str, tags: List[str]) -> Snippet:
        new_id = max((s.id for s in self.snippets), default=0) + 1
        snippet = Snippet(
            id=new_id,
            title=title,
            language=language,
            code=code,
            tags=tags
        )
        self.snippets.append(snippet)
        self._save_to_file()
        return snippet

    def update(self, snippet_id: int, **kwargs) -> Optional[Snippet]:
        snippet = self.get_by_id(snippet_id)
        if snippet:
            for key, value in kwargs.items():
                if hasattr(snippet, key) and key != 'id':
                    setattr(snippet, key, value)
            self._save_to_file()
        return snippet

    def delete(self, snippet_id: int) -> bool:
        snippet = self.get_by_id(snippet_id)
        if snippet:
            self.snippets.remove(snippet)
            self._save_to_file()
            return True
        return False
