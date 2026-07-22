# merge_files.py

여러 개의 CSV/Excel 파일을 파일마다 다른 키 컬럼 기준으로 순차적으로 머징하는 스크립트입니다. VLOOKUP을 여러 번 건 것과 같은 효과를 냅니다.

## 요구 사항

```bash
pip install pandas openpyxl
```

## 사용법

### 1. 헤더 확인

```bash
python merge_files.py inspect file1.xlsx file2.xlsx file3.xlsx
```

각 파일(엑셀은 시트별)의 컬럼명이 출력됩니다. 이 결과를 보고 어떤 컬럼을 키로 쓸지 정합니다.

### 2. config.json 작성

`config_example.json` 참고:

```json
{
  "join_type": "left",
  "files": [
    {
      "path": "file1.xlsx",
      "key": "고객ID",
      "columns": ["고객ID", "이름", "가입일"]
    },
    {
      "path": "file2.xlsx",
      "key": "고객번호",
      "columns": ["고객번호", "매출액", "최근구매일"]
    }
  ]
}
```

- `path`: 파일 경로 (CSV/XLSX 모두 지원)
- `key`: 이 파일에서 매칭 기준이 되는 컬럼명 (파일마다 이름이 달라도 됨)
- `columns`: 최종 결과에 남길 컬럼 (생략 시 전체 컬럼 포함)
- `sheet`: 엑셀 파일에서 특정 시트를 지정하고 싶을 때 (생략 시 첫 시트)
- `join_type`: 매칭 안 된 행을 어떻게 처리할지
  - `inner` (완전일치 병합): 키가 안 맞는 행은 결과에서 제외
  - `left` (기준 병합, 기본값): 첫 파일 행은 모두 유지, 안 맞는 값만 빈 칸 — VLOOKUP과 동일
  - `outer` (전체 병합): 양쪽 다 유지, 안 맞는 값은 빈 칸
- `match_mode`: 키 값을 어떻게 비교할지. 현재는 `"exact"`(완전일치, 공백 제거 후 문자열 비교)만 지원. 부분일치("서울시" vs "서울" 같은 경우)는 매칭되지 않음.
- `files` 배열에 파일을 계속 추가하면 3개 이상도 순차적으로 머징됩니다.

### 3. 머징 실행

```bash
python merge_files.py merge --config config.json --output result.xlsx
```

`result.xlsx`(또는 `.csv`)로 저장됩니다.

## 특징

- 파일 개수 제한 없이 순차적으로 왼쪽부터 겹쳐서 머징
- 키 값 앞뒤 공백 자동 제거 (매칭 실패 방지)
- 매칭되지 않는 값은 빈 값으로 처리 (VLOOKUP의 `#N/A`와 동일한 상황)
- CSV/Excel 혼합 사용 가능
