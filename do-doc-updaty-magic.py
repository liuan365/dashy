#!/usr/bin/env python3
"""
Dashy Documentation Updater for Docusaurus
Fetches latest docs from master and applies Docusaurus compatibility fixes.
"""

import os
import re
import glob
import subprocess
import sys
import shutil

def run_cmd(cmd, desc, allow_fail=False):
    """Run shell command, return True on success."""
    print(f"📋 {desc}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 or (allow_fail and "Generated static files" in result.stdout):
            print(f"✅ {desc}")
            return True
        print(f"❌ {desc}\n{result.stderr}")
        return False
    except Exception as e:
        print(f"❌ {desc}: {e}")
        return False

def download_docs():
    """Download latest docs from master branch."""
    print("🚀 Starting documentation update...")
    shutil.rmtree('temp_docs', ignore_errors=True)

    cmds = [
        ('mkdir -p temp_docs', 'Create temp directory'),
        ('git fetch origin master', 'Fetch master branch'),
        ('git archive origin/master docs/ | tar -x -C temp_docs', 'Download docs'),
        ('cp -r temp_docs/docs/* docs/', 'Copy to docs directory'),
    ]
    for cmd, desc in cmds:
        if not run_cmd(cmd, desc):
            return False
    shutil.rmtree('temp_docs', ignore_errors=True)
    return True

def fix_markdown_file(filepath):
    """Apply Docusaurus compatibility fixes to a markdown file."""
    print(f"🔧 Processing: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = original = f.read()
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False

    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Remove <p> blocks that contain markdown (images, lists) - these break JSX
    # Match <p ...> ... </p> where content spans multiple lines
    content = re.sub(r'<p[^>]*>\s*\n(.*?)\n\s*</p>', r'\1', content, flags=re.DOTALL)

    # Also remove single-line <p align=...> wrappers around images
    content = re.sub(r'<p[^>]*>\s*(\[?!?\[.*?\].*?)\s*</p>', r'\1', content)

    # Fix self-closing tags
    content = re.sub(r'<br\s*/?>', '<br />', content)
    content = re.sub(r'<hr\s*/?>', '<hr />', content)
    content = re.sub(r'<img([^>]*[^/])>', r'<img\1 />', content)

    # Remove problematic SVG charts
    content = re.sub(r'\[!\[Stargazers\].*?starchart\.cc.*?\)', '', content, flags=re.DOTALL)
    content = re.sub(r'\[!\[Contributors\].*?contrib\.rocks.*?\)', '', content, flags=re.DOTALL)

    # Remove details tags, convert to headings
    content = re.sub(r'<details[^>]*>\s*<summary>([^<]+)</summary>\s*', r'### \1\n\n', content)
    content = re.sub(r'</details>', '', content)

    # Back to top links
    content = re.sub(r'\[⬆️ Back to Top\]\([^)]*\)', '**[⬆️ Back to Top](#)**', content)
    content = re.sub(r'<p[^>]*>\s*<a[^>]*>⬆️ Back to Top</a>\s*</p>', '**[⬆️ Back to Top](#)**', content)

    # GitHub blob links to relative
    content = re.sub(r'https://github\.com/[^/]+/[^/]+/blob/[^/]+/docs/([^)]+)', r'/docs/\1', content)

    # Fix links: remove .md extension first
    content = re.sub(r'\]\(([^)]+)\.md\)', r'](\1)', content)

    # Fix relative links - convert ./X and ../X to /docs/X
    content = re.sub(r'\]\(\./([^)]+)\)', r'](/docs/\1)', content)
    content = re.sub(r'\]\(\.\./([^)]+)\)', r'](/docs/\1)', content)
    content = re.sub(r'\]\(docs/([^)]+)\)', r'](/docs/\1)', content)

    # Fix bare links that should be docs (e.g., backup-restore -> /docs/backup-restore)
    def fix_doc_link(m):
        link = m.group(1)
        if link.startswith(('http', '/', '#', 'mailto:')):
            return m.group(0)
        if '.' in link and not link.endswith(('.md', '.html')):
            return m.group(0)
        return f'](/docs/{link})'

    content = re.sub(r'\]\(([^)]+)\)', fix_doc_link, content)

    # Clean up any /docs/docs/ that might have been created
    content = re.sub(r'/docs/docs/', '/docs/', content)

    # Cleanup whitespace
    content = re.sub(r'\n\n\n+', '\n\n', content).strip() + '\n'

    if content != original:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
        except Exception as e:
            print(f"❌ Error writing {filepath}: {e}")
            return False
    else:
        print(f"ℹ️  No changes: {filepath}")
    return True

def process_all_docs():
    """Process all markdown files in docs directory."""
    if not os.path.exists('docs'):
        print("❌ docs directory not found!")
        return False

    md_files = glob.glob('docs/**/*.md', recursive=True)
    if not md_files:
        print("❌ No markdown files found")
        return False

    print(f"📚 Found {len(md_files)} markdown files...")
    success = sum(1 for f in md_files if fix_markdown_file(f))
    print(f"\n🎉 Processed {success}/{len(md_files)} files")
    return success == len(md_files)

def test_build():
    """Test Docusaurus build."""
    print("🧪 Testing build...")
    run_cmd("pkill -f 'docusaurus start' || true", "Stop dev servers", allow_fail=True)

    result = subprocess.run("npm run build", shell=True, capture_output=True, text=True)
    if "Generated static files" in result.stdout:
        print("✅ Build successful!")
        return True
    print(f"❌ Build failed\n{result.stderr}")
    return False

def main():
    print("=" * 50)
    print("🚀 Dashy Documentation Updater")
    print("=" * 50)

    for check in ['package.json', 'docusaurus.config.js']:
        if not os.path.exists(check):
            print(f"❌ {check} not found - run from project root")
            sys.exit(1)

    steps = [
        ("Download docs", download_docs),
        ("Process markdown", process_all_docs),
        ("Test build", test_build),
    ]

    for name, func in steps:
        print(f"\n📥 {name}\n" + "-" * 40)
        if not func():
            print(f"\n❌ Failed: {name}")
            sys.exit(1)

    print("\n" + "=" * 50)
    print("🎉 Documentation updated successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
