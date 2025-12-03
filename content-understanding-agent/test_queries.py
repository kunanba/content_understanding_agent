"""
Test natural language queries about document data.
"""
from agent import ContentUnderstandingAgent


def test_natural_language_queries():
    """Test querying the agent about document details."""
    print("=" * 80)
    print("Testing Natural Language Queries")
    print("=" * 80)
    
    try:
        # Initialize the agent
        print("\n1️⃣ Initializing agent...")
        agent = ContentUnderstandingAgent()
        
        # Process a fresh document
        document_name = "claims_sample2.png"
        print(f"\n2️⃣ Processing document: {document_name}")
        print("-" * 80)
        
        result = agent.process_document(document_name)
        
        if not result["success"]:
            print(f"\n❌ Failed to process document: {result.get('error')}")
            return
        
        print("\n✅ Document processed successfully!")
        thread_id = result["thread_id"]
        
        # Ask natural language questions about the data
        print("\n3️⃣ Asking questions about the document data...")
        print("=" * 80)
        
        questions = [
            "What personal details can you find in this document? Include names, addresses, phone numbers, etc.",
            "Are there any dates mentioned in the document?",
            "What is this document about? What type of form is it?",
            "Can you extract all the plaintiff information from the form?",
            "What are the defendant details if any are provided?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ Question {i}: {question}")
            print("-" * 80)
            answer = agent.query(question, thread_id)
            print(f"💬 Answer:\n{answer}")
            print("-" * 80)
        
        # Cleanup
        print("\n4️⃣ Cleaning up agent...")
        agent.cleanup()
        print("✅ Done!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_natural_language_queries()
