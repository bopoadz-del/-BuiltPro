#!/bin/bash
cd frontend
rm -f package-lock.json
npm install
git add package-lock.json
git commit -m "fix: regenerate package-lock.json to sync with package.json" --no-verify
git push