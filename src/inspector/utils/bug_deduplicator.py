"""
Bug deduplication system that identifies and merges duplicate bug reports.
"""

import asyncio
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

try:
    from ...core.types import Bug, Evidence
except ImportError:
    from core.types import Bug, Evidence


class BugDeduplicator:
    """
    Analyzes a list of bugs to identify and merge duplicates.
    Uses the same AI model that was used for the original bug detection.
    """
    
    def __init__(self, model: str = 'cohere'):
        """
        Initialize bug deduplicator.
        
        Args:
            model: Which model to use ('cohere' or 'gemini') - should match the original scan
        """
        self.model = model.lower()
    
    async def deduplicate_bugs(self, bugs: List[Bug]) -> List[Bug]:
        """
        Deduplicate a list of bugs, merging similar ones and prioritizing simpler reproduction steps.
        
        Args:
            bugs: List of Bug objects to deduplicate
            
        Returns:
            Deduplicated list of Bug objects
        """
        if len(bugs) <= 1:
            return bugs
        
        print(f"🔍 Deduplicating {len(bugs)} bugs using {self.model} model...")
        
        # Convert bugs to a format suitable for AI analysis
        bugs_data = self._prepare_bugs_for_analysis(bugs)
        
        # Get deduplication analysis from AI model
        dedup_result = await self._analyze_duplicates(bugs_data)
        
        if dedup_result is None:
            print("⚠️ Deduplication failed, returning original bugs")
            return bugs
        
        # Process the deduplication result
        deduplicated_bugs = self._process_deduplication_result(bugs, dedup_result)
        
        print(f"✅ Deduplication complete: {len(bugs)} → {len(deduplicated_bugs)} bugs")
        return deduplicated_bugs
    
    def _prepare_bugs_for_analysis(self, bugs: List[Bug]) -> str:
        """
        Prepare bugs data for AI analysis by creating a structured summary.
        
        Args:
            bugs: List of Bug objects
            
        Returns:
            JSON string with bug summaries for analysis
        """
        bugs_summary = []
        
        for i, bug in enumerate(bugs):
            # Count reproduction steps to assess complexity
            repro_step_count = len(bug.reproduction_steps) if bug.reproduction_steps else 0
            
            # Create a summary for this bug
            bug_summary = {
                "index": i,
                "id": bug.id,
                "type": bug.type,
                "severity": bug.severity,
                "page_url": bug.page_url,
                "summary": bug.summary,
                "reproduction_steps_count": repro_step_count,
                "reproduction_steps": bug.reproduction_steps[:3] if bug.reproduction_steps else [],  # First 3 steps for context
                "affected_elements": bug.affected_elements[:3] if bug.affected_elements else [],  # First 3 elements
                "viewport": bug.evidence.viewport if bug.evidence and bug.evidence.viewport else None,
                "has_screenshot": bool(bug.evidence and bug.evidence.screenshot_path)
            }
            bugs_summary.append(bug_summary)
        
        return json.dumps(bugs_summary, indent=2)
    
    async def _analyze_duplicates(self, bugs_data: str) -> Optional[Dict[str, Any]]:
        """
        Use AI model to analyze bugs and identify duplicates.
        
        Args:
            bugs_data: JSON string with bug summaries
            
        Returns:
            Dictionary with deduplication instructions, or None if analysis failed
        """
        if self.model == 'gemini':
            return await self._analyze_with_gemini(bugs_data)
        else:  # Default to cohere
            return await self._analyze_with_cohere(bugs_data)
    
    async def _analyze_with_cohere(self, bugs_data: str) -> Optional[Dict[str, Any]]:
        """Analyze duplicates using Cohere model"""
        try:
            from .cohere_analyzer import CohereAnalyzer
            
            # Create analyzer instance
            analyzer = CohereAnalyzer()
            
            # Create deduplication prompt
            prompt = self._create_deduplication_prompt(bugs_data)
            
            # Use Cohere's text generation for deduplication analysis
            text_model = 'command-r-plus'  # Use a known working text model
            
            # Cohere doesn't have native async support, so we'll run in executor
            loop = asyncio.get_event_loop()
            
            def sync_call():
                return analyzer.client.chat(
                    model=text_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=analyzer.generation_config["temperature"],
                    max_tokens=analyzer.generation_config["max_tokens"]
                )
            
            response = await loop.run_in_executor(None, sync_call)
            
            # Parse the response
            response_text = response.message.content[0].text if response.message.content else ""
            return self._parse_deduplication_response(response_text)
            
        except Exception as e:
            print(f"❌ Cohere deduplication analysis failed: {str(e)}")
            return None
    
    async def _analyze_with_gemini(self, bugs_data: str) -> Optional[Dict[str, Any]]:
        """Analyze duplicates using Gemini model"""
        try:
            from .gemini_analyzer import GeminiAnalyzer
            
            # Create analyzer instance
            analyzer = GeminiAnalyzer()
            
            # Create deduplication prompt
            prompt = self._create_deduplication_prompt(bugs_data)
            
            # Use Gemini for deduplication analysis
            response = await analyzer.model.generate_content_async(
                prompt,
                generation_config=analyzer.generation_config
            )
            
            # Parse the response
            return self._parse_deduplication_response(response.text)
            
        except Exception as e:
            print(f"❌ Gemini deduplication analysis failed: {str(e)}")
            return None
    
    def _create_deduplication_prompt(self, bugs_data: str) -> str:
        """
        Create a prompt for AI model to analyze bug duplicates.
        
        Args:
            bugs_data: JSON string with bug summaries
            
        Returns:
            Prompt string for AI analysis
        """
        return f"""You are a QA engineer analyzing bug reports to identify duplicates. Your task is to find bugs that represent the same underlying issue and group them together.

IMPORTANT CRITERIA FOR DUPLICATES:
1. **Same root cause**: Bugs that stem from the same underlying problem (e.g., same broken CSS, same missing image, same layout issue)
2. **Same visual manifestation**: Bugs that describe the same visual problem, even if discovered through different interactions
3. **Same affected element**: Bugs affecting the same UI component or element
4. **Different viewports/contexts don't make bugs different**: The same visual issue seen on mobile vs desktop is still the same bug

DEDUPLICATION RULES:
- When merging duplicates, ALWAYS prefer the bug with the FEWEST reproduction steps
- If reproduction step counts are equal, prefer the bug that doesn't require viewport changes or complex interactions
- Preserve the most descriptive summary and combine affected elements from all duplicates
- Keep the highest severity level among duplicates
- The SAME issue i multiple different viewports is still the same bug - if you see it for desktop, tablet and/or mobile, merge it to one and remove any window resizing steps.
Here are the bug reports to analyze:

{bugs_data}

Please respond with a JSON object in this exact format:
{{
  "duplicate_groups": [
    {{
      "primary_bug_index": 0,
      "duplicate_indices": [1, 2],
      "reason": "All three bugs describe the same rotated pink image container issue - same visual problem, same affected element, just discovered in different contexts"
    }}
  ],
  "unique_bugs": [3, 4, 5]
}}

Where:
- `duplicate_groups`: Array of groups where bugs are duplicates of each other
- `primary_bug_index`: Index of the bug to keep (should have simplest reproduction steps)
- `duplicate_indices`: Indices of bugs to merge into the primary bug
- `reason`: Brief explanation of why these bugs are duplicates
- `unique_bugs`: Indices of bugs that have no duplicates

Be conservative - only group bugs that are clearly the same issue. When in doubt, keep them separate."""
    
    def _parse_deduplication_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the AI model's deduplication response.
        
        Args:
            response_text: Raw response from AI model
            
        Returns:
            Parsed deduplication instructions, or None if parsing failed
        """
        try:
            # Try to extract JSON from the response
            # Look for JSON block in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                print("❌ No JSON found in deduplication response")
                return None
            
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            
            # Validate the structure
            if not isinstance(result.get('duplicate_groups'), list):
                print("❌ Invalid deduplication response structure")
                return None
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse deduplication response as JSON: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Error parsing deduplication response: {str(e)}")
            return None
    
    def _process_deduplication_result(self, original_bugs: List[Bug], dedup_result: Dict[str, Any]) -> List[Bug]:
        """
        Process the deduplication result to create the final deduplicated bug list.
        
        Args:
            original_bugs: Original list of bugs
            dedup_result: Deduplication instructions from AI
            
        Returns:
            Deduplicated list of bugs
        """
        try:
            deduplicated_bugs = []
            processed_indices = set()
            
            # Process duplicate groups
            for group in dedup_result.get('duplicate_groups', []):
                primary_index = group.get('primary_bug_index')
                duplicate_indices = group.get('duplicate_indices', [])
                reason = group.get('reason', 'Identified as duplicate')
                
                if primary_index is None or not isinstance(duplicate_indices, list):
                    continue
                
                # Validate indices
                all_indices = [primary_index] + duplicate_indices
                if any(idx < 0 or idx >= len(original_bugs) for idx in all_indices):
                    print(f"⚠️ Invalid bug indices in group: {all_indices}")
                    continue
                
                # Get the primary bug and duplicates
                primary_bug = original_bugs[primary_index]
                duplicate_bugs = [original_bugs[idx] for idx in duplicate_indices]
                
                # Merge the bugs
                merged_bug = self._merge_bugs(primary_bug, duplicate_bugs, reason)
                deduplicated_bugs.append(merged_bug)
                
                # Mark all indices as processed
                processed_indices.update(all_indices)
                
                print(f"🔗 Merged {len(duplicate_indices)} duplicates into bug: {merged_bug.summary[:60]}...")
            
            # Add unique bugs (those not in any duplicate group)
            unique_indices = dedup_result.get('unique_bugs', [])
            for idx in unique_indices:
                if 0 <= idx < len(original_bugs) and idx not in processed_indices:
                    deduplicated_bugs.append(original_bugs[idx])
                    processed_indices.add(idx)
            
            # Add any remaining bugs that weren't mentioned in the result
            for idx, bug in enumerate(original_bugs):
                if idx not in processed_indices:
                    deduplicated_bugs.append(bug)
                    print(f"⚠️ Bug {idx} not mentioned in deduplication result, keeping as unique")
            
            return deduplicated_bugs
            
        except Exception as e:
            print(f"❌ Error processing deduplication result: {str(e)}")
            return original_bugs
    
    def _merge_bugs(self, primary_bug: Bug, duplicate_bugs: List[Bug], reason: str) -> Bug:
        """
        Merge duplicate bugs into the primary bug.
        
        Args:
            primary_bug: The bug to keep as primary
            duplicate_bugs: List of bugs to merge into primary
            reason: Reason for the merge
            
        Returns:
            Merged bug object
        """
        # Start with a copy of the primary bug
        merged_bug = Bug(
            id=primary_bug.id,
            type=primary_bug.type,
            severity=primary_bug.severity,
            page_url=primary_bug.page_url,
            summary=primary_bug.summary,
            suggested_fix=primary_bug.suggested_fix,
            evidence=primary_bug.evidence,
            reproduction_steps=primary_bug.reproduction_steps.copy() if primary_bug.reproduction_steps else [],
            fix_steps=primary_bug.fix_steps.copy() if primary_bug.fix_steps else [],
            affected_elements=primary_bug.affected_elements.copy() if primary_bug.affected_elements else [],
            impact_description=primary_bug.impact_description,
            # Copy other fields from primary bug
            wcag_guidelines=primary_bug.wcag_guidelines.copy() if primary_bug.wcag_guidelines else [],
            business_impact=primary_bug.business_impact,
            technical_details=primary_bug.technical_details,
            priority=primary_bug.priority,
            category=primary_bug.category,
            estimated_effort=primary_bug.estimated_effort,
            tags=primary_bug.tags.copy() if primary_bug.tags else []
        )
        
        # Collect all affected elements and URLs
        all_affected_elements = set(merged_bug.affected_elements)
        all_page_urls = {merged_bug.page_url}
        
        # Find the highest severity
        severities = ['low', 'medium', 'high', 'critical']
        max_severity = primary_bug.severity
        
        for dup_bug in duplicate_bugs:
            # Collect affected elements
            if dup_bug.affected_elements:
                all_affected_elements.update(dup_bug.affected_elements)
            
            # Collect page URLs
            all_page_urls.add(dup_bug.page_url)
            
            # Update severity to highest
            if severities.index(dup_bug.severity) > severities.index(max_severity):
                max_severity = dup_bug.severity
        
        # Update merged bug
        merged_bug.severity = max_severity
        merged_bug.affected_elements = list(all_affected_elements)
        
        # Update summary to indicate it affects multiple pages if needed
        if len(all_page_urls) > 1:
            merged_bug.summary += f" (affects {len(all_page_urls)} pages)"
        
        # Set deduplication metadata
        merged_bug.is_deduplicated = True
        merged_bug.original_bug_ids = [primary_bug.id] + [dup.id for dup in duplicate_bugs]
        merged_bug.deduplication_reason = reason
        
        # Add deduplication info to impact description
        dup_count = len(duplicate_bugs)
        dedup_info = f"Deduplicated from {dup_count} similar report{'s' if dup_count != 1 else ''}: {reason}"
        
        if merged_bug.impact_description:
            merged_bug.impact_description += f"\n\n{dedup_info}"
        else:
            merged_bug.impact_description = dedup_info
        
        return merged_bug
