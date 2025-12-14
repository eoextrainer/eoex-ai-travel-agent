#!/usr/bin/env bash
set -euo pipefail

# Config
DOWNSTREAM_REMOTE="origin"
UPSTREAM_REMOTE="origin"
INT_BRANCH="int"

commit_msg() {
  local desc="$1"; local ver_major="$2"; local ver_minor="$3"; local ver_patch="$4"
  echo "[eoex-ai-travel-agent-${desc}-SGJ-v${ver_major}.${ver_minor}.${ver_patch}]"
}

ensure_git() {
  git config user.name "Sosthene Grosset-Janin"
  git config user.email "educ1.eoex@gmail.com"
}

pull_downstream_main() { git checkout main && git pull ${DOWNSTREAM_REMOTE} main; }
sync_branch() { local b="$1"; git checkout "$b" && git merge --no-edit main || true; }
stash_all() { local msg="$1"; git stash push -u -m "$msg"; }
stage_all() { git add -A; }
commit_all() { local msg="$1"; git commit -m "$msg" || true; }
merge_to_test() { git checkout test && git merge --no-edit "$1" || true; }
open_frontend() { xdg-open "http://localhost:8000" >/dev/null 2>&1 || true; }
archive_patch() { local msg="$1"; git checkout archive && git merge --no-edit test || true; git commit --allow-empty -m "$msg" || true; }
ready_and_push() { git checkout ready && git merge --no-edit test || true; git push ${DOWNSTREAM_REMOTE} ready:${INT_BRANCH} || true; }

run_workflow_new_dev() {
  local feature_name="$1"; local ver_major="$2"; local ver_minor="$3"; local ver_patch="$4"
  ensure_git
  pull_downstream_main
  sync_branch develop
  sync_branch feature
  git checkout -b "feat-${feature_name}" feature
  stash_all "new development: ${feature_name}"
  stage_all
  commit_all "$(commit_msg "app setup" "$ver_major" "$ver_minor" "$ver_patch")"
  merge_to_test "feat-${feature_name}"
  echo "Run tests and manual checks..."
  open_frontend
  archive_patch "[eoex-ai-travel-agent-app project archive-SGJ-v${ver_major}.${ver_minor}.${ver_patch}]"
  ready_and_push
  echo "Create pull/merge request manually in GitHub UI."
}

run_workflow_feature() {
  local feature_branch="$1"; local ver_major="$2"; local ver_minor="$3"; local ver_patch="$4"
  ensure_git
  pull_downstream_main
  sync_branch develop
  sync_branch feature
  git checkout "$feature_branch"
  stash_all "feature enhancement: ${feature_branch}"
  stage_all
  commit_all "$(commit_msg "feature enhancement" "$ver_major" "$ver_minor" "$ver_patch")"
  merge_to_test "$feature_branch"
  echo "Run tests and manual checks..."
  open_frontend
  archive_patch "[eoex-ai-travel-agent-app project archive-SGJ-v${ver_major}.${ver_minor}.${ver_patch}]"
  ready_and_push
  echo "Create pull/merge request manually in GitHub UI."
}

run_workflow_bugfix() {
  local bug_name="$1"; local ver_major="$2"; local ver_minor="$3"; local ver_patch="$4"
  ensure_git
  pull_downstream_main
  sync_branch develop
  sync_branch fix
  git checkout -b "bugfix-${bug_name}" fix
  stash_all "bugfix: ${bug_name}"
  stage_all
  commit_all "$(commit_msg "bugfix" "$ver_major" "$ver_minor" "$ver_patch")"
  merge_to_test "bugfix-${bug_name}"
  echo "Run tests and manual checks..."
  open_frontend
  archive_patch "[eoex-ai-travel-agent-app project archive-SGJ-v${ver_major}.${ver_minor}.${ver_patch}]"
  ready_and_push
  echo "Create pull/merge request manually in GitHub UI."
}

echo "Select action:"
echo "1) New development"
echo "2) Feature enhancement"
echo "3) Bug fix"
read -r action

read -r -p "Major version: " ver_major
read -r -p "Minor version: " ver_minor
read -r -p "Patch version: " ver_patch

case "$action" in
  1)
    read -r -p "Feature name (feat-...): " feature_name
    run_workflow_new_dev "$feature_name" "$ver_major" "$ver_minor" "$ver_patch"
    ;;
  2)
    read -r -p "Target feature branch: " feature_branch
    run_workflow_feature "$feature_branch" "$ver_major" "$ver_minor" "$ver_patch"
    ;;
  3)
    read -r -p "Bug name (bugfix-...): " bug_name
    run_workflow_bugfix "$bug_name" "$ver_major" "$ver_minor" "$ver_patch"
    ;;
  *)
    echo "Invalid selection"; exit 1;
    ;;
esac
