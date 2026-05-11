# Import GitHub Skills

GitHub 레포지토리에서 Claude Code 스킬을 가져와 설치합니다.

## 사용법

사용자가 GitHub에서 스킬을 가져오고 싶다고 하면:

1. `scripts/import-github-skills.sh` 스크립트를 실행합니다.
2. 설치 결과를 확인합니다.
3. 설치된 스킬 목록을 안내합니다.

## 실행 방법

```bash
# 프로젝트 스킬로 설치 (현재 프로젝트의 .claude/skills/)
bash scripts/import-github-skills.sh <GitHub-repo-URL>

# 특정 서브디렉토리에서 스킬 가져오기
bash scripts/import-github-skills.sh <GitHub-repo-URL> skills/

# 글로벌 스킬로 설치 (~/.claude/skills/)
bash scripts/import-github-skills.sh <GitHub-repo-URL> .claude/skills --global
```

## GitHub 레포 구조 요구사항

가져올 레포는 아래 구조를 가져야 합니다:

```
my-skills-repo/
└── .claude/
    └── skills/
        ├── my-skill-1/
        │   └── SKILL.md
        └── my-skill-2/
            └── SKILL.md
```

## 주의사항

- 같은 이름의 스킬이 있으면 덮어씁니다.
- `SKILL.md`가 없는 디렉토리는 스킬로 인식하지 않습니다.
- 설치 후 Claude Code를 재시작해야 새 스킬이 인식됩니다.
