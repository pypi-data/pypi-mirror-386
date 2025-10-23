from typing import Any, Dict, List, Optional, Type, Union
import httpx
import json
import asyncio
from pydantic import BaseModel, ValidationError

from robora.CONFIG import PERPLEXITY_API_KEY

from collections import namedtuple
from robora.classes import QueryHandler, QueryResponse

class SonarQueryHandler(QueryHandler):
    response_model: Type[BaseModel]
    model: str = "sonar"
    max_retries: int = 3
    def __init__(self, response_model: Type[BaseModel], model: str = "sonar", max_retries: int = 3, ):
        self.response_model = response_model
        self.model = model
        self.max_retries = max_retries
    
    def _format_pretty_citations(self, enriched_citations: List[Dict[str, Any]]) -> str:
        """Format enriched citations into a human-readable string."""
        if not enriched_citations:
            return "No citations available."
        
        formatted_parts = []
        for i, citation in enumerate(enriched_citations, 1):
            parts = [f"[{i}]"]
            
            # Add title if available
            if citation.get('title'):
                parts.append(citation['title'])
            
            # Add URL
            parts.append(f"({citation['url']})")
            
            # Add date information if available
            if citation.get('date'):
                parts.append(f"- Published: {citation['date']}")
            elif citation.get('last_updated'):
                parts.append(f"- Updated: {citation['last_updated']}")
            
            # Add snippet if available
            if citation.get('snippet'):
                snippet = citation['snippet']
                # Truncate snippet if too long
                if len(snippet) > 150:
                    snippet = snippet[:147] + "..."
                parts.append(f"\n    {snippet}")
            
            formatted_parts.append(" ".join(parts))
        
        return "\n\n".join(formatted_parts)
    
    async def query(self, prompt:str) -> QueryResponse:
        schema = self.response_model.model_json_schema()
        enhanced_prompt = f"""{prompt}\n\nAnswer schema:\n{json.dumps(schema, indent=2)}"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json = {
                        'model': self.model,
                        'messages': [
                            {
                                'role': 'user',
                                'content': enhanced_prompt
                            }
                        ],
                        'response_format': {
                            'type': 'json_schema',
                            'json_schema': {
                                'schema': schema
                            }
                        }
                    }
                )
                response.raise_for_status()
                if not response.content:
                    raise ValueError("Empty response from API")
                full_response = response.json()
                return QueryResponse(full_response=full_response, error=None)
        except Exception as e:
            return QueryResponse(full_response=None, error=str(e))
    
    def extract_fields(self, full_response: Dict[str,Any]) -> dict[str,Any]:

        content_raw = full_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not content_raw:
            raise ValueError("Empty content in API response")
        content_dict = json.loads(content_raw)
        content = self.response_model.model_validate(content_dict)

        # Enrich with citations
        enriched_citations = []
        assert(type(full_response) == dict)
        citations = full_response.get('citations', [])
        search_results = full_response.get('search_results', [])
        search_lookup = {result.get('url', ''): result for result in search_results}
        for citation_url in citations:
            enriched_citation = {
                'url': citation_url,
                'title': None,
                'snippet': None,
                'date': None,
                'last_updated': None,
                'matched': False
            }
            if citation_url in search_lookup:
                search_result = search_lookup[citation_url]
                enriched_citation.update({
                    'title': search_result.get('title'),
                    'snippet': search_result.get('snippet'),
                    'date': search_result.get('date'),
                    'last_updated': search_result.get('last_updated'),
                    'matched': True
                })
            enriched_citations.append(enriched_citation)

        # Format pretty citations
        pretty_citations = self._format_pretty_citations(enriched_citations)

        # 
        content_dict = content.model_dump()
        content_dict['enriched_citations'] = enriched_citations
        content_dict['pretty_citations'] = pretty_citations
        return content_dict
        
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(response_model={self.response_model.__name__}, "
            f"model='{self.model}', max_retries={self.max_retries})"
        )

    def __str__(self) -> str:
        return f"SonarQueryHandler for model '{self.model}' with max_retries={self.max_retries}"