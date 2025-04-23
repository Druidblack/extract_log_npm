#!/usr/bin/env python3
# -*- coding: cp1251 -*-

import re
import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def extract_client_ips(log_path: Path) -> set:
    ip_pattern = re.compile(r'405\s*-\s*POST.*\[Client\s+(\d+\.\d+\.\d+\.\d+)\]')
    ips = set()
    with log_path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            match = ip_pattern.search(line)
            if match:
                ips.add(match.group(1))
    return ips

def load_existing_ips(file_path: Path) -> set:
    if not file_path.exists():
        return set()
    with file_path.open('r', encoding='utf-8', errors='ignore') as f:
        return { line.strip() for line in f if line.strip() }

def save_ips(file_path: Path, ips: set):
    with file_path.open('w', encoding='utf-8') as out_f:
        for ip in sorted(ips, key=lambda s: tuple(int(p) for p in s.split('.'))):
            out_f.write(ip + '\n')

def push_to_github(repo_path: Path, file_path: Path, message: str):
    try:
        subprocess.run(['git', 'add', str(file_path)], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', message], cwd=repo_path, check=True)
        subprocess.run(['git', 'push'], cwd=repo_path, check=True)
        print("? ���� ������� ���������� � ��������� �� GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"������ ��� �������� � GitHub: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="�������� IP � 405-POST �� ����, ��������� ���� � (���� ���� ���������) ����� �� GitHub"
    )
    parser.add_argument('logfile', type=Path,
                        help="���� �� ����� ���� nginx proxy manager")
    parser.add_argument('-o', '--output', type=Path, default=Path('clients_405_post.txt'),
                        help="���� ��� ���������� IP (�� ���������: clients_405_post.txt)")
    parser.add_argument('--repo', type=Path, default=Path('.'),
                        help="���� � ���������� git-����������� (�� ���������: ������� ����������)")
    args = parser.parse_args()

    if not args.logfile.exists():
        print(f"������: ���� {args.logfile} �� ������.", file=sys.stderr)
        sys.exit(1)

    existing_ips = load_existing_ips(args.output)
    new_ips = extract_client_ips(args.logfile)

    if not new_ips:
        print("� ���� �� ������� ������ � '405 - POST'. ������ ���������.")
        sys.exit(0)

    all_ips = existing_ips.union(new_ips)
    added_count = len(all_ips) - len(existing_ips)

    # ���� ����� IP ��� � �����
    if added_count == 0:
        print("����� IP �� ������ �� ����������. ���� � ����������� �� ����������.")
        sys.exit(0)

    # ��������� ���������� ������
    save_ips(args.output, all_ips)
    print(f"������� {len(new_ips)} IP � ����, �� ��� �����: {added_count}. ����� � �����: {len(all_ips)}.")

    # ������ ������ � ���
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    commit_msg = f"Update IP list: +{added_count} @ {timestamp}"
    push_to_github(args.repo, args.output, commit_msg)

if __name__ == '__main__':
    main()
