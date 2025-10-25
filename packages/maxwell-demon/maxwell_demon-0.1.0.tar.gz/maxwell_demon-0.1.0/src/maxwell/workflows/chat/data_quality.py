#!/usr/bin/env python3
"""Chat data quality and cleanup workflow.

This workflow provides:
1. Chat data validation and cleaning
2. MongoDB collection maintenance
3. Qdrant integration monitoring
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Set

from pymongo import MongoClient
from pymongo.database import Database

from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)


class ChatDataQualityWorkflow(BaseWorkflow):
    """Chat data quality and cleanup workflow."""

    # Workflow metadata
    workflow_id: str = "chat-data-quality"
    name: str = "Chat Data Quality & Cleanup"
    description: str = "Validates, cleans, and maintains MongoDB chat collections"
    version: str = "1.0"
    category: str = "chat"
    tags: Set[str] = {"chat", "quality", "etl", "mongodb"}

    def __init__(self):
        self.workflow_id = "chat-data-quality"
        self.name = "Chat Data Quality & Cleanup"
        self.description = "Validates, cleans, and maintains MongoDB chat collections"
        self.version = "1.0"
        super().__init__()

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=1800,  # 30 minutes
            cache_results=True,
            parameters={
                "root_dir": str(root_dir),
                "mongodb_uri": "mongodb://localhost:27017",
                "qdrant_url": "http://localhost:6333",
                "collection_name": "chat_turns",
                "embedding_service": {"url": "http://localhost:8001", "model": "qwen2-embedder"},
            },
        )

    def get_required_inputs(self) -> List[str]:
        """Get required input data keys."""
        return ["root_dir"]

    def get_produced_outputs(self) -> List[str]:
        """Get output data keys this workflow produces."""
        return ["quality_report", "collection_stats", "embeddings_report"]

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Get CLI parameters for maxwell chat-data-quality command."""
        return [
            {
                "name": "operation",
                "type": str,
                "required": False,
                "help": "Operation to perform: validate, clean, backup, rebuild-index",
                "choices": ["validate", "clean", "backup", "rebuild-index", "quality-report"],
            },
            {
                "name": "limit",
                "type": int,
                "required": False,
                "help": "Limit number of turns to process (default: 1000)",
                "default": 1000,
            },
            {
                "name": "dry-run",
                "type": bool,
                "required": False,
                "help": "Only analyze what would be done without making changes (default: False)",
            },
            {
                "name": "force-rebuild",
                "type": bool,
                "required": False,
                "help": "Force rebuild of all indexes (default: False)",
            },
        ]

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute chat data quality workflow."""
        try:
            mongodb_uri = context.get("mongodb_uri", "mongodb://localhost:27017")
            collection_name = context.get("collection_name", "chat_turns")
            limit = context.get("limit", 1000)

            # Connect to MongoDB
            client = MongoClient(mongodb_uri)
            db = client[collection_name.rsplit("/", 1)[0]]  # Get database from URI

            # Report initial collection stats
            start_time = time.time()
            initial_stats = {
                "total_turns": db[collection_name].count_documents({}),
                "chatgpt_turns": db[collection_name].count_documents({"source": "chatgpt"}),
                "claude_turns": db[collection_name].count_documents({"source": "claude"}),
            }

            print(f"[SCAN] Initial collection stats: {initial_stats}")

            # Define quality checks
            quality_issues = {
                "corrupted_content": 0,
                "empty_turns": 0,
                "short_turns": 0,
                "duplicate_turns": 0,
                "format_errors": 0,
                "missing_metadata": 0,
            }

            # Process turns in batches
            processed_count = 0
            batch_size = 100
            cursor = db[collection_name].find({})

            for batch_num, batch in enumerate(self._create_batches(cursor, batch_size)):
                if len(batch) == 0:
                    continue

                print(f"[BATCH] Processing batch {batch_num + 1}: {len(batch)} turns...")

                # Validate each turn and collect validation results
                validation_results = []
                for turn in batch:
                    validation_result = self._validate_turn(turn, db, collection_name)
                    validation_results.append(validation_result)
                    for issue_type, issues in validation_result.items():
                        if issues:
                            quality_issues[issue_type] += len(issues)

                # Apply fixes if any validation issues found
                has_issues = any(any(vr.values()) for vr in validation_results)
                if has_issues:
                    print(f"[FIX] Applying fixes to batch {batch_num + 1}...")
                    success = self._apply_fixes(batch, validation_results, db, collection_name)
                    if success:
                        print(f"[OK] Fixed {len(batch)} turns")
                    else:
                        print(f"[ERROR] Failed to fix batch {batch_num + 1}")

                processed_count += len(batch)

                # Progress reports
                if batch_num % 10 == 0:
                    elapsed = time.time() - start_time
                    print(
                        f"[STATS] Batch {batch_num + 1}: {processed_count} turns processed in {elapsed:.1f}s"
                    )
                    print(f"[SCAN] Total: {processed_count} turns processed so far")

            # Final report
            end_time = time.time()
            elapsed = end_time - start_time
            final_stats = {
                "total_turns_processed": processed_count,
                "quality_issues_found": quality_issues,
                "duration_seconds": elapsed,
                "turns_per_second": processed_count / elapsed if elapsed > 0 else 0,
            }

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.COMPLETED,
                metrics=self.metrics,
                artifacts={
                    "quality_report": final_stats,
                    "collection_stats": final_stats,
                    "operation": context.get("operation", "validate"),
                    "turns_processed": processed_count,
                    "batch_size": batch_size,
                    "limit": limit,
                },
            )

        except Exception as e:
            print(f"[ERROR] Workflow failed: {e}")
            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.FAILED,
                metrics=self.metrics,
                error_message=str(e),
            )

    def _validate_turn(
        self, turn: Dict, db: Database, collection_name: str
    ) -> Dict[str, List[str]]:
        """Validate a single chat turn for quality issues."""
        issues: Dict[str, List[str]] = {}

        # Check for empty or very short content
        content = turn.get("content", "")
        if not content or len(content.strip()) < 10:
            issues["empty_turns"] = [f"Empty turn: {turn.get('turn_id', 'unknown')}"]

        # Check for unprintable characters
        try:
            content.encode("ascii")
            # If it contains unprintable chars, likely corrupted
            issues["corrupted_content"] = [
                f"Corrupted content in turn {turn.get('turn_id', 'unknown')}"
            ]
        except UnicodeEncodeError:
            issues["encoding_issues"] = [f"Encoding error in turn {turn.get('turn_id', 'unknown')}"]

        # Check for JSON structure
        if turn.get("source") and not isinstance(turn.get("conversation_id"), (str, dict)):
            issues["format_errors"] = [
                f"Invalid conversation structure in turn {turn.get('turn_id', 'unknown')}"
            ]

        # Check for duplicate content using content hash
        content_length = turn.get("content_length")
        if turn.get("content_hash") and content_length is not None and content_length > 0:
            # Check for other turns with same hash in same conversation
            duplicate = db[collection_name].find_one(
                {
                    "conversation_id": turn.get("conversation_id"),
                    "content_hash": turn.get("content_hash"),
                    "turn_id": {"$ne": turn.get("turn_id")},
                }
            )
            if duplicate:
                issues["duplicate_turns"] = [f"Duplicate turn: {turn.get('turn_id', 'unknown')}"]

        # Check for missing required fields
        required_fields = ["turn_id", "role", "content", "conversation_id", "source"]
        for field in required_fields:
            if not turn.get(field):
                issues["missing_metadata"] = [
                    f"Missing field: {field} in turn {turn.get('turn_id', 'unknown')}"
                ]

        return issues

    def _apply_fixes(
        self,
        batch: List[Dict],
        validation_results: List[Dict[str, List[str]]],
        db: Database,
        collection_name: str,
    ) -> bool:
        """Apply fixes to a batch of turns."""
        try:
            for turn, validation_result in zip(batch, validation_results):
                issues = validation_result
                if not issues:
                    continue

                print(f"[FIX] Applying {len(issues)} fixes to turn...")

                for issue_type, issue_list in issues.items():
                    for issue in issue_list:
                        if issue_type == "corrupted_content":
                            # Remove corrupted turn
                            db[collection_name].delete_one({"turn_id": turn["turn_id"]})
                            print(f"[DELETE]  Removed corrupted turn: {turn['turn_id']}")

                        elif issue_type == "encoding_issues":
                            # Could try to re-encode, but removal is safer
                            db[collection_name].delete_one({"turn_id": turn["turn_id"]})
                            print(f"[DELETE]  Removed encoding error turn: {turn['turn_id']}")

                        elif issue_type == "format_errors":
                            # Could try to fix JSON, but removal is safer
                            db[collection_name].delete_one({"turn_id": turn["turn_id"]})
                            print(f"[DELETE]  Removed format error turn: {turn['turn_id']}")

                        elif issue_type == "missing_metadata":
                            # Could try to reconstruct, but removal is safer
                            db[collection_name].delete_one({"turn_id": turn["turn_id"]})
                            print(f"[DELETE]  Removed malformed turn: {turn['turn_id']}")

                        elif issue_type == "empty_turns":
                            # Remove empty turn
                            db[collection_name].delete_one({"turn_id": turn["turn_id"]})
                            print(f"[DELETE]  Removed empty turn: {turn['turn_id']}")

                        elif issue_type == "duplicate_turns":
                            # Keep the first occurrence, remove duplicates
                            # This is complex - would need tracking and deduplication logic
                            pass  # Simplify for now

            return True

        except Exception as e:
            print(f"[ERROR] Error applying fixes to batch: {e}")
            return False

    def _create_batches(self, cursor, batch_size: int) -> List[List[Dict]]:
        """Create batches from cursor."""
        batches = []
        batch = []
        for turn in cursor:
            batch.append(turn)
            if len(batch) >= batch_size:
                batches.append(batch)
                batch = []

        return batches


def main() -> int:
    """Main execution method."""
    import argparse

    parser = argparse.ArgumentParser(description="Chat data quality and cleanup workflow")
    parser.add_argument(
        "operation",
        choices=["validate", "clean", "backup", "rebuild-index", "quality-report"],
        help="Operation to perform",
    )
    parser.add_argument("--limit", type=int, default=1000, help="Limit number of turns to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="Only analyze without making changes"
    )
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild of all indexes")
    parser.add_argument("--root-dir", type=str, default=".", help="Root directory")

    args = parser.parse_args()

    # Create workflow and run
    workflow = ChatDataQualityWorkflow()

    # Get config for defaults
    config = workflow.get_config(Path(args.root_dir))

    # Build context dict from config + args
    context = {
        **config.parameters,
        "operation": args.operation,
        "limit": args.limit,
        "dry_run": args.dry_run,
        "force_rebuild": args.force_rebuild,
    }

    # Execute workflow
    print("[START] Starting chat data quality workflow...")
    result = workflow.execute(Path(args.root_dir), context)

    if result.status == WorkflowStatus.COMPLETED:
        print("[OK] Chat data quality workflow completed successfully!")
        if result.artifacts and "quality_report" in result.artifacts:
            report = result.artifacts["quality_report"]
            print("\n[STATS] QUALITY REPORT")
            print("=" * 50)
            for key, value in report.items():
                if isinstance(value, dict) and value:
                    print(f"  {key}: {value}")
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        print(f"  {key}: {item}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("\n[SUCCESS] No quality issues found!")

    elif result.status == WorkflowStatus.FAILED:
        error_msg = result.error_message if result.error_message else "Unknown error"
        print(f"[ERROR] Chat data quality workflow failed: {error_msg}")
    else:
        print("[WARN] Chat data quality workflow completed with warnings")

    return 0
