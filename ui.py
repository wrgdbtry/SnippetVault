from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import (
    Header, Footer, ListView, ListItem,
    Label, Static, Input, Button, TextArea
)
from textual.binding import Binding
from textual.screen import ModalScreen
from rich.syntax import Syntax
from rich.panel import Panel

from typing import List, Optional

import yaml 

def load_config():
    """Загрузка конфигурации"""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"lang": "en"}
    except FileNotFoundError:
        # Создаём дефолтный конфиг
        default_config = {"lang": "en"}
        with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(default_config, f)
        return default_config

def load_language(lang_code):
    """Загрузка языкового файла"""
    try:
        with open(f"{lang_code}.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Warning: Language file {lang_code}.yaml not found")
        return {}

# Загружаем конфиг и язык
config = load_config()
lang = load_language(config.get("lang", "en")

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from model import SnippetManager, Snippet


class CodeView(Static):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_snippet: Optional[Snippet] = None

    def show_snippet(self, snippet: Snippet) -> None:
        self.current_snippet = snippet

        syntax = Syntax(
            snippet.code,
            snippet.language,
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )

        tags_str = ", ".join(f"#{tag}" for tag in snippet.tags)

        self.update(Panel(
            syntax,
            title=f"[bold cyan]{snippet.title}[/bold cyan]",
            subtitle=f"[dim]{snippet.language} | {tags_str}[/dim]",
            border_style="green"
        ))

    def show_placeholder(self, message: str = None) -> None:
        if message is None:
            message = lang.get("select_snippet_first", "Select a snippet")
        self.current_snippet = None
        self.update(Panel(
            f"[dim italic]{message}[/dim italic]",
            border_style="dim"
        ))


class LanguageItem(ListItem):

    def __init__(self, language: str, count: int, **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.count = count

    def compose(self) -> ComposeResult:
        icon = self._get_icon()
        yield Label(f"{icon} {self.language.capitalize()} ({self.count})")

    def _get_icon(self) -> str:
        icons = {
            "python": "",
            "bash": "",
            "sql": "",
            "yaml": "",
            "javascript": "",
            "rust": "",
            "all": ""
        }
        return icons.get(self.language.lower(), "")


class SnippetItem(ListItem):

    def __init__(self, snippet: Snippet, **kwargs):
        super().__init__(**kwargs)
        self.snippet = snippet

    def compose(self) -> ComposeResult:
        yield Label(f"  {self.snippet.title}")


class AddSnippetScreen(ModalScreen):

    CSS = """
    AddSnippetScreen {
        align: center middle;
    }
    
    #add-dialog {
        width: 80;
        height: auto;
        max-height: 90%;
        padding: 1 2;
        background: $surface;
        border: thick $primary;
        overflow-y: auto;
    }
    
    #add-dialog Label {
        margin-top: 1;
        height: 1;
    }
    
    #add-dialog Input {
        margin-bottom: 1;
        height: 3;
    }
    
    #code-area {
        height: 10;
        margin-bottom: 1;
    }
    
    #buttons {
        margin-top: 2;
        height: 3;
        align: center middle;
        dock: bottom;
    }
    
    #buttons Button {
        margin: 0 2;
    }
    
    #dialog-title {
        text-align: center;
        text-style: bold;
        color: $text;
        background: $primary;
        width: 100%;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="add-dialog"):
            yield Label(f'  {lang.get("new_snippet", "Create snippet")}', id="dialog-title")

            yield Label(f'{lang.get("title", "Title")}:')
            yield Input(placeholder=f'{lang.get("example", "Example")}: Docker build', id="title-input")

            yield Label(f'{lang.get("language", "Language")}:')
            yield Input(placeholder="python, bash, sql, yaml...", id="lang-input")

            yield Label(f'{lang.get("tags", "Tags")}:')
            yield Input(placeholder="docker, deploy, quick", id="tags-input")

            yield Label(f'{lang.get("code", "Code")}:')
            yield TextArea(id="code-area")

            with Horizontal(id="buttons"):
                yield Button(lang.get("save", "Save"), variant="success", id="save-btn")
                yield Button(lang.get("cancel_action", "Cancel"), variant="error", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._save_snippet()
        else:
            self.app.pop_screen()

    def _save_snippet(self):
        title = self.query_one("#title-input", Input).value.strip()
        language = self.query_one("#lang-input", Input).value.strip().lower()
        tags_str = self.query_one("#tags-input", Input).value.strip()
        code = self.query_one("#code-area", TextArea).text

        if not all([title, language, code]):
            self.notify(lang.get("not_enough_parametrs", "Fill all fields!"), severity="error")
            return

        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        app = self.app
        if isinstance(app, SnippetVaultApp):
            app.manager.add(
                title=title,
                language=language,
                code=code,
                tags=tags
            )
            app.refresh_all_lists()
            self.notify(f"  {lang.get('added', 'Added')}: {title}", severity="information")

        self.app.pop_screen()

    def action_cancel(self) -> None:
        self.app.pop_screen()


class SnippetVaultApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }
    
    #main-container {
        height: 1fr;
    }
    
    #sidebar {
        width: 36;
        background: $panel;
        border-right: tall $primary;
        padding: 0 1;
    }
    
    #sidebar-title {
        text-align: center;
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 0 1;
        margin-bottom: 1;
    }
    
    #languages-list {
        height: auto;
        max-height: 12;
        margin-bottom: 1;
    }
    
    #snippets-section {
        height: 1fr;
    }
    
    #snippets-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }
    
    #snippets-list {
        height: 1fr;
    }
    
    #content {
        width: 1fr;
        padding: 1;
    }
    
    #search-bar {
        dock: top;
        height: 3;
        padding: 0 1;
        background: $boost;
    }
    
    #search-input {
        width: 100%;
    }
    
    #code-view {
        height: 1fr;
    }
    
    ListItem {
        padding: 0 1;
    }
    
    ListItem:hover {
        background: $boost;
    }
    
    ListView:focus > ListItem.--highlight {
        background: $accent;
    }
    """

    TITLE = " SnippetVault"
    SUB_TITLE = "Your code vault"

    BINDINGS = [
        Binding("q", "quit", lang.get("quit", "Quit")),
        Binding("c", "copy_code", lang.get("copy_code", "Copy")),
        Binding("a", "add_snippet", lang.get("add_snippet", "Add")),
        Binding("d", "delete_snippet", lang.get("delete_snippet", "Delete")),
        Binding("/", "focus_search", lang.get("focus_search", "Search")),
        Binding("l", "lang_switch", "Lang"),
        Binding("escape", "clear_search", lang.get("clear_search", "Clear")),
    ]

    def __init__(self):
        super().__init__()
        self.manager = SnippetManager()
        self.current_language = "all"
        self.current_snippets: List[Snippet] = []
        self._list_counter = 0

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield Static(f" {lang.get('categories', 'Categories')}", id="sidebar-title")
                yield ListView(id="languages-list")

                with Vertical(id="snippets-section"):
                    yield Static(f" {lang.get('snippets', 'Snippets')}", id="snippets-title")
                    yield ListView(id="snippets-list")

            with Vertical(id="content"):
                with Container(id="search-bar"):
                    yield Input(
                        placeholder=f" {lang.get('search_placeholder', 'Search...')}",
                        id="search-input"
                    )
                yield CodeView(id="code-view")

        yield Footer()

    def on_mount(self) -> None:
        self._populate_languages()
        self._populate_snippets()
        self.query_one("#code-view", CodeView).show_placeholder()

    def _get_unique_id(self, prefix: str) -> str:
        self._list_counter += 1
        return f"{prefix}-{self._list_counter}"

    def _populate_languages(self) -> None:
        languages_list = self.query_one("#languages-list", ListView)
        languages_list.clear()

        all_count = len(self.manager.get_all())
        languages_list.mount(
            LanguageItem("all", all_count, id=self._get_unique_id("lang"))
        )

        for language in self.manager.get_languages():
            count = len(self.manager.get_by_language(language))
            languages_list.mount(
                LanguageItem(language, count, id=self._get_unique_id("lang"))
            )

    def _populate_snippets(self, snippets: Optional[List[Snippet]] = None) -> None:
        snippets_list = self.query_one("#snippets-list", ListView)
        snippets_list.clear()

        if snippets is None:
            snippets = self.manager.get_by_language(self.current_language)

        self.current_snippets = snippets

        for snippet in snippets:
            snippets_list.mount(
                SnippetItem(snippet, id=self._get_unique_id("snip"))
            )

        if not snippets:
            self.query_one("#code-view", CodeView).show_placeholder(
                lang.get("no_snippets", "No snippets")
            )

    def refresh_all_lists(self) -> None:
        self._populate_languages()
        self._populate_snippets()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item

        if isinstance(item, LanguageItem):
            self.current_language = item.language
            self._populate_snippets()
            self.query_one("#code-view", CodeView).show_placeholder()

        elif isinstance(item, SnippetItem):
            self.query_one("#code-view", CodeView).show_snippet(item.snippet)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            query = event.value
            results = self.manager.search(query, self.current_language)
            self._populate_snippets(results)

    def action_lang_switch(self) -> None:
        global lang, config
        
        current_lang = config.get("lang", "en")
        new_lang = "en" if current_lang == "ru" else "ru"
        
        config["lang"] = new_lang
        with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

        lang = load_language(new_lang)
        self.recompose()
        self.notify(f"Language was switched to {new_lang.upper()}. Please restart an app")

    def action_copy_code(self) -> None:
        code_view = self.query_one("#code-view", CodeView)

        if code_view.current_snippet:
            if CLIPBOARD_AVAILABLE:
                try:
                    pyperclip.copy(code_view.current_snippet.code)
                    self.notify(
                        f" {lang.get('copied', 'Copied')}: {code_view.current_snippet.title}",
                        severity="information"
                    )
                except Exception as e:
                    self.notify(f" {lang.get('error', 'Error')}: {e}", severity="error")
            else:
                self.notify(
                    f" {lang.get('clipboard_not_installed', 'pyperclip not installed')}", 
                    severity="warning"
                )
        else:
            self.notify(
                f" {lang.get('select_snippet_first', 'Select a snippet first')}", 
                severity="warning"
            )

    def action_add_snippet(self) -> None:
        self.push_screen(AddSnippetScreen())

    def action_delete_snippet(self) -> None:
        code_view = self.query_one("#code-view", CodeView)

        if code_view.current_snippet:
            title = code_view.current_snippet.title
            self.manager.delete(code_view.current_snippet.id)
            self.refresh_all_lists()
            code_view.show_placeholder()
            self.notify(
                f" {lang.get('deleted', 'Deleted')}: {title}", 
                severity="warning"
            )
        else:
            self.notify(
                f" {lang.get('select_snippet_first', 'Select a snippet first')}", 
                severity="warning"
            )

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self._populate_snippets()


if __name__ == "__main__":
    app = SnippetVaultApp()
    app.run()
