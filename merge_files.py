import argparse
import json
import os
import sys

import pandas as pd


def read_table(path, sheet_name=None):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path, dtype=str)
    if ext in (".xlsx", ".xlsm", ".xls"):
        if sheet_name:
            return pd.read_excel(path, sheet_name=sheet_name, dtype=str)
        return pd.read_excel(path, dtype=str)
    raise ValueError(f"지원하지 않는 파일 형식입니다: {path}")


def inspect(paths):
    for path in paths:
        print(f"\n=== {path} ===")
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path, dtype=str, nrows=0)
            print("컬럼:", list(df.columns))
            continue

        xls = pd.ExcelFile(path)
        for sheet in xls.sheet_names:
            df = xls.parse(sheet, dtype=str, nrows=0)
            print(f"[시트: {sheet}] 컬럼:", list(df.columns))


def strip_key(series):
    return series.astype(str).str.strip()


def merge(config_path, output_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    join_type = config.get("join_type", "left")
    files = config.get("files", [])
    if len(files) < 2:
        raise ValueError("files 항목에는 최소 2개의 파일 정보가 필요합니다.")

    pandas_how = {"left": "left", "outer": "outer", "inner": "inner"}.get(join_type)
    if pandas_how is None:
        raise ValueError(f"알 수 없는 join_type입니다: {join_type}")

    # 매칭 방식은 항상 "완전일치"입니다 (공백 제거 후 문자열이 완전히 같아야 매칭).
    # 부분일치/대소문자 무시 등은 지원하지 않습니다.
    match_mode = config.get("match_mode", "exact")
    if match_mode != "exact":
        raise ValueError(f"현재는 match_mode='exact'만 지원합니다: {match_mode}")

    result = None
    for i, file_cfg in enumerate(files):
        path = file_cfg["path"]
        key = file_cfg["key"]
        columns = file_cfg.get("columns")
        sheet_name = file_cfg.get("sheet")

        df = read_table(path, sheet_name=sheet_name)

        if columns:
            missing = [c for c in columns if c not in df.columns]
            if missing:
                raise ValueError(f"{path}에 없는 컬럼입니다: {missing}")
            df = df[columns]

        if key not in df.columns:
            raise ValueError(f"{path}에 key 컬럼 '{key}'가 없습니다.")

        df[key] = strip_key(df[key])

        if result is None:
            result = df
            merge_key = key
        else:
            result = result.merge(
                df, left_on=merge_key, right_on=key, how=pandas_how,
                suffixes=("", f"_{i}"),
            )
            if key != merge_key and key in result.columns:
                result = result.drop(columns=[key])

    result = result.fillna("")

    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".csv":
        result.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        result.to_excel(output_path, index=False)

    print(f"완료: {output_path} ({len(result)}행, {len(result.columns)}열)")


def main():
    parser = argparse.ArgumentParser(description="여러 CSV/Excel 파일을 지정한 키로 머징합니다.")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser("inspect", help="파일들의 헤더(컬럼명)를 확인합니다.")
    inspect_parser.add_argument("paths", nargs="+", help="확인할 파일 경로들")

    merge_parser = sub.add_parser("merge", help="config.json에 따라 파일들을 머징합니다.")
    merge_parser.add_argument("--config", required=True, help="config.json 경로")
    merge_parser.add_argument("--output", required=True, help="결과 저장 경로 (xlsx 또는 csv)")

    args = parser.parse_args()

    if args.command == "inspect":
        inspect(args.paths)
    elif args.command == "merge":
        merge(args.config, args.output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
