# 📈 주식 종목 분석 AI 에이전트 (오케스트레이션 구조)

증권사 리서치센터를 모사한 멀티 에이전트. **오케스트레이터 1개**가 **5개 전문 애널리스트**를
병렬로 호출하고 결과를 통합해 종합 투자의견과 추천픽을 산출합니다.

## 구조

```
          ┌─────────────────────────────┐
          │   stock-analyst (오케스트레이터)  │   ← 사용자 진입점 (PROACTIVELY)
          │   결과 통합 → 종합의견 → 추천픽    │
          └──────────────┬──────────────┘
        병렬 위임 (Agent tool / 중첩 서브에이전트)
   ┌──────────┬──────────┼──────────┬──────────┐
   ▼          ▼          ▼          ▼          ▼
기업개요     재무분석     산업분석    모멘텀     리스크
company-   financial- industry-  momentum-  risk-
overview-  analyst    analyst    analyst    analyst
analyst
```

## 분석 프레임워크 (리포트 순서 고정)

1. 기업개요 → 2. 재무분석 → 3. 산업분석 → 4. 모멘텀 분석 → 5. 리스크 요인 → 6. 종합 의견
→ **추천픽 & 근거** → **함께 고려할 리스크**

## 사용 방법

세션에서 종목을 언급하면 `stock-analyst`가 자동(PROACTIVELY) 위임됩니다. 명시 호출도 가능합니다:

```
삼성전자 분석해줘
> use the stock-analyst subagent to analyze 005930
```

## 설계 노트 (Anthropic 공식 가이드 준수)

- 파일 위치: `.claude/agents/*.md`, 필수 frontmatter는 `name`, `description`.
- `description`에 **PROACTIVELY use** 키워드를 넣어 자동 위임을 유도.
- 시스템 프롬프트 본문은 **HTML(XML 태그) 형식**(`<role>`, `<task>`, `<output_format>` 등).
- 오케스트레이션: `stock-analyst`의 `tools`에 `Agent(...)`를 부여해 5개 전문가 **중첩 호출**.
  서브에이전트끼리 직접 통신하지 않으며 오케스트레이터가 취합을 담당.
- 파일을 직접 수정한 경우 세션을 재시작해야 로딩됩니다(`/agents`로는 즉시 반영).

> ⚠️ 본 에이전트의 산출물은 정보 제공 목적의 참고 자료이며 투자 권유가 아닙니다.
