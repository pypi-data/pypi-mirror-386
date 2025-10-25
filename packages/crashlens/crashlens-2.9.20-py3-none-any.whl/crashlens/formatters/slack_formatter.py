"""
CrashLens FinOps Formatter
Compact, scannable forma         # Compact header with key metrics
        output.append(f"📊 CrashLe                    trace_lines.append(f"{i}. {trace_id} → {model} → {cost_str}")
            
            output.append(f"💡 Top {len(trace_lines)} Expensive Traces: " + " | ".join(trace_lines))Report – {timestamp} | Traces: {len(traces)} | Spend: {spend_str} | Savings: {savings_str}")
        output.append("")
        
        # Detector summaries - sorted by waste amount    output.append(f"📊 CrashLens Report – {timestamp} | Traces: {len(t            output.append(f"💡 Top {len(trace_lines)} Expensive Traces: " + " | ".join(trace_lines))aces)} | Spend: {spend_str} | Savings: {savings_str}")     # Compact header with key metrics
        output.append(f"📊 CrashL            output.append(f"💡 Top {len(trace_lines)} Expensive Traces: " + " | ".join(trace_lines))ns Report – {timestamp} | Traces: {len(traces)} | Spend: {spend_str} | Savings: {savings_str}")er optimized for FinOps/AI infrastructure teams
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils.pii_scrubber import PIIScrubber


class SlackFormatter:
    """Formats detections in FinOps-focused compact format"""
    
    def __init__(self, max_traces_to_show: int = 3):
        self.max_traces_to_show = max_traces_to_show
        
        self.detector_emojis = {
            'retry_loop': '🔁',
            'gpt4_short': '�',
            'expensive_model_short': '�',
            'fallback_storm': '⚡',
            'fallback_failure': '�'
        }
        
        self.detector_fixes = {
            'retry_loop': 'exponential backoff',
            'gpt4_short': 'use cheaper model for short prompts',
            'expensive_model_short': 'use cheaper model for short prompts',
            'fallback_storm': 'optimize model selection',
            'fallback_failure': 'remove redundant fallbacks'
        }
        
        self.pii_scrubber = PIIScrubber()
        
        self.pii_scrubber = PIIScrubber()
    
    def format(self, detections: List[Dict[str, Any]], traces: Dict[str, List[Dict[str, Any]]], model_pricing: Optional[Dict[str, Any]] = None, summary_only: bool = False, include_json_footer: bool = False) -> str:
        """Format detections in FinOps-focused compact format"""
        if not detections:
            return "🔒 CrashLens runs 100% locally. No data leaves your system.\n\n✅ *No token waste patterns detected!* Your GPT usage looks efficient. 🎉"
        
        # Calculate costs and metrics
        total_ai_spend = self._calculate_total_ai_spend(traces, model_pricing)
        total_savings = sum(d.get('waste_cost', 0) for d in detections)
        total_savings = min(total_savings, total_ai_spend)  # Sanity check
        
        # Generate timestamp and header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spend_str = f"${total_ai_spend:.4f}" if total_ai_spend < 0.01 else f"${total_ai_spend:.2f}"
        savings_str = f"${total_savings:.4f}" if total_savings < 0.01 else f"${total_savings:.2f}"
        
        output = []
        if summary_only:
            output.append("🔒 CrashLens runs 100% locally. No data leaves your system.")
            output.append("📝 *Summary-only mode:* Prompts, sample inputs, and trace IDs are suppressed for safe internal sharing.")
            output.append("")
        
        # Enhanced header with Slack-native formatting
        output.append(f"🚨 *CrashLens Token Waste Report* 🚨")
        output.append(f"📊 *Analysis Date:* {timestamp}")
        output.append("")
        
        # Summary section with bullet points
        total_waste_tokens = sum(d.get('waste_tokens', 0) for d in detections)
        output.append("📋 *Report Summary:*")
        output.append(f"• 💰 *Total AI Spend:* {spend_str}")
        output.append(f"• 🔥 *Potential Savings:* {savings_str}")
        output.append(f"• 🎯 *Wasted Tokens:* {total_waste_tokens:,}")
        output.append(f"• ⚠️ *Issues Found:* {len(detections)}")
        output.append(f"• 📈 *Traces Analyzed:* {len(traces)}")
        output.append("")
        
        # Detector summaries - sorted by waste amount
        scrubbed_detections = [self.pii_scrubber.scrub_detection(detection) for detection in detections]
        aggregated = self._aggregate_detections(scrubbed_detections)
        sorted_detectors = sorted(aggregated.items(), key=lambda x: x[1]['total_waste_cost'], reverse=True)
        
        for det_type, group_data in sorted_detectors:
            # Enhanced emoji mapping
            emoji_map = {
                'retry_loop': '🔄',
                'fallback_storm': '⚡',
                'fallback_failure': '📢',
                'overkill_model': '❓'
            }
            emoji = emoji_map.get(group_data['detector'], '❓')
            detector_name = group_data['detector'].replace('_', ' ').title()
            waste_str = f"${group_data['total_waste_cost']:.4f}" if group_data['total_waste_cost'] < 0.01 else f"${group_data['total_waste_cost']:.2f}"
            
            # More specific fix suggestions
            fix_hint = self._get_specific_fix_suggestion(group_data)
            
            output.append(f"{emoji} *{detector_name}* • {group_data['count']} traces • {waste_str} wasted")
            output.append(f"   💡 *Fix:* {fix_hint}")
            
            # Add essential debugging details
            if group_data['total_waste_tokens'] > 0:
                output.append(f"   🎯 *Wasted tokens:* {group_data['total_waste_tokens']:,}")
            
            # Show affected trace IDs (critical for debugging)
            if not summary_only:
                trace_ids = group_data.get('trace_ids', [])
                if trace_ids:
                    trace_count = len(trace_ids)
                    trace_list = ', '.join(trace_ids[:5])  # Show up to 5 trace IDs
                    if len(trace_ids) > 5:
                        trace_list += f", +{len(trace_ids) - 5} more"
                    output.append(f"   🔗 *Traces ({trace_count}):* `{trace_list}`")
            
            output.append("")  # Add spacing between detector groups
        
        output.append("")
        
        # Top expensive traces
        self._add_top_traces(output, traces, summary_only)
        
        # Model breakdown - single line format
        self._add_model_breakdown(output, traces)
        
        # Add call to action
        output.append("💡 *Next Steps:*")
        output.append("• Run `crashlens --detailed` for grouped JSON reports")
        output.append("• Review trace patterns to optimize model routing")
        output.append("• Implement suggested fixes to reduce token waste")
        output.append("")
        
        # Optional JSON footer for machine-readable data
        if include_json_footer:
            self._add_json_footer(output, detections, traces, total_ai_spend, total_savings)
        
        return "\n".join(output)
    
    def _add_top_traces(self, output: List[str], traces: Dict[str, List[Dict[str, Any]]], summary_only: bool):
        """Add top expensive traces section with Slack-native formatting"""
        trace_costs = {}
        
        for trace_id, records in traces.items():
            trace_cost = sum((record.get('cost') or 0.0) for record in records)
            if trace_cost > 0:
                trace_costs[trace_id] = trace_cost
        
        if trace_costs:
            sorted_traces = sorted(trace_costs.items(), key=lambda x: x[1], reverse=True)[:self.max_traces_to_show]
            
            output.append("🏆 *Top Expensive Traces:*")
            for i, (trace_id, cost) in enumerate(sorted_traces, 1):
                cost_str = f"${cost:.4f}" if cost < 0.01 else f"${cost:.2f}"
                if summary_only:
                    output.append(f"• #{i} → `trace_***` → {cost_str}")
                else:
                    # Get model from first record
                    first_record = traces[trace_id][0] if traces[trace_id] else {}
                    model = first_record.get('input', {}).get('model', first_record.get('model', 'unknown'))
                    output.append(f"• #{i} → `{trace_id}` → {model} → {cost_str}")
            output.append("")
    
    def _add_model_breakdown(self, output: List[str], traces: Dict[str, List[Dict[str, Any]]]):
        """Add model cost breakdown with Slack-native formatting"""
        from collections import defaultdict
        
        model_costs = defaultdict(float)
        
        for records in traces.values():
            for record in records:
                cost = record.get('cost') or 0.0
                model = record.get('input', {}).get('model', record.get('model', 'unknown'))
                model_costs[model] += cost
        
        if model_costs:
            total_cost = sum(model_costs.values())
            sorted_models = sorted(model_costs.items(), key=lambda x: x[1], reverse=True)
            
            output.append("🤖 *Cost by Model:*")
            for model, cost in sorted_models:
                cost_str = f"${cost:.4f}" if cost < 0.01 else f"${cost:.2f}"
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                output.append(f"• {model} → {cost_str} ({percentage:.0f}%)")
            output.append("")

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
                detector = 'overkill_model'
            elif detector == 'retry_loop':
                detector = 'retry_loop'
            elif detector == 'fallback_storm':
                detector = 'fallback_storm'
            elif detector == 'fallback_failure':
                detector = 'fallback_failure'
            
            if detector not in aggregated:
                aggregated[detector] = {
                    'detector': detector,
                    'count': 0,
                    'total_waste_cost': 0.0,
                    'total_waste_tokens': 0,
                    'trace_ids': [],
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

    def _get_specific_fix_suggestion(self, group_data: Dict[str, Any]) -> str:
        """Generate specific, actionable fix suggestions based on detection data"""
        detector = group_data.get('detector', 'unknown').lower()
        if detector == 'overkillmodeldetector':
            model_used = group_data.get('model_used', 'expensive model')
            suggested_model = group_data.get('suggested_model', 'cheaper model')
            return f"route short prompts from {model_used} → {suggested_model}"
        elif detector == 'retryloopdetector':
            retry_counts = [d.get('retry_count', 0) for d in group_data['detections']]
            max_retries = max(retry_counts) if retry_counts else 0
            if max_retries > 5:
                return f"implement exponential backoff (saw {max_retries} retries)"
            else:
                return "add circuit breakers and retry limits"
        elif detector == 'fallbackstormdetector':
            sequences = []
            for d in group_data['detections']:
                seq = d.get('models_sequence', [])
                if seq and len(seq) > 2:
                    sequences.append(' → '.join(seq[:3]))
            if sequences:
                return f"fix cascade: {sequences[0]}"
            else:
                return "optimize model selection logic"
        elif detector == 'fallbackfailuredetector':
            pairs = []
            for d in group_data['detections']:
                primary = d.get('primary_model', '')
                fallback = d.get('fallback_model', '')
                if primary and fallback:
                    pairs.append(f"{primary}→{fallback}")
            if pairs:
                return f"remove redundant fallback: {pairs[0]}"
            else:
                return "remove unnecessary fallback calls"
        else:
            return self.detector_fixes.get(detector, 'optimize usage')

    def _add_json_footer(self, output: List[str], detections: List[Dict[str, Any]], traces: Dict[str, List[Dict[str, Any]]], total_spend: float, total_savings: float):
        """Add machine-readable JSON footer for automation"""
        import json
        
        # Prepare summary data for JSON
        trace_count = len(traces)
        detection_count = len(detections)
        
        # Group detections by type
        detections_by_type = {}
        for detection in detections:
            det_type = detection.get('type', 'unknown')
            if det_type not in detections_by_type:
                detections_by_type[det_type] = []
            detections_by_type[det_type].append(detection)
        
        # Create machine-readable summary
        json_summary = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "traces_analyzed": trace_count,
                "total_spend": round(total_spend, 6),
                "total_savings": round(total_savings, 6),
                "issues_found": detection_count
            },
            "detections": {
                det_type: {
                    "count": len(dets),
                    "total_waste": round(sum(d.get('waste_cost', 0) for d in dets), 6)
                }
                for det_type, dets in detections_by_type.items()
            }
        }
        
        output.append("")
        output.append("```json")
        output.append(json.dumps(json_summary, indent=2))
        output.append("```")
    
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