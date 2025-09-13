"""
InteractionTracker prevents duplicate testing of interactive elements during scroll exploration.

This class tracks which interactive elements (dropdowns, modals, accordions, forms) have already
been tested in each viewport to avoid redundant testing of sticky/persistent elements like
navigation menus that remain visible across multiple scroll positions.
"""

from typing import Dict, List, Set, Any, Optional


class InteractionTracker:
    """
    Tracks tested interactive elements to prevent duplicate testing during scroll exploration.
    
    Key features:
    - Viewport-aware tracking (same element can be tested once per viewport)
    - Element signature generation for unique identification
    - Filtering of already-tested elements
    - Reset capability for new viewports
    """
    
    def __init__(self):
        """Initialize the interaction tracker."""
        # viewport_key -> set of element signatures that have been tested
        self.tested_elements: Dict[str, Set[str]] = {}
        
        # Current viewport context for tracking
        self.current_viewport: str = ""
        
        # Statistics for logging and debugging
        self.interaction_counts: Dict[str, Dict[str, int]] = {}  # viewport -> element_type -> count
        self.skipped_counts: Dict[str, Dict[str, int]] = {}     # viewport -> element_type -> count
    
    def set_viewport_context(self, viewport_key: str):
        """
        Set the current viewport context for element tracking.
        
        Args:
            viewport_key: Viewport identifier (e.g., "1280x800", "768x1024")
        """
        self.current_viewport = viewport_key
        
        # Initialize tracking sets for this viewport if not exists
        if viewport_key not in self.tested_elements:
            self.tested_elements[viewport_key] = set()
            self.interaction_counts[viewport_key] = {}
            self.skipped_counts[viewport_key] = {}
    
    def reset_for_viewport(self, viewport_key: str):
        """
        Reset tracking for a specific viewport (useful when starting fresh exploration).
        
        Args:
            viewport_key: Viewport identifier to reset
        """
        if viewport_key in self.tested_elements:
            self.tested_elements[viewport_key].clear()
            self.interaction_counts[viewport_key].clear()
            self.skipped_counts[viewport_key].clear()
    
    def filter_untested_elements(self, elements: List[Dict[str, Any]], element_type: str) -> List[Dict[str, Any]]:
        """
        Filter out elements that have already been tested in the current viewport.
        
        Args:
            elements: List of element info dictionaries from _find_viewport_visible_elements
            element_type: Type of element ("dropdown", "modal", "accordion", "form")
            
        Returns:
            List of elements that haven't been tested yet
        """
        if not self.current_viewport:
            # If no viewport context set, return all elements (fallback behavior)
            return elements
        
        untested_elements = []
        skipped_count = 0
        
        for element_info in elements:
            signature = self._create_element_signature(element_info, element_type)
            
            if signature not in self.tested_elements[self.current_viewport]:
                untested_elements.append(element_info)
            else:
                skipped_count += 1
        
        # Update statistics
        if skipped_count > 0:
            if element_type not in self.skipped_counts[self.current_viewport]:
                self.skipped_counts[self.current_viewport][element_type] = 0
            self.skipped_counts[self.current_viewport][element_type] += skipped_count
            
            print(f"      🔄 Skipped {skipped_count} already-tested {element_type}(s) in {self.current_viewport}")
        
        return untested_elements
    
    def mark_as_tested(self, element_info: Dict[str, Any], element_type: str):
        """
        Mark an element as tested in the current viewport.
        
        Args:
            element_info: Element info dictionary
            element_type: Type of element ("dropdown", "modal", "accordion", "form")
        """
        if not self.current_viewport:
            return
        
        signature = self._create_element_signature(element_info, element_type)
        self.tested_elements[self.current_viewport].add(signature)
        
        # Update statistics
        if element_type not in self.interaction_counts[self.current_viewport]:
            self.interaction_counts[self.current_viewport][element_type] = 0
        self.interaction_counts[self.current_viewport][element_type] += 1
    
    def is_element_tested(self, element_info: Dict[str, Any], element_type: str) -> bool:
        """
        Check if an element has already been tested in the current viewport.
        
        Args:
            element_info: Element info dictionary
            element_type: Type of element
            
        Returns:
            True if element has been tested, False otherwise
        """
        if not self.current_viewport:
            return False
        
        signature = self._create_element_signature(element_info, element_type)
        return signature in self.tested_elements[self.current_viewport]
    
    def _create_element_signature(self, element_info: Dict[str, Any], element_type: str) -> str:
        """
        Create a unique signature for an element to identify it across scroll positions.
        
        The signature combines:
        - Element type (dropdown, modal, etc.)
        - Element selector (most specific identifier)
        - Key identifying text (first 20 chars for disambiguation)
        
        Args:
            element_info: Element info dictionary with 'selector', 'text', etc.
            element_type: Type of element
            
        Returns:
            Unique signature string
        """
        selector = element_info.get('selector', 'unknown')
        
        # Use element text for disambiguation, but limit length
        element_text = element_info.get('text', '').strip()
        text_key = element_text[:20] if element_text else 'no-text'
        
        # Include base selector for additional context
        base_selector = element_info.get('baseSelector', '')
        base_key = base_selector.split('.')[-1].split('[')[0] if base_selector else ''
        
        # Create signature: type:selector:text:base
        signature = f"{element_type}:{selector}:{text_key}:{base_key}"
        
        return signature
    
    def get_testing_summary(self, viewport_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of testing activity for debugging/logging.
        
        Args:
            viewport_key: Specific viewport to get summary for, or None for current viewport
            
        Returns:
            Dictionary with testing statistics
        """
        target_viewport = viewport_key or self.current_viewport
        
        if target_viewport not in self.tested_elements:
            return {"viewport": target_viewport, "tested": 0, "skipped": 0, "details": {}}
        
        tested_total = len(self.tested_elements[target_viewport])
        skipped_total = sum(self.skipped_counts[target_viewport].values())
        
        return {
            "viewport": target_viewport,
            "tested_total": tested_total,
            "skipped_total": skipped_total,
            "tested_by_type": dict(self.interaction_counts[target_viewport]),
            "skipped_by_type": dict(self.skipped_counts[target_viewport]),
            "tested_signatures": list(self.tested_elements[target_viewport])
        }
    
    def get_all_viewports_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get testing summary for all viewports.
        
        Returns:
            Dictionary mapping viewport keys to their testing summaries
        """
        return {
            viewport: self.get_testing_summary(viewport)
            for viewport in self.tested_elements.keys()
        }
    
    def log_final_summary(self):
        """Log a final summary of all testing activity across viewports."""
        print(f"\n📊 InteractionTracker Final Summary:")
        
        total_tested = 0
        total_skipped = 0
        
        for viewport_key in self.tested_elements.keys():
            summary = self.get_testing_summary(viewport_key)
            tested = summary['tested_total']
            skipped = summary['skipped_total']
            
            total_tested += tested
            total_skipped += skipped
            
            print(f"  📱 {viewport_key}: {tested} tested, {skipped} skipped")
            
            # Show breakdown by element type if there's activity
            if tested > 0 or skipped > 0:
                for element_type, count in summary['tested_by_type'].items():
                    skipped_count = summary['skipped_by_type'].get(element_type, 0)
                    print(f"    • {element_type}: {count} tested, {skipped_count} skipped")
        
        efficiency_saved = total_skipped / (total_tested + total_skipped) * 100 if (total_tested + total_skipped) > 0 else 0
        print(f"  🎯 Overall: {total_tested} interactions, {total_skipped} duplicates prevented ({efficiency_saved:.1f}% efficiency gain)")
