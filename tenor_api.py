#!/usr/bin/env python3
"""
Tenor API Handler for GIF Bot
Handles all Tenor API interactions with error handling and rate limiting
"""

import os
import aiohttp
import asyncio
from typing import List, Optional
from urllib.parse import quote
from rich.console import Console

console = Console()

class TenorAPI:
    """Async Tenor API handler with comprehensive features"""
    
    def __init__(self):
        self.api_key = os.getenv("TENOR_API_KEY")
        self.base_url = "https://tenor.googleapis.com/v2"
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make async request to Tenor API with error handling"""
        if not self.api_key:
            console.print("[red]❌ TENOR_API_KEY not found![/red]")
            return None
        
        params['key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        try:
            session = await self._get_session()
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    console.print(f"[green]✅ Tenor API: {endpoint} - {response.status}[/green]")
                    return data
                else:
                    console.print(f"[red]❌ Tenor API Error: {response.status}[/red]")
                    return None
        
        except asyncio.TimeoutError:
            console.print("[red]❌ Tenor API: Request timeout[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Tenor API Error: {e}[/red]")
            return None
    
    async def search_gif(self, query: str, limit: int = 1, safe_search: bool = True) -> List[str]:
        """
        Search for GIFs using Tenor API
        
        Args:
            query: Search query string
            limit: Number of results (max 50)
            safe_search: Enable content filtering
        
        Returns:
            List of GIF URLs
        """
        if not query.strip():
            return []
        
        params = {
            'q': quote(query),
            'limit': min(limit, 50),
            'media_filter': 'gif',
            'contentfilter': 'high' if safe_search else 'off'
        }
        
        data = await self._make_request('search', params)
        
        if not data or 'results' not in data:
            return []
        
        gifs = []
        for item in data['results']:
            try:
                # Try to get the best quality GIF URL
                gif_formats = item.get('media_formats', {})
                if 'gif' in gif_formats:
                    gif_url = gif_formats['gif']['url']
                elif 'tinygif' in gif_formats:
                    gif_url = gif_formats['tinygif']['url']
                else:
                    continue
                
                gifs.append(gif_url)
            except (KeyError, TypeError):
                continue
        
        console.print(f"[blue]🔍 Found {len(gifs)} GIFs for '{query}'[/blue]")
        return gifs
    
    async def get_trending(self, limit: int = 10) -> List[str]:
        """
        Get trending GIFs from Tenor
        
        Args:
            limit: Number of trending GIFs to fetch
        
        Returns:
            List of trending GIF URLs
        """
        params = {
            'limit': min(limit, 50),
            'media_filter': 'gif'
        }
        
        data = await self._make_request('trending', params)
        
        if not data or 'results' not in data:
            return []
        
        gifs = []
        for item in data['results']:
            try:
                gif_formats = item.get('media_formats', {})
                if 'gif' in gif_formats:
                    gif_url = gif_formats['gif']['url']
                elif 'tinygif' in gif_formats:
                    gif_url = gif_formats['tinygif']['url']
                else:
                    continue
                
                gifs.append(gif_url)
            except (KeyError, TypeError):
                continue
        
        console.print(f"[blue]🔥 Found {len(gifs)} trending GIFs[/blue]")
        return gifs
    
    async def get_random_gif(self, query: str = "random") -> Optional[str]:
        """
        Get a random GIF
        
        Args:
            query: Search query for random selection
        
        Returns:
            Random GIF URL or None
        """
        gifs = await self.search_gif(query, limit=20)
        if not gifs:
            return None
        
        import random
        return random.choice(gifs)
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
