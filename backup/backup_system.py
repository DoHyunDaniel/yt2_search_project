#!/usr/bin/env python3
"""
YT2 백업 시스템
수원시 행궁동 YouTube 데이터 수집 시스템용 백업 관리
"""

import os
import json
import gzip
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# 환경변수 로딩
try:
    load_dotenv()
except Exception as e:
    print(f"환경변수 로딩 실패 (무시됨): {e}")

class YT2BackupSystem:
    """YT2 백업 시스템 클래스"""
    
    def __init__(self, backup_dir: str = "backups"):
        """
        백업 시스템 초기화
        
        Args:
            backup_dir: 백업 파일 저장 디렉토리
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 데이터베이스 연결 설정
        self.db_config = {
            'host': os.getenv("DB_HOST", "localhost"),
            'port': int(os.getenv("DB_PORT", "5432")),
            'dbname': os.getenv("DB_NAME", "yt2"),
            'user': os.getenv("DB_USER", "app"),
            'password': os.getenv("DB_PASSWORD", "app1234"),
        }
        
        # 백업 메타데이터
        self.metadata = {
            'backup_time': datetime.now().isoformat(),
            'system': 'YT2 - 수원시 행궁동 YouTube 데이터 수집 시스템',
            'database_config': {
                'host': self.db_config['host'],
                'port': self.db_config['port'],
                'dbname': self.db_config['dbname'],
                'user': self.db_config['user']
            }
        }
    
    def get_database_stats(self) -> Dict:
        """데이터베이스 통계 정보 수집"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # 기본 통계
                    cur.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM yt2.channels) as total_channels,
                            (SELECT COUNT(*) FROM yt2.videos) as total_videos,
                            (SELECT COUNT(*) FROM yt2.comments) as total_comments,
                            (SELECT COUNT(*) FROM yt2.embeddings) as total_embeddings,
                            (SELECT COUNT(*) FROM yt2.search_logs) as total_searches
                    """)
                    stats = cur.fetchone()
                    
                    # 최근 데이터 통계
                    cur.execute("""
                        SELECT 
                            COUNT(*) as videos_last_24h,
                            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as videos_last_7d
                        FROM yt2.videos
                    """)
                    recent_stats = cur.fetchone()
                    
                    # 상위 채널 통계
                    cur.execute("""
                        SELECT c.title, COUNT(v.id) as video_count
                        FROM yt2.channels c
                        LEFT JOIN yt2.videos v ON c.id = v.channel_id
                        GROUP BY c.id, c.title
                        ORDER BY video_count DESC
                        LIMIT 10
                    """)
                    top_channels = [{'channel_title': row[0], 'video_count': row[1]} for row in cur.fetchall()]
                    
                    return {
                        'total_channels': stats[0],
                        'total_videos': stats[1],
                        'total_comments': stats[2],
                        'total_embeddings': stats[3],
                        'total_searches': stats[4],
                        'videos_last_24h': recent_stats[0],
                        'videos_last_7d': recent_stats[1],
                        'top_channels': top_channels
                    }
        except Exception as e:
            print(f"데이터베이스 통계 수집 실패: {e}")
            return {}
    
    def backup_schema(self, backup_path: Path) -> None:
        """스키마 백업"""
        schema_file = backup_path / "schema.sql"
        
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # 스키마 정보 수집
                    schema_sql = []
                    schema_sql.append("-- YT2 데이터베이스 스키마 백업")
                    schema_sql.append(f"-- 생성 시간: {datetime.now().isoformat()}")
                    schema_sql.append("")
                    
                    # 테이블 생성 스크립트
                    cur.execute("""
                        SELECT table_name, column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_schema = 'yt2' 
                        ORDER BY table_name, ordinal_position
                    """)
                    
                    tables = {}
                    for row in cur.fetchall():
                        table_name, column_name, data_type, is_nullable, column_default = row
                        if table_name not in tables:
                            tables[table_name] = []
                        tables[table_name].append({
                            'column_name': column_name,
                            'data_type': data_type,
                            'is_nullable': is_nullable,
                            'column_default': column_default
                        })
                    
                    for table_name, columns in tables.items():
                        schema_sql.append(f"-- 테이블: {table_name}")
                        schema_sql.append(f"CREATE TABLE IF NOT EXISTS yt2.{table_name} (")
                        
                        column_definitions = []
                        for col in columns:
                            col_def = f"    {col['column_name']} {col['data_type']}"
                            if col['is_nullable'] == 'NO':
                                col_def += " NOT NULL"
                            if col['column_default']:
                                col_def += f" DEFAULT {col['column_default']}"
                            column_definitions.append(col_def)
                        
                        schema_sql.append(",\n".join(column_definitions))
                        schema_sql.append(");")
                        schema_sql.append("")
                    
                    # 파일 저장
                    with open(schema_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(schema_sql))
                    
                    print(f"스키마 백업 완료: {schema_file}")
                    
        except Exception as e:
            print(f"스키마 백업 실패: {e}")
            raise
    
    def backup_data(self, backup_path: Path) -> None:
        """데이터 백업"""
        data_file = backup_path / "data.sql"
        
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    data_sql = []
                    data_sql.append("-- YT2 데이터베이스 데이터 백업")
                    data_sql.append(f"-- 생성 시간: {datetime.now().isoformat()}")
                    data_sql.append("")
                    
                    # 테이블 순서 (외래키 의존성 고려)
                    table_order = ['channels', 'videos', 'comments', 'embeddings', 'search_logs']
                    
                    for table_name in table_order:
                        data_sql.append(f"-- {table_name} 테이블 데이터")
                        
                        # 테이블 존재 확인
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'yt2' AND table_name = %s
                            )
                        """, (table_name,))
                        
                        if not cur.fetchone()[0]:
                            data_sql.append(f"-- 테이블 {table_name}이 존재하지 않습니다.")
                            data_sql.append("")
                            continue
                        
                        # 데이터 수집
                        cur.execute(f"SELECT * FROM yt2.{table_name} ORDER BY created_at")
                        rows = cur.fetchall()
                        
                        if not rows:
                            data_sql.append(f"-- {table_name} 테이블에 데이터가 없습니다.")
                            data_sql.append("")
                            continue
                        
                        # 컬럼 정보 수집
                        cur.execute("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_schema = 'yt2' AND table_name = %s
                            ORDER BY ordinal_position
                        """, (table_name,))
                        columns = [row[0] for row in cur.fetchall()]
                        
                        # INSERT 문 생성
                        for row in rows:
                            values = []
                            for i, value in enumerate(row):
                                if value is None:
                                    values.append('NULL')
                                elif isinstance(value, str):
                                    escaped_value = value.replace("'", "''")
                                    values.append(f"'{escaped_value}'")
                                elif isinstance(value, (list, dict)):
                                    json_value = json.dumps(value, ensure_ascii=False)
                                    escaped_json = json_value.replace("'", "''")
                                    values.append(f"'{escaped_json}'")
                                elif hasattr(value, 'isoformat'):  # datetime 객체
                                    values.append(f"'{value.isoformat()}'")
                                else:
                                    values.append(str(value))
                            
                            insert_sql = f"INSERT INTO yt2.{table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                            data_sql.append(insert_sql)
                        
                        data_sql.append("")
                    
                    # 파일 저장
                    with open(data_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(data_sql))
                    
                    print(f"데이터 백업 완료: {data_file}")
                    
        except Exception as e:
            print(f"데이터 백업 실패: {e}")
            raise
    
    def create_backup(self, compress: bool = True) -> str:
        """
        전체 백업 생성
        
        Args:
            compress: 압축 여부
            
        Returns:
            백업 폴더 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(exist_ok=True)
        
        print(f"백업 시작: {backup_path}")
        
        try:
            # 1. 데이터베이스 통계 수집
            print("데이터베이스 통계 수집 중...")
            stats = self.get_database_stats()
            self.metadata['database_stats'] = stats
            
            # 2. 스키마 백업
            print("스키마 백업 중...")
            self.backup_schema(backup_path)
            
            # 3. 데이터 백업
            print("데이터 백업 중...")
            self.backup_data(backup_path)
            
            # 4. 메타데이터 저장
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            # 5. 압축 (선택사항)
            if compress:
                print("백업 압축 중...")
                self._compress_backup(backup_path)
            
            print(f"백업 완료: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"백업 실패: {e}")
            # 실패한 백업 폴더 삭제
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def _compress_backup(self, backup_path: Path) -> None:
        """백업 압축"""
        tar_file = backup_path.parent / f"{backup_path.name}.tar.gz"
        
        with tarfile.open(tar_file, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        # 원본 폴더 삭제
        shutil.rmtree(backup_path)
        print(f"압축 완료: {tar_file}")
    
    def list_backups(self) -> List[Dict]:
        """백업 목록 조회"""
        backups = []
        
        for item in self.backup_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backups.append({
                            'path': str(item),
                            'timestamp': metadata.get('backup_time'),
                            'stats': metadata.get('database_stats', {})
                        })
                    except Exception as e:
                        print(f"메타데이터 읽기 실패 {item}: {e}")
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30) -> None:
        """오래된 백업 정리"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        removed_count = 0
        
        for item in self.backup_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        backup_time = datetime.fromisoformat(metadata.get('backup_time', ''))
                        if backup_time < cutoff_date:
                            shutil.rmtree(item)
                            removed_count += 1
                            print(f"오래된 백업 삭제: {item}")
                    except Exception as e:
                        print(f"백업 정리 실패 {item}: {e}")
        
        print(f"백업 정리 완료: {removed_count}개 삭제")

if __name__ == "__main__":
    # 백업 시스템 테스트
    backup_system = YT2BackupSystem()
    
    print("=== YT2 백업 시스템 테스트 ===")
    
    # 백업 생성
    backup_path = backup_system.create_backup(compress=True)
    print(f"백업 생성 완료: {backup_path}")
    
    # 백업 목록 조회
    backups = backup_system.list_backups()
    print(f"사용 가능한 백업: {len(backups)}개")
    
    for backup in backups[:5]:  # 최근 5개만 표시
        print(f"- {backup['timestamp']}: {backup['path']}")
