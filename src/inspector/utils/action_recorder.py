import time
from typing import List, Optional
from playwright.async_api import Page

try:
    from ...core.types import ReproStep
except ImportError:
    from core.types import ReproStep


class ActionRecorder:
    """
    Records user actions during testing to generate reproduction steps for bugs.
    
    This class tracks all interactions with the page and can generate a sequence
    of steps that developers can follow to reproduce identified issues.
    """
    
    def __init__(self, page_url: str, initial_viewport: Optional[str] = None):
        self.page_url = page_url
        self.current_viewport = initial_viewport
        self.steps: List[ReproStep] = []
        self.step_counter = 0
        
    def record_navigation(self, url: str, description: str = ""):
        """Record a navigation action"""
        self._add_step(
            action="navigate",
            target=url,
            description=description or f"Navigate to {url}"
        )
    
    def record_click(self, selector: str, element_text: str = "", description: str = ""):
        """Record a click action"""
        desc = description
        if not desc and element_text:
            desc = f"Click on '{element_text[:50]}'"
        elif not desc:
            desc = f"Click element at {selector}"
            
        self._add_step(
            action="click",
            target=selector,
            description=desc
        )
    
    def record_fill(self, selector: str, value: str, field_name: str = "", description: str = ""):
        """Record a form fill action"""
        desc = description
        if not desc and field_name:
            desc = f"Fill '{field_name}' with '{value[:50]}'"
        elif not desc:
            desc = f"Fill input at {selector} with '{value[:50]}'"
            
        self._add_step(
            action="fill",
            target=selector,
            value=value,
            description=desc
        )
    
    def record_scroll(self, direction: str = "down", amount: str = "", description: str = ""):
        """Record a scroll action"""
        desc = description or f"Scroll {direction}" + (f" by {amount}" if amount else "")
        self._add_step(
            action="scroll",
            target=direction,
            value=amount,
            description=desc
        )
    
    def record_wait(self, duration: float, reason: str = "", description: str = ""):
        """Record a wait/pause action"""
        desc = description or f"Wait {duration}s" + (f" for {reason}" if reason else "")
        self._add_step(
            action="wait",
            value=str(duration),
            description=desc
        )
    
    def record_viewport_change(self, new_viewport: str, description: str = ""):
        """Record a viewport/resize action"""
        self.current_viewport = new_viewport
        desc = description or f"Change viewport to {new_viewport}"
        self._add_step(
            action="resize",
            target=new_viewport,
            description=desc
        )
    
    def record_keyboard(self, key: str, selector: str = "", description: str = ""):
        """Record a keyboard action"""
        desc = description or f"Press {key}" + (f" on {selector}" if selector else "")
        self._add_step(
            action="keyboard",
            target=selector,
            value=key,
            description=desc
        )
    
    def record_hover(self, selector: str, element_text: str = "", description: str = ""):
        """Record a hover action"""
        desc = description
        if not desc and element_text:
            desc = f"Hover over '{element_text[:50]}'"
        elif not desc:
            desc = f"Hover over element at {selector}"
            
        self._add_step(
            action="hover",
            target=selector,
            description=desc
        )
    
    def record_custom_action(self, action: str, target: str = "", value: str = "", description: str = ""):
        """Record a custom action not covered by other methods"""
        self._add_step(
            action=action,
            target=target,
            value=value,
            description=description or f"Perform {action}"
        )
    
    def _add_step(self, action: str, target: str = "", value: str = "", description: str = ""):
        """Internal method to add a step to the recording"""
        self.step_counter += 1
        step = ReproStep(
            step_number=self.step_counter,
            action=action,
            target=target or None,
            value=value or None,
            description=description,
            timestamp=time.time(),
            viewport=self.current_viewport
        )
        self.steps.append(step)
    
    def get_steps(self) -> List[ReproStep]:
        """Get all recorded steps"""
        return self.steps.copy()
    
    def get_steps_since(self, step_number: int) -> List[ReproStep]:
        """Get steps recorded since a specific step number"""
        return [step for step in self.steps if step.step_number > step_number]
    
    def clear_steps(self):
        """Clear all recorded steps (useful for starting a new test scenario)"""
        self.steps.clear()
        self.step_counter = 0
    
    def get_last_step_number(self) -> int:
        """Get the number of the last recorded step"""
        return self.step_counter
    
    def format_steps_for_human(self) -> str:
        """Format steps as human-readable text for developers"""
        if not self.steps:
            return "No reproduction steps recorded."
        
        formatted = [f"Reproduction Steps for {self.page_url}:\n"]
        
        for step in self.steps:
            step_text = f"{step.step_number}. {step.description}"
            if step.viewport:
                step_text += f" (viewport: {step.viewport})"
            formatted.append(step_text)
        
        return "\n".join(formatted)
    
    def format_steps_for_automation(self) -> List[dict]:
        """Format steps as structured data for automation tools"""
        return [
            {
                "step": step.step_number,
                "action": step.action,
                "target": step.target,
                "value": step.value,
                "description": step.description,
                "viewport": step.viewport
            }
            for step in self.steps
        ]
