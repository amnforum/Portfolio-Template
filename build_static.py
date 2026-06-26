import os
import shutil
import subprocess
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_project.settings')

import django

django.setup()

from django.conf import settings
from django.contrib.staticfiles import finders

BASE_DIR = Path(__file__).resolve().parent


def build_css():
    if os.getenv('SKIP_CSS_BUILD') == '1':
        print('Skipping CSS build because SKIP_CSS_BUILD=1')
        return

    if not (BASE_DIR / 'package.json').exists():
        print('Skipping CSS build because package.json is missing')
        return

    npm_command = 'npm.cmd' if os.name == 'nt' else 'npm'
    print('Building Tailwind CSS...')
    subprocess.run([npm_command, 'run', 'build:css'], cwd=BASE_DIR, check=True)


def collect_static():
    static_source = BASE_DIR / 'static'
    target_root = Path(settings.STATIC_ROOT)
    if target_root.resolve() == static_source.resolve():
        print(f'Using source static directory at {target_root}; skipping copy step.')
        copied = 0
    else:
        if target_root.exists():
            shutil.rmtree(target_root)
        target_root.mkdir(parents=True, exist_ok=True)

        print(f'Copying static files into {settings.STATIC_ROOT}...')
        copied = 0
        seen = set()

        for finder in finders.get_finders():
            for relative_path, storage in finder.list(ignore_patterns=[]):
                normalized = relative_path.replace('\\', '/')
                if normalized in seen:
                    continue
                seen.add(normalized)

                destination = target_root / Path(normalized)
                destination.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy2(storage.path(relative_path), destination)
                except NotImplementedError:
                    with storage.open(relative_path, 'rb') as source_file:
                        destination.write_bytes(source_file.read())

                copied += 1

    expected_files = [
        Path(settings.STATIC_ROOT) / 'css' / 'output.css',
        Path(settings.STATIC_ROOT) / 'css' / 'portfolio.css',
        Path(settings.STATIC_ROOT) / 'css' / 'kurama.css',
    ]
    missing = [str(path) for path in expected_files if not path.exists()]
    if missing:
        raise FileNotFoundError(
            'Static build completed but expected files were missing: '
            + ', '.join(missing)
        )

    print(f'Static build completed successfully. Copied {copied} files.')


if __name__ == '__main__':
    build_css()
    collect_static()
