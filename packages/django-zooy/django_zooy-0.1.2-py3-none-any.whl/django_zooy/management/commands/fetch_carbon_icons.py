import urllib.request
import json
import tarfile
import io
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = (
        'Download Carbon Design System icons from npm to CARBON_ICONS_PATH.\n\n'
        'Setup:\n'
        '  1. Add to settings.py: CARBON_ICONS_PATH = BASE_DIR / "carbon-icons"\n'
        '  2. Run: python manage.py fetch_carbon_icons\n'
        '  3. Icons will be downloaded to the specified path'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force download even if directory exists and is not empty',
        )

    def handle(self, *args, **options):
        # Get the path from settings
        try:
            icons_path = settings.CARBON_ICONS_PATH
        except AttributeError:
            raise CommandError(
                'CARBON_ICONS_PATH is not set in Django settings.\n'
                'Add to your settings.py:\n'
                '  CARBON_ICONS_PATH = BASE_DIR / "carbon-icons"'
            )

        output_path = Path(icons_path)

        # Check if a directory exists and has content
        if output_path.exists() and any(output_path.iterdir()):
            if not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Directory {output_path} already exists and is not empty. '
                        'Use --force to overwrite.'
                    )
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING(f'Overwriting existing icons in {output_path}')
                )

        # Create a directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Get the latest version info from npm registry
        registry_url = "https://registry.npmjs.org/@carbon/icons/latest"

        self.stdout.write('Fetching latest Carbon Icons version...')

        try:
            with urllib.request.urlopen(registry_url) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            raise CommandError(f'Failed to fetch package info: {e}')

        # Get the tarball URL and version
        tarball_url = data['dist']['tarball']
        version = data['version']

        self.stdout.write(f'Downloading Carbon Icons v{version}...')
        self.stdout.write(f'From: {tarball_url}')

        # Download the tarball
        try:
            with urllib.request.urlopen(tarball_url) as response:
                tarball_data = response.read()
        except Exception as e:
            raise CommandError(f'Failed to download tarball: {e}')

        # Extract only the svg directory
        self.stdout.write('Extracting SVG files...')

        try:
            with tarfile.open(fileobj=io.BytesIO(tarball_data), mode='r:gz') as tar:
                # Filter for only svg files
                svg_members = [
                    member for member in tar.getmembers()
                    if member.name.startswith('package/svg/')
                ]

                for member in svg_members:
                    # Strip the 'package/svg/' prefix
                    member.name = member.name.replace('package/svg/', '', 1)
                    tar.extract(member, path=output_path)
        except Exception as e:
            raise CommandError(f'Failed to extract files: {e}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully downloaded {len(svg_members)} Carbon Icons '
                f'(v{version}) to {output_path}'
            )
        )