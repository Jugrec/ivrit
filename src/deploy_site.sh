#!/bin/bash
# Build the standalone site and push it, together with the sources (src/), to GitHub Pages (Jugrec/ivrit, branch main).
#   bash deploy_site.sh "commit message"
set -e
MSG="${1:-Обновить приложение}"
python3 -I /home/claude/ivrit/build/make_site.py /home/claude/ivrit /home/claude/ivrit-site
[ -d /home/claude/ivrit-gh/.git ] || git clone --depth 1 https://github.com/Jugrec/ivrit /home/claude/ivrit-gh
cd /home/claude/ivrit-gh
git fetch -q origin main && git reset -q --hard origin/main
find . -mindepth 1 -maxdepth 1 ! -name .git ! -name README.md ! -name .nojekyll -exec rm -rf {} +
cp -r /home/claude/ivrit-site/. ./
touch .nojekyll
# sources of the course (builders, word lists, tests, the page before make_site) live next to the site in src/,
# because the Claude project has no room for them: everything can be rebuilt from this folder
mkdir -p src && cp -r /home/claude/ivrit/build/. src/ && rm -rf src/__pycache__ src/index.html.copy
cp /home/claude/ivrit/index.html src/index.src.html
git add -A
if git diff --cached --quiet; then echo "nothing to deploy"; exit 0; fi
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -qm "$MSG

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BbUnvDc2v45GN8xBXvFc6N"
git push -q origin HEAD:main
git log --oneline -1
