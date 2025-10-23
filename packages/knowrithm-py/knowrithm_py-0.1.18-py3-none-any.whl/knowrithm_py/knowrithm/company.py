



from typing import Dict, List, Optional

from knowrithm_py.knowrithm.agent import KnowrithmAgent
from knowrithm_py.knowrithm.client import KnowrithmClient


class KnowrithmCompany:
    """High-level interface for company operations"""
    
    def __init__(self, client: KnowrithmClient, company_id: str):
        self.client = client
        self.company_id = company_id
        self._details = None
    
    def create_agent(self, name: str, description: Optional[str] = None, **kwargs) -> KnowrithmAgent:
        """Create a new agent for this company"""
        agent_data = {
            "name": name,
            "company_id": self.company_id,
            **kwargs
        }
        if description:
            agent_data["description"] = description
        
        agent = self.client.agents.create(agent_data)
        return KnowrithmAgent(self.client, agent["id"])
    
    def list_agents(self) -> List[Dict]:
        """List all agents for this company"""
        return self.client.agents.list(company_id=self.company_id)
    
    def get_details(self, force_refresh: bool = False) -> Dict:
        """Get company details with caching"""
        if not self._details or force_refresh:
            self._details = self.client.companies.get(self.company_id)
        return self._details
    
    def get_statistics(self) -> Dict:
        """Get company statistics"""
        return self.client.companies.get_statistics(self.company_id)
    
    def create_lead(self, first_name: str, last_name: str, email: str, **kwargs) -> Dict:
        """Create a lead for this company"""
        lead_data = {
            "company_id": self.company_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            **kwargs
        }
        return self.client.leads.create(lead_data)
    
    def list_leads(self, status: Optional[str] = None) -> List[Dict]:
        """List company leads"""
        return self.client.leads.list(company_id=self.company_id, status=status)
    
    def get_analytics(self) -> Dict:
        """Get company analytics dashboard"""
        return self.client.analytics.get_dashboard(company_id=self.company_id)

