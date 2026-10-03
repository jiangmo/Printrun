"""Compile gettext catalogs before running from source or packaging."""
from pathlib import Path
import polib


def main():
    root = Path(__file__).resolve().parents[1]
    for path in sorted((root / 'locale').glob('*/LC_MESSAGES/*.po')):
        catalog = polib.pofile(str(path))
        catalog.save_as_mofile(str(path.with_suffix('.mo')))
        print(f'{path.relative_to(root)}: {catalog.percent_translated():.1f}%')


if __name__ == '__main__':
    main()
