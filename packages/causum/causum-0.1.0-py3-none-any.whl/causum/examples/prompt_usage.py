"""
Example of using Causum™ API with natural language prompts.

This demonstrates both:
1. Prompt with specific profile (targeted query generation)
2. Prompt without profile (intelligent routing across databases)
"""
import os
from causum import UniversalClient

# Set API key
# os.environ['CAUSALPY_API_KEY'] = 'your-api-key-here'


def main():
    """Main example function."""
    
    # Initialize client
    client = UniversalClient(
        profiles="./profiles.json",
        governance_url="http://localhost:5000/metadata",
        enable_cache=True,
        fail_open=True
    )
    
    print("="*70)
    print("Causum™ API Prompt-Based Query Examples")
    print("="*70)
    
    # ========================================================================
    # Example 1: Prompt with specific profile (targeted query generation)
    # ========================================================================
    print("\n" + "="*70)
    print("Example 1: Prompt WITH Profile (Targeted Query Generation)")
    print("="*70)
    print("\nUse Case: You know which database to query, want LLM to generate SQL")
    
    result = client.execute_prompt(
        profile="postgres_admin",
        prompt="How many patients are in the database?",
        max_rows=1
    )
    
    print(f"\n📝 Prompt: 'How many patients are in the database?'")
    print(f"🗄️  Profile: postgres_admin")
    print(f"📊 Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"🔧 Generated Query: {result.get('generated_query')}")
        print(f"📈 Result: {result.get('data')}")
        print(f"⏱️  Execution Time: {result['metadata'].get('execution_time_ms')}ms")
    else:
        print(f"❌ Error: {result['error']}")
    
    # ========================================================================
    # Example 2: Another targeted query
    # ========================================================================
    print("\n" + "-"*70)
    
    result = client.execute_prompt(
        profile="mongodb_ed",
        prompt="Show me emergency department visits where disposition was 'admitted'",
        max_rows=5
    )
    
    print(f"\n📝 Prompt: 'Show me ED visits where disposition was admitted'")
    print(f"🗄️  Profile: mongodb_ed")
    print(f"📊 Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"🔧 Generated Query: {result.get('generated_query')}")
        print(f"📈 Results: {len(result.get('data', []))} documents")
    else:
        print(f"❌ Error: {result['error']}")
    
    # ========================================================================
    # Example 3: Prompt WITHOUT profile (intelligent routing)
    # ========================================================================
    print("\n" + "="*70)
    print("Example 2: Prompt WITHOUT Profile (Intelligent Routing)")
    print("="*70)
    print("\nUse Case: Ask a question, let the system figure out which DB(s) to query")
    
    result = client.execute_prompt(
        prompt="What were the most common diagnoses for patients admitted in 2020?",
        max_rows=10
    )
    
    print(f"\n📝 Prompt: 'What were the most common diagnoses for patients admitted in 2020?'")
    print(f"🗄️  Profile: AUTO-DETECT")
    print(f"📊 Status: {result['status']}")
    
    if result['status'] == 'success':
        execution_plan = result.get('execution_plan', [])
        print(f"\n🧠 Execution Plan ({len(execution_plan)} queries):")
        
        for i, plan_item in enumerate(execution_plan, 1):
            print(f"\n  Query {i}:")
            print(f"    Profile: {plan_item['profile']}")
            print(f"    Query: {plan_item['query']}")
        
        print(f"\n📈 Results from {len(result.get('results', []))} database(s):")
        for i, res in enumerate(result.get('results', []), 1):
            print(f"\n  Result {i} ({res['profile']}):")
            print(f"    Rows: {len(res['result'].get('data', []))}")
            print(f"    Status: {res['result']['status']}")
        
        # If API provides synthesized answer
        if result.get('synthesized_answer'):
            print(f"\n💡 Synthesized Answer:")
            print(f"   {result['synthesized_answer']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # ========================================================================
    # Example 4: Complex cross-database question
    # ========================================================================
    print("\n" + "-"*70)
    
    result = client.execute_prompt(
        prompt="Compare ICU length of stay between patients in TimescaleDB "
               "with their ED disposition from MongoDB"
    )
    
    print(f"\n📝 Prompt: Cross-database analysis (TimescaleDB + MongoDB)")
    print(f"📊 Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"\n🧠 Databases queried: {len(result.get('results', []))}")
        for res in result.get('results', []):
            print(f"  - {res['profile']}: {res['result']['status']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # ========================================================================
    # Example 5: Prompt with user context
    # ========================================================================
    print("\n" + "="*70)
    print("Example 3: Prompt with User Context (for Governance)")
    print("="*70)
    
    result = client.execute_prompt(
        profile="mysql_clinical",
        prompt="What is the average age of patients?",
        user_context={
            "session_id": "rag-session-12345",
            "user_id": "doctor-smith",
            "app_name": "clinical-rag-assistant",
            "use_case": "patient_demographics"
        }
    )
    
    print(f"\n📝 Prompt: 'What is the average age of patients?'")
    print(f"🗄️  Profile: mysql_clinical")
    print(f"📊 Status: {result['status']}")
    print(f"👤 User Context: Tracked for governance")
    
    if result['status'] == 'success':
        print(f"🔧 Generated Query: {result.get('generated_query')}")
        print(f"📈 Result: {result.get('data')}")
    
    print("\n" + "="*70)
    print("✓ All examples completed")
    print("="*70)
    
    # Clean up
    client.close()


def comparison_table():
    """Print comparison of query methods."""
    print("\n" + "="*70)
    print("Query Method Comparison")
    print("="*70)
    
    print("""
┌─────────────────────────┬──────────────────────┬─────────────────────┐
│ Method                  │ Use Case             │ What You Provide    │
├─────────────────────────┼──────────────────────┼─────────────────────┤
│ execute(query, profile) │ You write SQL/query  │ Exact query + DB    │
│                         │ You know the DB      │                     │
├─────────────────────────┼──────────────────────┼─────────────────────┤
│ execute_prompt(prompt,  │ LLM writes query     │ Question + DB       │
│                profile) │ You pick the DB      │                     │
├─────────────────────────┼──────────────────────┼─────────────────────┤
│ execute_prompt(prompt)  │ LLM picks DB(s)      │ Just the question   │
│                         │ LLM writes queries   │                     │
│                         │ Cross-DB possible    │                     │
└─────────────────────────┴──────────────────────┴─────────────────────┘
    """)


if __name__ == "__main__":
    comparison_table()
    print("\n")
    main()