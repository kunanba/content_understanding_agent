"""
Test script for the Content Understanding Agent.
This will test the complete workflow with an existing document.
"""
import os
from agent import ContentUnderstandingAgent


def test_agent_workflow():
    """Test the complete document processing workflow."""
    print("=" * 80)
    print("Testing Content Understanding Agent")
    print("=" * 80)
    
    try:
        # Initialize the agent
        print("\n1️⃣ Initializing agent...")
        agent = ContentUnderstandingAgent()
        
        # Test with an existing document
        document_name = "claims_sample3.jpg"
        print(f"\n2️⃣ Processing document: {document_name}")
        print("-" * 80)
        
        result = agent.process_document(document_name)
        
        if result["success"]:
            print("\n✅ Workflow completed successfully!")
            print("\n📊 Agent Responses:")
            print("=" * 80)
            for i, response in enumerate(result["responses"], 1):
                print(f"\nResponse {i}:")
                print(response)
                print("-" * 80)
            
            # Test querying capability
            print("\n3️⃣ Testing query capability...")
            thread_id = result["thread_id"]
            
            test_questions = [
                "What was the result of the OCR processing?",
                "Were all workflow steps completed successfully?"
            ]
            
            for question in test_questions:
                print(f"\n❓ Question: {question}")
                answer = agent.query(question, thread_id)
                print(f"💬 Answer: {answer}")
                print("-" * 80)
        else:
            print(f"\n❌ Workflow failed: {result.get('error', 'Unknown error')}")
        
        # Note: Agent persists for reuse across sessions
        print("\n✅ Done! Agent remains active for future use.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_agent_workflow()
