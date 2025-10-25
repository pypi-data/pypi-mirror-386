"""Deep research workflow - comprehensive search across multiple data sources.

Simple implementation that uses existing Maxwell workflows via MCP interface.
"""

__all__ = ["DeepResearchWorkflow"]

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from maxwell.api import execute_workflow
from maxwell.lm_pool import get_lm
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


# Workflow-specific schemas (defined in same file as workflow)
# -------------------------------------------------------------


@dataclass(frozen=True)
class DeepResearchInputs(WorkflowInputs):
    """Input schema for deep research workflow."""

    research_question: str
    data_sources: str = "chat,filesystem"
    max_iterations: int = 3
    queries_per_iteration: int = 5


@dataclass(frozen=True)
class DeepResearchOutputs(WorkflowOutputs):
    """Output schema for deep research workflow."""

    report: str
    findings_summary: str
    findings: List[Dict[str, str]]
    data_sources: List[str]
    queries_executed: int
    iterations_completed: int


class DeepResearchWorkflow(BaseWorkflow):
    """Deep research workflow using existing Maxwell workflows."""

    workflow_id: str = "deep-research"
    name: str = "Deep Research"
    description: str = "Comprehensive research across chat and filesystem data"
    version: str = "1.0"
    category: str = "research"
    tags: set = {"research", "search", "synthesis"}

    # Typed schemas
    InputSchema = DeepResearchInputs
    OutputSchema = DeepResearchOutputs

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Define CLI parameters."""
        return [
            {
                "name": "research_question",
                "type": str,
                "required": True,
                "help": "Research question to investigate",
            },
            {
                "name": "data_sources",
                "type": str,
                "required": False,
                "default": "chat,filesystem",
                "help": "Data sources: chat, filesystem, or both (comma-separated)",
            },
            {
                "name": "max_iterations",
                "type": int,
                "required": False,
                "default": 3,
                "help": "Maximum research iterations",
            },
            {
                "name": "queries_per_iteration",
                "type": int,
                "required": False,
                "default": 5,
                "help": "Queries to generate per iteration",
            },
        ]

    def get_required_inputs(self) -> List[str]:
        """Get required inputs."""
        return ["research_question"]

    def get_produced_outputs(self) -> List[str]:
        """Get produced outputs."""
        return [
            "report",
            "findings_summary",
            "findings",
            "data_sources",
            "queries_executed",
            "iterations_completed",
        ]

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute deep research with typed schemas."""
        try:
            # Parse inputs with type safety
            inputs: DeepResearchInputs = self.parse_inputs(context)  # type: ignore[assignment]

            # Now we have typed access!
            research_question = inputs.research_question
            data_sources = [ds.strip() for ds in inputs.data_sources.lower().split(",")]
            max_iterations = inputs.max_iterations
            queries_per_iteration = inputs.queries_per_iteration

            logger.info(f"Starting research: {research_question}")
            logger.info(f"Data sources: {data_sources}")

            # Research state
            all_findings = []
            used_queries = set()

            # Get LLM client
            llm_client = get_lm()

            # Initial queries
            current_queries = self._generate_queries(
                research_question, data_sources, llm_client, queries_per_iteration
            )

            iteration = 0
            for iteration in range(max_iterations):
                logger.info(f"Research iteration {iteration + 1}/{max_iterations}")

                if not current_queries:
                    break

                # Execute searches
                iteration_findings = []
                for query in current_queries:
                    if query in used_queries:
                        continue

                    used_queries.add(query)
                    findings = self._search_and_extract(query, data_sources, project_root)
                    iteration_findings.extend(findings)

                all_findings.extend(iteration_findings)

                # Generate follow-up queries if not last iteration
                if iteration < max_iterations - 1 and iteration_findings:
                    current_queries = self._generate_followup_queries(
                        research_question, iteration_findings, llm_client, queries_per_iteration
                    )
                else:
                    break

            # Generate final report
            report = self._synthesize_report(research_question, all_findings, llm_client)
            findings_summary = self._summarize_findings(all_findings)

            # Create typed outputs
            outputs = DeepResearchOutputs(
                report=report,
                findings_summary=findings_summary,
                findings=all_findings,
                data_sources=data_sources,
                queries_executed=len(used_queries),
                iterations_completed=iteration + 1,
            )

            # Use helper to create result with metrics
            self.metrics.files_processed = len(all_findings)
            self.metrics.custom_metrics = {
                "queries_executed": len(used_queries),
                "findings_found": len(all_findings),
            }

            return self.create_result(outputs, WorkflowStatus.COMPLETED)

        except Exception as e:
            logger.error(f"Deep research failed: {e}", exc_info=True)
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message=f"Deep research failed: {str(e)}",
            )

    def _generate_queries(
        self, research_question: str, data_sources: List[str], llm_client, limit: int
    ) -> List[str]:
        """Generate initial search queries."""
        source_text = ", ".join(data_sources)
        prompt = f"""Generate {limit} diverse search queries to research this question:

Question: {research_question}
Data sources: {source_text}

Generate search queries that cover different aspects. Return as a JSON list:
["query 1", "query 2", "query 3", ...]
"""

        try:
            response = llm_client.complete(prompt)
            import json

            queries = json.loads(response.text)
            return queries[:limit] if isinstance(queries, list) else [research_question]
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return [research_question]

    def _generate_followup_queries(
        self, research_question: str, findings: List[Dict[str, str]], llm_client, limit: int
    ) -> List[str]:
        """Generate follow-up queries based on findings."""
        findings_text = "\n".join([f.get("content", "")[:200] for f in findings[:3]])

        prompt = f"""Based on these findings, generate {limit} follow-up search queries:

Original question: {research_question}

Current findings:
{findings_text}

Generate follow-up queries to explore gaps or interesting leads. Return as JSON list:
["query 1", "query 2", ...]
"""

        try:
            response = llm_client.complete(prompt)
            import json

            queries = json.loads(response.text)
            return queries[:limit] if isinstance(queries, list) else []
        except Exception as e:
            logger.error(f"Follow-up query generation failed: {e}")
            return []

    def _search_and_extract(
        self, query: str, data_sources: List[str], project_root: Path
    ) -> List[Dict[str, str]]:
        """Execute search across data sources and extract findings."""
        all_results = []

        # Search each data source
        for source in data_sources:
            try:
                if source == "chat":
                    # Try semantic search first
                    result = execute_workflow(
                        "chat-semantic-search", project_root, {"query": query}
                    )
                    if result.status == WorkflowStatus.COMPLETED and result.artifacts:
                        chat_results = result.artifacts.get("results", [])
                        for chat_result in chat_results[:3]:
                            content = ""
                            if isinstance(chat_result, dict):
                                if "user_text" in chat_result and "assistant_text" in chat_result:
                                    content = f"User: {chat_result.get('user_text', '')}\nAssistant: {chat_result.get('assistant_text', '')}"
                                else:
                                    content = chat_result.get("content", str(chat_result))

                            if content:
                                all_results.append(
                                    {
                                        "content": content,
                                        "source": f"chat:{chat_result.get('turn_id', 'unknown')}",
                                        "query": query,
                                        "data_source": "chat",
                                    }
                                )

                elif source == "filesystem":
                    result = execute_workflow("fs-search", project_root, {"query": query})
                    if result.status == WorkflowStatus.COMPLETED and result.artifacts:
                        fs_results = result.artifacts.get("results", [])
                        for fs_result in fs_results[:3]:
                            content = ""
                            if isinstance(fs_result, dict):
                                content = fs_result.get("content", str(fs_result))

                            if content:
                                all_results.append(
                                    {
                                        "content": content,
                                        "source": f"filesystem:{fs_result.get('path', 'unknown')}",
                                        "query": query,
                                        "data_source": "filesystem",
                                    }
                                )

            except Exception as e:
                logger.error(f"Search failed for {source}: {e}")
                continue

        return all_results

    def _synthesize_report(
        self, research_question: str, findings: List[Dict[str, str]], llm_client
    ) -> str:
        """Generate final research report."""
        findings_text = "\n\n".join(
            [
                f"Source: {f['source']}\nContent: {f['content'][:500]}..."
                for f in findings[:10]  # Limit for LLM context
            ]
        )

        prompt = f"""Synthesize a research report answering this question:

Question: {research_question}

Research Findings:
{findings_text}

Create a structured report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (bulleted list)
3. Detailed Analysis
4. Conclusion

Focus on directly answering the research question.
"""

        try:
            response = llm_client.complete(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Report synthesis failed: {e}")
            return f"Research completed with {len(findings)} findings. Report synthesis failed."

    def _summarize_findings(self, findings: List[Dict[str, str]]) -> str:
        """Create summary of findings."""
        if not findings:
            return "No findings found."

        source_counts = {}
        for f in findings:
            source = f["data_source"]
            source_counts[source] = source_counts.get(source, 0) + 1

        summary = (
            f"Found {len(findings)} total findings across {len(source_counts)} data sources:\n"
        )
        for source, count in source_counts.items():
            summary += f"- {source}: {count} findings\n"

        return summary
