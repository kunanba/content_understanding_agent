"""
Content Understanding Agent using Microsoft Agent Framework.
This agent orchestrates document processing workflows using Azure Functions.
"""
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet
from azure.identity import DefaultAzureCredential
import function_tools
import validation_tools


class ContentUnderstandingAgent:
    """
    AI Agent that orchestrates document processing workflows.
    
    Uses Microsoft Agent Framework (azure-ai-projects SDK) to:
    1. Perform OCR on documents
    2. Parse and validate OCR results
    3. Create Excel reports
    4. Clean up processed files
    """
    
    def __init__(self, agent_name: str = "content-understanding-agent"):
        """Initialize the agent with Azure AI Foundry project connection."""
        load_dotenv()
        
        self.agent_name = agent_name
        self.project_endpoint = os.getenv("PROJECT_ENDPOINT")
        self.model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")
        
        if not self.project_endpoint:
            raise ValueError("PROJECT_ENDPOINT environment variable is required")
        
        # Create project client
        self.project_client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=DefaultAzureCredential()
        )
        
        # Define the functions that the agent can use
        user_functions = {
            function_tools.perform_ocr,
            function_tools.parse_ocr,
            function_tools.create_excel,
            function_tools.clean_up,
            validation_tools.get_ocr_result_content,
            validation_tools.get_parsed_summary_content,
            validation_tools.validate_ocr_and_parse
        }
        
        # Create toolset with function tools
        functions = FunctionTool(functions=user_functions)
        toolset = ToolSet()
        toolset.add(functions)
        
        # Enable automatic function calls
        self.project_client.agents.enable_auto_function_calls(toolset)
        
        # Try to find existing agent by name
        self.agent = self._find_or_create_agent(toolset)
        
        print(f"✅ Using agent: {self.agent.id} (name: {self.agent_name})")
    
    def _find_or_create_agent(self, toolset: ToolSet):
        """Find existing agent by name or create new one."""
        # List all agents
        try:
            agents = self.project_client.agents.list_agents()
            
            # Look for agent with matching name
            for agent in agents:
                if agent.name == self.agent_name:
                    print(f"♻️ Found existing agent: {agent.id}")
                    return agent
        except Exception as e:
            print(f"⚠️ Could not list agents: {e}")
        
        # Create new agent if not found
        print(f"🆕 Creating new agent: {self.agent_name}")
        return self.project_client.agents.create_agent(
            model=self.model_deployment,
            name=self.agent_name,
            instructions="""You are a document processing agent that orchestrates workflows using Azure Functions.

Your workflow for processing documents:
1. Call perform_ocr with the document filename to extract text and data
2. Call parse_ocr with the OCR result blob name to create a summary
3. VALIDATE DATA: Use validate_ocr_and_parse to compare the OCR result with the parsed summary
   - This downloads both files and checks that the summary contains data from the OCR
   - Reports any issues like missing data or empty summaries
   - Provides specific validation checks and recommendations
4. If validation passes, call create_excel with the OCR result blob name
5. After successful Excel creation, call clean_up with the original document filename

For data validation:
- ALWAYS use validate_ocr_and_parse after parse_ocr completes
- Pass both the OCR result blob name (from step 1) and summary blob name (from step 2)
- Review the validation checks and issues reported
- Only proceed to Excel creation if validation passes
- If validation fails, report the issues and do not proceed to cleanup

You also have access to:
- get_ocr_result_content: Download and inspect OCR JSON content
- get_parsed_summary_content: Download and inspect parsed summary text

Always provide clear status updates about each step and handle errors gracefully.
If any step fails, do not proceed to cleanup.

When answering questions about processed documents:
- Use the function results to answer questions about patient information, expenses, dates, etc.
- Provide specific details from the OCR results when available""",
            toolset=toolset
        )
    
    def process_document(self, document_filename: str, classifier_id: str = "prebuilt-layout") -> dict:
        """
        Process a document through the complete workflow.
        
        Args:
            document_filename: Name of the document in incoming-docs container
            classifier_id: Azure Content Understanding classifier to use
            
        Returns:
            Dictionary with workflow results
        """
        # Create a thread for this conversation
        thread = self.project_client.agents.threads.create()
        print(f"📝 Created thread: {thread.id}")
        
        # Send the processing request
        prompt = f"""Please process the document '{document_filename}' using classifier '{classifier_id}'.
        
Follow the complete workflow:
1. Perform OCR
2. Parse the OCR results
3. Validate the data
4. Create Excel report
5. Clean up the original file

Provide status updates for each step and the final results."""
        
        message = self.project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        # Run the agent
        print("🤖 Starting agent run...")
        run = self.project_client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=self.agent.id
        )
        
        print(f"✅ Run completed with status: {run.status}")
        
        if run.status == "failed":
            print(f"❌ Run failed: {run.last_error}")
            return {"success": False, "error": run.last_error}
        
        # Get all messages from the thread
        messages = self.project_client.agents.messages.list(thread_id=thread.id)
        
        # Extract the agent's responses
        responses = []
        for msg in messages:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text') and content.text:
                        responses.append(content.text.value)
        
        return {
            "success": True,
            "thread_id": thread.id,
            "responses": responses
        }
    
    def query(self, question: str, thread_id: str = None) -> str:
        """
        Ask a natural language question about processed documents.
        
        Args:
            question: The question to ask
            thread_id: Optional thread ID to continue a conversation
            
        Returns:
            The agent's response
        """
        # Create new thread if not provided
        if not thread_id:
            thread = self.project_client.agents.threads.create()
            thread_id = thread.id
        
        # Send the question
        self.project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=question
        )
        
        # Run the agent
        run = self.project_client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=self.agent.id
        )
        
        if run.status == "failed":
            return f"Error: {run.last_error}"
        
        # Get the latest assistant message
        messages = self.project_client.agents.messages.list(thread_id=thread_id)
        for msg in messages:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text') and content.text:
                        return content.text.value
        
        return "No response generated"
    
    def delete_agent(self):
        """Delete the agent permanently. Use with caution - normally not needed."""
        if self.agent:
            self.project_client.agents.delete_agent(self.agent.id)
            print(f"🗑️ Deleted agent: {self.agent.id}")
            self.agent = None


if __name__ == "__main__":
    # Example usage
    agent = ContentUnderstandingAgent()
    
    # Process a document
    result = agent.process_document("claims_sample2.png")
    
    if result["success"]:
        print("\n📊 Workflow Results:")
        for response in result["responses"]:
            print(response)
            print("-" * 80)
    
    # Note: Agent persists for reuse. Only delete if you want to remove it permanently.
    # agent.delete_agent()
