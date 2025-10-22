"""
Julia Browser Tools for Agno Agent
Wrapper around julia_browser AgentSDK for web browsing capabilities
"""

import json
import sys
import os
from typing import Optional
from contextlib import redirect_stdout, redirect_stderr
from julia_browser import AgentSDK


class JuliaBrowserTools:
    """Julia Browser tools for web browsing, element interaction, and form submission"""
    
    def __init__(self):
        """Initialize the Julia Browser AgentSDK"""
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull), redirect_stderr(devnull):
                self.browser = AgentSDK()
        self.current_url = None
    
    def open_website(self, url: str) -> str:
        """
        Open a website and return its title and basic information.
        
        Args:
            url (str): The URL to open (e.g., "https://example.com")
        
        Returns:
            str: JSON string containing the page title and URL
        """
        try:
            result = self.browser.open_website(url)
            self.current_url = url
            return json.dumps({
                "success": True,
                "url": url,
                "title": result.get('title', 'No title'),
                "message": f"Successfully opened: {result.get('title', url)}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to open website: {str(e)}"
            })
    
    def list_elements(self) -> str:
        """
        List all interactive elements on the current page.
        
        Returns:
            str: JSON string containing information about clickable elements, inputs, and buttons
        """
        try:
            elements = self.browser.list_elements()
            return json.dumps({
                "success": True,
                "total_clickable": elements.get('total_clickable', 0),
                "elements": elements,
                "message": f"Found {elements.get('total_clickable', 0)} interactive elements"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to list elements: {str(e)}"
            })
    
    def type_text(self, element_id: int, text: str) -> str:
        """
        Type text into an input field.
        
        Args:
            element_id (int): The ID of the input element
            text (str): The text to type into the field
        
        Returns:
            str: JSON string confirming the action
        """
        try:
            self.browser.type_text(element_id, text)
            return json.dumps({
                "success": True,
                "message": f"Typed '{text}' into element {element_id}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to type text: {str(e)}"
            })
    
    def click_element(self, element_id: int) -> str:
        """
        Click a button or link on the page.
        
        Args:
            element_id (int): The ID of the element to click
        
        Returns:
            str: JSON string confirming the action
        """
        try:
            self.browser.click_element(element_id)
            return json.dumps({
                "success": True,
                "message": f"Clicked element {element_id}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to click element: {str(e)}"
            })
    
    def submit_form(self) -> str:
        """
        Submit the current form on the page.
        
        Returns:
            str: JSON string containing the result page title
        """
        try:
            result = self.browser.submit_form()
            return json.dumps({
                "success": True,
                "title": result.get('title', 'No title'),
                "message": f"Form submitted successfully: {result.get('title', 'Unknown page')}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to submit form: {str(e)}"
            })
    
    def get_page_info(self) -> str:
        """
        Get current page title, URL, and full content.
        
        Returns:
            str: JSON string containing page information
        """
        try:
            page_info = self.browser.get_page_info()
            return json.dumps({
                "success": True,
                "url": page_info.get('url', self.current_url),
                "title": page_info.get('title', 'No title'),
                "content": page_info.get('content', ''),
                "message": f"Page info retrieved for: {page_info.get('title', 'Unknown')}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to get page info: {str(e)}"
            })
    
    def search_page(self, term: str) -> str:
        """
        Search for text within the current page.
        
        Args:
            term (str): The search term to find on the page
        
        Returns:
            str: JSON string containing search results
        """
        try:
            results = self.browser.search_page(term)
            return json.dumps({
                "success": True,
                "term": term,
                "results": results,
                "message": f"Found search results for: {term}"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to search page: {str(e)}"
            })
    
    def follow_link(self, link_url: str) -> str:
        """
        Navigate to a link by its URL.
        
        Args:
            link_url (str): The URL of the link to follow
        
        Returns:
            str: JSON string confirming the navigation
        """
        try:
            result = self.browser.follow_link(link_url)
            return json.dumps({
                "success": True,
                "message": f"Followed link to {link_url}",
                "title": result.get('title', 'No title')
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to follow link: {str(e)}"
            })
    
    def scroll_down(self, chunks: int = 1) -> str:
        """
        Scroll down to see more content (like browser scrolling).
        
        Args:
            chunks (int): Number of chunks to scroll (default: 1)
        
        Returns:
            str: JSON string confirming the scroll action
        """
        try:
            result = self.browser.scroll_down(chunks)
            return json.dumps({
                "success": True,
                "chunks": chunks,
                "message": f"Scrolled down {chunks} chunk(s)",
                "scroll_info": result
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to scroll down: {str(e)}"
            })
    
    def scroll_up(self, chunks: int = 1) -> str:
        """
        Scroll up to see previous content.
        
        Args:
            chunks (int): Number of chunks to scroll (default: 1)
        
        Returns:
            str: JSON string confirming the scroll action
        """
        try:
            result = self.browser.scroll_up(chunks)
            return json.dumps({
                "success": True,
                "chunks": chunks,
                "message": f"Scrolled up {chunks} chunk(s)",
                "scroll_info": result
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to scroll up: {str(e)}"
            })
    
    def scroll_to_top(self) -> str:
        """
        Jump to the top of the page.
        
        Returns:
            str: JSON string confirming the action
        """
        try:
            result = self.browser.scroll_to_top()
            return json.dumps({
                "success": True,
                "message": "Scrolled to top of page",
                "scroll_info": result
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to scroll to top: {str(e)}"
            })
    
    def scroll_to_bottom(self) -> str:
        """
        Jump to the bottom of the page.
        
        Returns:
            str: JSON string confirming the action
        """
        try:
            result = self.browser.scroll_to_bottom()
            return json.dumps({
                "success": True,
                "message": "Scrolled to bottom of page",
                "scroll_info": result
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to scroll to bottom: {str(e)}"
            })
    
    def get_scroll_info(self) -> str:
        """
        Get current scroll position and progress.
        
        Returns:
            str: JSON string containing scroll position and page info
        """
        try:
            scroll_info = self.browser.get_scroll_info()
            return json.dumps({
                "success": True,
                "scroll_info": scroll_info,
                "message": "Retrieved scroll information"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Failed to get scroll info: {str(e)}"
            })


def get_julia_browser_tools():
    """
    Get all julia browser tools as a list of functions for the Agent.
    
    Core Website Functions:
    - open_website(url) - Open any website and get page content
    - list_elements() - List all clickable elements and input fields with numbers
    - get_page_info() - Get current page title, URL, and full content
    - search_page(term) - Search for text within the current page
    
    Human-like Interactions:
    - click_element(number) - Click buttons or links by their number
    - type_text(field_number, text) - Type text into input fields by number
    - submit_form() - Submit forms with typed data
    - follow_link(url) - Navigate to a specific URL
    
    Page Navigation & Scrolling:
    - scroll_down(chunks=1) - Scroll down to see more content
    - scroll_up(chunks=1) - Scroll up to see previous content
    - scroll_to_top() - Jump to the top of the page
    - scroll_to_bottom() - Jump to the bottom of the page
    - get_scroll_info() - Get current scroll position and progress
    
    Returns:
        list: List of tool functions
    """
    browser_tools = JuliaBrowserTools()
    
    return [
        browser_tools.open_website,
        browser_tools.list_elements,
        browser_tools.get_page_info,
        browser_tools.search_page,
        browser_tools.click_element,
        browser_tools.type_text,
        browser_tools.submit_form,
        browser_tools.follow_link,
        browser_tools.scroll_down,
        browser_tools.scroll_up,
        browser_tools.scroll_to_top,
        browser_tools.scroll_to_bottom,
        browser_tools.get_scroll_info
    ]
