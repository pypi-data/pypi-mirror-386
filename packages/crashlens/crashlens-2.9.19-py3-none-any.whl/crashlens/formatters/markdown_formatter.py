"""
Markdown Formatter
Formats detection results in Markdown format for documentation
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils.pii_scrubber import PIIScrubber


class MarkdownFormatter:
    """Formats detections in Markdown format"""
    
    def __init__(self):
        self.severity_colors = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        self.pii_scrubber = PIIScrubber()
    
    def format(self, detections: List[Dict[str, Any]], traces: Dict[str, List[Dict[str, Any]]], model_pricing: Optional[Dict[str, Any]] = None, summary_only: bool = False) -> str:
        """Format detections in Markdown output"""
        if not detections:
            return "**No token waste patterns detected! Your GPT usage looks efficient.**"
        
        output = []
        output.append("🔒 CrashLens runs 100% locally. No data leaves your system.\n")
        if summary_only:
            output.append("> **Summary-only mode:** Prompts, sample inputs, and trace IDs are suppressed for safe internal sharing.\n")
        output.append("# CrashLens Token Waste Report")
        output.append("")
        
        # Add analysis metadata
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output.append(f"**Analysis Date:** {current_time}  \n")
        output.append(f"**Traces Analyzed:** {len(traces):,}  \n")
        output.append("")
        
        # Scrub PII from detections
        scrubbed_detections = [self.pii_scrubber.scrub_detection(detection) for detection in detections]
        
        # Aggregate detections by type
        aggregated = self._aggregate_detections(scrubbed_detections)
        
        # Summary table
        total_waste_cost = sum(d.get('waste_cost', 0) for d in scrubbed_detections)
        total_waste_tokens = sum(d.get('waste_tokens', 0) for d in scrubbed_detections)
        total_ai_spend = self._calculate_total_ai_spend(traces, model_pricing)
        
        # Sanity check: savings shouldn't exceed total spend
        total_waste_cost = min(total_waste_cost, total_ai_spend)
        
        output.append("## Summary")
        output.append("")
        output.append("| Metric | Value |")
        output.append("|--------|-------|")
        # Format spend amount appropriately
        if total_ai_spend >= 0.01:
            spend_str = f"${total_ai_spend:.2f}"
        else:
            spend_str = f"${total_ai_spend:.4f}"
        
        # Format savings amount appropriately
        if total_waste_cost >= 0.01:
            savings_str = f"${total_waste_cost:.2f}"
        else:
            savings_str = f"${total_waste_cost:.4f}"
        
        output.append(f"| Total AI Spend | {spend_str} |")
        output.append(f"| Total Potential Savings | {savings_str} |")
        output.append(f"| Wasted Tokens | {total_waste_tokens:,} |")
        output.append(f"| Issues Found | {len(scrubbed_detections)} |")
        output.append(f"| Traces Analyzed | {len(traces)} |")
        output.append("")
        
        # Format aggregated detections
        for detector_name, group_data in aggregated.items():
            output.append(f"## {group_data['detector']} ({group_data['count']} issues)")
            output.append("")
            
            # Type summary table
            output.append("| Metric | Value |")
            output.append("|--------|-------|")
            output.append(f"| Total Waste Cost | ${group_data['total_waste_cost']:.4f} |")
            output.append(f"| Total Waste Tokens | {group_data['total_waste_tokens']:,} |")
            output.append("")
            
            # Add trace IDs array
            if group_data['trace_ids'] and not summary_only:
                output.append("**Trace IDs**:")
                trace_list = ', '.join(group_data['trace_ids'][:10])  # Show first 10
                if len(group_data['trace_ids']) > 10:
                    trace_list += f", +{len(group_data['trace_ids']) - 10} more"
                output.append(f"`{trace_list}`")
                output.append("")
            
            # Aggregated details
            output.append(self._format_aggregated_detection(group_data, summary_only))
            output.append("")
        
        # Add cost breakdown sections (if we have real costs)
        if total_ai_spend > 0:
            self._add_cost_breakdown_tables(output, traces, summary_only)
        
        # Add next steps section
        output.append("## Next Steps")
        output.append("")
        output.append("- Run `crashlens --detailed` for grouped JSON reports")
        output.append("- Review trace patterns to optimize model routing")
        output.append("- Implement suggested fixes to reduce token waste")
        output.append("")
        
        return "\n".join(output)
    
    def _aggregate_detections(self, detections: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Aggregate detections by detector type"""
        aggregated = {}
        
        for detection in detections:
            # Get the proper detector name from the detection
            detector = detection.get('type', 'unknown')  # Use 'type' field instead of 'detector'
            if detector == 'unknown':
                # Fallback to detector field if type is not available
                detector = detection.get('detector', 'unknown')
            
            # Clean up detector name
            if detector == 'overkill_model':
                detector = 'Overkill Model'
            elif detector == 'retry_loop':
                detector = 'Retry Loop'
            elif detector == 'fallback_storm':
                detector = 'Fallback Storm'
            elif detector == 'fallback_failure':
                detector = 'Fallback Failure'
            else:
                detector = detector.replace('_', ' ').title()
            
            if detector not in aggregated:
                aggregated[detector] = {
                    'detector': detector,
                    'count': 0,
                    'total_waste_cost': 0.0,
                    'total_waste_tokens': 0,
                    'trace_ids': [],
                    'severity': detection.get('severity', 'medium'),
                    'detections': []
                }
            
            group = aggregated[detector]
            group['count'] += 1
            group['total_waste_cost'] += detection.get('waste_cost', 0)
            group['total_waste_tokens'] += detection.get('waste_tokens', 0)
            group['detections'].append(detection)
            
            # Add trace ID to the list
            trace_id = detection.get('trace_id')
            if trace_id and trace_id not in group['trace_ids']:
                group['trace_ids'].append(trace_id)
        
        return aggregated

    def _format_aggregated_detection(self, group_data: Dict[str, Any], summary_only: bool = False) -> str:
        """Format an aggregated detection group in Markdown"""
        lines = []
        detector = group_data.get('detector', 'unknown').replace('_', ' ').title()
        lines.append(f"**Issue**: {group_data['count']} traces flagged by {detector}")
        lines.append("")
        # Suggested fix (optional, can be improved per detector)
        if detector.lower() == 'overkillmodeldetector':
            lines.append(f"**Suggested Fix**: Route short prompts to `{group_data['suggested_model']}`")
        elif detector.lower() == 'retryloopdetector':
            lines.append("**Suggested Fix**: Implement exponential backoff and circuit breakers")
        elif detector.lower() == 'fallbackstormdetector':
            lines.append("**Suggested Fix**: Optimize model selection logic")
        elif detector.lower() == 'fallbackfailuredetector':
            lines.append("**Suggested Fix**: Remove redundant fallback calls after successful cheaper model calls")
        return "\n".join(lines)

    def _format_detection(self, detection: Dict[str, Any], index: int, summary_only: bool = False) -> str:
        """Format a single detection in Markdown (kept for backward compatibility)"""
        severity_emoji = self.severity_colors.get(detection['severity'], '⚪')
        
        lines = []
        lines.append(f"### {severity_emoji} Issue #{index}")
        lines.append("")
        lines.append(f"**Description**: {detection['description']}")
        lines.append("")
        
        # Key metrics
        if detection.get('waste_cost', 0) > 0:
            lines.append(f"- **Waste Cost**: ${detection['waste_cost']:.4f}")
        
        if detection.get('waste_tokens', 0) > 0:
            lines.append(f"- **Waste Tokens**: {detection['waste_tokens']:,}")
        
        # Type-specific details
        if detection['type'] == 'retry_loop':
            lines.append(f"- **Retry Count**: {detection.get('retry_count', 0)}")
            lines.append(f"- **Time Span**: {detection.get('time_span', 'unknown')}")
        
        elif detection['type'] in ['gpt4_short', 'expensive_model_short', 'expensive_model_overkill']:
            lines.append(f"- **Completion Length**: {detection.get('completion_length', 0)} tokens")
            lines.append(f"- **Model Used**: {detection.get('model_used', 'unknown')}")
            lines.append(f"- **Suggested Model**: {detection.get('suggested_model', 'gpt-3.5-turbo')}")
        
        elif detection['type'] == 'fallback_storm':
            lines.append(f"- **Fallback Count**: {detection.get('fallback_count', 0)}")
            models = detection.get('models_sequence', [])
            if models:
                lines.append(f"- **Model Sequence**: {' → '.join(models)}")
            lines.append(f"- **Time Span**: {detection.get('time_span', 'unknown')}")
        
        elif detection['type'] == 'fallback_failure':
            lines.append(f"- **Primary Model**: {detection.get('primary_model', 'unknown')}")
            lines.append(f"- **Fallback Model**: {detection.get('fallback_model', 'unknown')}")
            lines.append(f"- **Time Between Calls**: {detection.get('time_between_calls', 'unknown')}")
            if not summary_only:
                lines.append(f"- **Primary Prompt**: `{detection.get('primary_prompt', '')[:50]}{'...' if len(detection.get('primary_prompt', '')) > 50 else ''}`")
        
        # Trace ID (suppress in summary_only)
        if not summary_only:
            lines.append(f"- **Trace ID**: `{detection.get('trace_id', 'unknown')}`")
            lines.append("")
        
        return "\n".join(lines) 

    def _calculate_total_ai_spend(self, traces: Dict[str, List[Dict[str, Any]]], model_pricing: Optional[Dict[str, Any]] = None) -> float:
        """Calculate the total cost of all traces using existing cost field or pricing config"""
        total = 0.0
        for records in traces.values():
            for record in records:
                # First try to use existing cost field
                if 'cost' in record and record['cost'] is not None:
                    total += record['cost']
                    continue
                
                # Fallback to calculating from pricing config
                if model_pricing:
                    model = record.get('model', record.get('input', {}).get('model', 'gpt-3.5-turbo'))
                    
                    # Get tokens from various possible locations
                    usage = record.get('usage', {})
                    input_tokens = (record.get('prompt_tokens') or 
                                   usage.get('prompt_tokens') or 0)
                    output_tokens = (record.get('completion_tokens') or 
                                    usage.get('completion_tokens') or 0)
                    
                    model_config = model_pricing.get(model, {})
                    if model_config:
                        input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
                        output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
                        total += input_cost + output_cost
        return total

    def _add_cost_breakdown_tables(self, output: List[str], traces: Dict[str, List[Dict[str, Any]]], summary_only: bool):
        """Add top expensive traces and cost by model tables"""
        from collections import defaultdict
        
        # Calculate cost breakdown by model
        model_costs = defaultdict(float)
        trace_costs = {}
        
        for trace_id, records in traces.items():
            trace_cost = 0.0
            for record in records:
                cost = record.get('cost') or 0.0
                model = record.get('input', {}).get('model', record.get('model', 'unknown'))
                
                trace_cost += cost
                model_costs[model] += cost
            
            if trace_cost > 0:
                trace_costs[trace_id] = trace_cost
        
        # Top expensive traces table
        if trace_costs:
            output.append("## Top Expensive Traces")
            output.append("")
            output.append("| Rank | Trace ID | Model | Cost |")
            output.append("|------|----------|-------|------|")
            
            sorted_traces = sorted(trace_costs.items(), key=lambda x: x[1], reverse=True)[:3]
            for i, (trace_id, cost) in enumerate(sorted_traces, 1):
                cost_str = f"${cost:.2f}" if cost >= 0.01 else f"${cost:.4f}"
                if summary_only:
                    output.append(f"| {i} | trace_*** | *** | {cost_str} |")
                else:
                    # Extract model from first record of this trace
                    first_record = traces[trace_id][0] if traces[trace_id] else {}
                    model = first_record.get('input', {}).get('model', first_record.get('model', 'unknown'))
                    output.append(f"| {i} | {trace_id} | {model} | {cost_str} |")
            output.append("")
        
        # Cost by model table
        if model_costs:
            total_cost = sum(model_costs.values())
            output.append("## Cost by Model")
            output.append("")
            output.append("| Model | Cost | Percentage |")
            output.append("|-------|------|------------|")
            
            sorted_models = sorted(model_costs.items(), key=lambda x: x[1], reverse=True)
            for model, cost in sorted_models:
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                cost_str = f"${cost:.2f}" if cost >= 0.01 else f"${cost:.4f}"
                output.append(f"| {model} | {cost_str} | {percentage:.0f}% |")
            output.append("")