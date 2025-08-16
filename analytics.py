"""
Analytics and monitoring for search quality and usage patterns.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import pandas as pd
from collections import Counter, defaultdict
import statistics
import time

@dataclass
class QueryLog:
    """Structure for query logging."""
    timestamp: datetime
    query: str
    recall_success: bool
    latency_ms: float
    results_count: int
    source: str  # "context", "llm_knowledge", or "hybrid"
    user_feedback: Optional[str] = None
    error: Optional[str] = None
    user_id: Optional[str] = None

class AnalyticsDashboard:
    """Analytics for search quality and usage patterns."""
    
    def __init__(self, log_file: str = "data/analytics.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        self.logs: List[QueryLog] = []
        self._load_logs()
        
        # Real-time metrics
        self.current_session = {
            "start_time": datetime.now(),
            "queries": 0,
            "total_latency": 0,
            "errors": 0,
            "success_count": 0
        }
    
    def _load_logs(self):
        """Load existing logs from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            self.logs.append(QueryLog(
                                timestamp=datetime.fromisoformat(data['timestamp']),
                                query=data['query'],
                                recall_success=data['recall_success'],
                                latency_ms=data['latency_ms'],
                                results_count=data['results_count'],
                                source=data['source'],
                                user_feedback=data.get('user_feedback'),
                                error=data.get('error'),
                                user_id=data.get('user_id')
                            ))
                        except Exception as e:
                            print(f"Failed to parse log line: {e}")
                            continue
            except Exception as e:
                print(f"Failed to load analytics logs: {e}")
    
    def log_query(
        self, 
        query: str,
        recall_success: bool,
        latency_ms: float,
        results_count: int,
        source: str,
        error: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log a query execution."""
        log_entry = QueryLog(
            timestamp=datetime.now(),
            query=query,
            recall_success=recall_success,
            latency_ms=latency_ms,
            results_count=results_count,
            source=source,
            error=error,
            user_id=user_id
        )
        
        self.logs.append(log_entry)
        
        # Update session metrics
        self.current_session["queries"] += 1
        self.current_session["total_latency"] += latency_ms
        if error:
            self.current_session["errors"] += 1
        if recall_success:
            self.current_session["success_count"] += 1
        
        # Append to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_dict = asdict(log_entry)
                log_dict['timestamp'] = log_entry.timestamp.isoformat()
                f.write(json.dumps(log_dict) + '\n')
        except Exception as e:
            print(f"Failed to write analytics log: {e}")
    
    def add_feedback(self, query: str, feedback: str, user_id: Optional[str] = None):
        """Add user feedback for a query."""
        # Find the most recent matching query
        for log in reversed(self.logs):
            if log.query == query and (not user_id or log.user_id == user_id):
                log.user_feedback = feedback
                # Update in file (would need to rewrite file for persistence)
                break
    
    def get_metrics(
        self, 
        days: int = 7,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate analytics metrics."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter logs
        filtered_logs = [
            l for l in self.logs 
            if l.timestamp > cutoff and (not user_id or l.user_id == user_id)
        ]
        
        if not filtered_logs:
            return self._empty_metrics()
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([asdict(l) for l in filtered_logs])
        
        # Calculate metrics
        metrics = {
            "total_queries": len(df),
            "unique_queries": df['query'].nunique(),
            "recall_rate": (df['recall_success'].mean() * 100) if not df.empty else 0,
            "avg_latency": df['latency_ms'].mean() if not df.empty else 0,
            "median_latency": df['latency_ms'].median() if not df.empty else 0,
            "p95_latency": df['latency_ms'].quantile(0.95) if not df.empty else 0,
            "p99_latency": df['latency_ms'].quantile(0.99) if not df.empty else 0,
            "avg_results": df['results_count'].mean() if not df.empty else 0,
            "error_rate": ((df['error'].notna().sum() / len(df)) * 100) if not df.empty else 0,
            "source_distribution": df['source'].value_counts().to_dict() if not df.empty else {}
        }
        
        # Top queries
        query_counts = Counter(df['query'].str.lower())
        metrics['top_queries'] = query_counts.most_common(10)
        
        # Failure patterns
        failures = df[~df['recall_success']]
        if not failures.empty:
            failure_queries = Counter(failures['query'].str.lower())
            metrics['failure_patterns'] = failure_queries.most_common(5)
        else:
            metrics['failure_patterns'] = []
        
        # Error patterns
        errors = df[df['error'].notna()]
        if not errors.empty:
            error_types = Counter(errors['error'])
            metrics['error_types'] = error_types.most_common(5)
        else:
            metrics['error_types'] = []
        
        # Time-based patterns
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        
        metrics['queries_by_hour'] = df.groupby('hour').size().to_dict()
        metrics['queries_by_day'] = df.groupby('day_of_week').size().to_dict()
        
        # Performance trends
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_stats = df.groupby('date').agg({
            'recall_success': 'mean',
            'latency_ms': 'mean',
            'query': 'count'
        }).rename(columns={'query': 'count'})
        
        metrics['daily_trends'] = {
            str(date): {
                'recall_rate': float(row['recall_success'] * 100),
                'avg_latency': float(row['latency_ms']),
                'query_count': int(row['count'])
            }
            for date, row in daily_stats.iterrows()
        }
        
        # User satisfaction (if feedback available)
        feedback_logs = [l for l in filtered_logs if l.user_feedback]
        if feedback_logs:
            positive_feedback = sum(1 for l in feedback_logs if 'good' in l.user_feedback.lower() or 'helpful' in l.user_feedback.lower())
            metrics['satisfaction_rate'] = (positive_feedback / len(feedback_logs)) * 100
        else:
            metrics['satisfaction_rate'] = None
        
        return metrics
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "total_queries": 0,
            "unique_queries": 0,
            "recall_rate": 0,
            "avg_latency": 0,
            "median_latency": 0,
            "p95_latency": 0,
            "p99_latency": 0,
            "avg_results": 0,
            "error_rate": 0,
            "source_distribution": {},
            "top_queries": [],
            "failure_patterns": [],
            "error_types": [],
            "queries_by_hour": {},
            "queries_by_day": {},
            "daily_trends": {},
            "satisfaction_rate": None
        }
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get metrics for current session."""
        session_duration = (datetime.now() - self.current_session["start_time"]).total_seconds()
        
        return {
            "session_duration_minutes": session_duration / 60,
            "total_queries": self.current_session["queries"],
            "avg_latency": (
                self.current_session["total_latency"] / self.current_session["queries"]
                if self.current_session["queries"] > 0 else 0
            ),
            "error_rate": (
                (self.current_session["errors"] / self.current_session["queries"]) * 100
                if self.current_session["queries"] > 0 else 0
            ),
            "success_rate": (
                (self.current_session["success_count"] / self.current_session["queries"]) * 100
                if self.current_session["queries"] > 0 else 0
            ),
            "queries_per_minute": (
                self.current_session["queries"] / (session_duration / 60)
                if session_duration > 0 else 0
            )
        }
    
    def generate_report(self, days: int = 7) -> str:
        """Generate analytics report."""
        metrics = self.get_metrics(days)
        session_metrics = self.get_session_metrics()
        
        report = []
        report.append("=" * 60)
        report.append("COGNITIVE COMPANION ANALYTICS REPORT")
        report.append("=" * 60)
        report.append(f"\nPeriod: Last {days} days")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Performance Metrics
        report.append("\n## Performance Metrics")
        report.append(f"- Total Queries: {metrics['total_queries']:,}")
        report.append(f"- Unique Queries: {metrics['unique_queries']:,}")
        report.append(f"- Recall Rate: {metrics['recall_rate']:.1f}%")
        report.append(f"- Error Rate: {metrics['error_rate']:.1f}%")
        report.append(f"- Avg Latency: {metrics['avg_latency']:.1f}ms")
        report.append(f"- Median Latency: {metrics['median_latency']:.1f}ms")
        report.append(f"- P95 Latency: {metrics['p95_latency']:.1f}ms")
        report.append(f"- P99 Latency: {metrics['p99_latency']:.1f}ms")
        report.append(f"- Avg Results: {metrics['avg_results']:.1f}")
        
        if metrics['satisfaction_rate'] is not None:
            report.append(f"- User Satisfaction: {metrics['satisfaction_rate']:.1f}%")
        
        # Source Distribution
        report.append("\n## Source Distribution")
        total = sum(metrics['source_distribution'].values())
        for source, count in metrics['source_distribution'].items():
            pct = (count / total) * 100 if total > 0 else 0
            report.append(f"- {source}: {count:,} ({pct:.1f}%)")
        
        # Top Queries
        if metrics['top_queries']:
            report.append("\n## Top Queries")
            for i, (query, count) in enumerate(metrics['top_queries'][:10], 1):
                report.append(f"{i:2}. '{query[:50]}...': {count} times")
        
        # Common Failures
        if metrics['failure_patterns']:
            report.append("\n## Common Failures")
            for query, count in metrics['failure_patterns']:
                report.append(f"- '{query[:50]}...': {count} failures")
        
        # Error Types
        if metrics['error_types']:
            report.append("\n## Error Types")
            for error, count in metrics['error_types']:
                report.append(f"- {error[:50]}: {count} occurrences")
        
        # Current Session
        report.append("\n## Current Session")
        report.append(f"- Duration: {session_metrics['session_duration_minutes']:.1f} minutes")
        report.append(f"- Queries: {session_metrics['total_queries']}")
        report.append(f"- Avg Latency: {session_metrics['avg_latency']:.1f}ms")
        report.append(f"- Success Rate: {session_metrics['success_rate']:.1f}%")
        report.append(f"- QPM: {session_metrics['queries_per_minute']:.2f}")
        
        # Usage Patterns
        report.append("\n## Usage Patterns")
        
        # Busiest hours
        if metrics['queries_by_hour']:
            busiest_hours = sorted(
                metrics['queries_by_hour'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            report.append("Busiest Hours:")
            for hour, count in busiest_hours:
                report.append(f"  - {hour:02d}:00: {count} queries")
        
        # Busiest days
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if metrics['queries_by_day']:
            busiest_days = sorted(
                metrics['queries_by_day'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            report.append("Activity by Day:")
            for day, count in busiest_days:
                report.append(f"  - {day_names[day]}: {count} queries")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def export_to_csv(self, output_file: str = "analytics_export.csv"):
        """Export analytics data to CSV."""
        if not self.logs:
            print("No data to export")
            return
        
        df = pd.DataFrame([asdict(l) for l in self.logs])
        df.to_csv(output_file, index=False)
        print(f"Exported {len(df)} records to {output_file}")

# Global analytics instance
analytics = AnalyticsDashboard()

# Decorator for automatic query logging
def track_query(source: str = "unknown"):
    """Decorator to automatically track query performance."""
    def decorator(func):
        def wrapper(query: str, *args, **kwargs):
            start_time = time.time()
            error = None
            results = []
            
            try:
                results = func(query, *args, **kwargs)
                recall_success = len(results) > 0 if isinstance(results, list) else True
                return results
                
            except Exception as e:
                error = str(e)
                recall_success = False
                raise
                
            finally:
                latency_ms = (time.time() - start_time) * 1000
                results_count = len(results) if isinstance(results, list) else 0
                
                analytics.log_query(
                    query=query,
                    recall_success=recall_success,
                    latency_ms=latency_ms,
                    results_count=results_count,
                    source=source,
                    error=error,
                    user_id=kwargs.get('user_id')
                )
        
        return wrapper
    return decorator
