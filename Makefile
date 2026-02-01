PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin

all: build

build:
	@echo "📦 Подготовка окружения..."
	python3 -m venv .venv
	.venv/bin/pip install -q pyyaml textual pyperclip pyinstaller
	@echo "🔨 Сборка snipv..."
	.venv/bin/pyinstaller --noconfirm --onefile --console --name snipv --collect-all rich main.py

install: build
	@echo "🚀 Установка в $(BINDIR)..."
	@mkdir -p $(BINDIR)
	@cp dist/snipv $(BINDIR)/
	@chmod +x $(BINDIR)/snipv
	@echo "✅ Готово! Напиши 'snipv' для запуска."

clean:
	sudo rm -rf build dist .venv *.spec
