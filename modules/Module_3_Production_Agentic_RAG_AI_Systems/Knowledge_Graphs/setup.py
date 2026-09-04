"""
Setup Script - Initialize RAG and Knowledge Graph System
=========================================================

Run this script ONCE before using the Streamlit app to:
1. Connect to Neo4j
2. Load the dataset
3. Create embeddings
4. Verify everything works

Learn more: https://maven.com/boring-bot/advanced-llm?promoCode=200OFF
"""

import os
from dotenv import load_dotenv
from knowledge_graph_rag_comparison import Neo4jGraphRAG
import sys

def print_banner():
    """Print a nice banner."""
    print("\n" + "=" * 80)
    print("RAG vs Knowledge Graph - System Setup")
    print("=" * 80)
    print("\n🎓 Learn more about building multi-agent systems:")
    print("   https://maven.com/boring-bot/advanced-llm?promoCode=200OFF")
    print("\n" + "=" * 80 + "\n")


def check_environment():
    """Check if environment variables are set."""
    print("📋 Step 1: Checking environment variables...")

    load_dotenv()

    required_vars = {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }

    missing = [key for key, value in required_vars.items() if not value]

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("\n📝 Please update your .env file with the required credentials:")
        print("   - NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io")
        print("   - NEO4J_USERNAME=neo4j")
        print("   - NEO4J_PASSWORD=your-password")
        print("   - OPENAI_API_KEY=sk-...")
        return False

    print("✅ All environment variables are set!\n")
    return True


def test_connection():
    """Test Neo4j connection."""
    print("🔌 Step 2: Testing Neo4j connection...")

    try:
        rag = Neo4jGraphRAG()
        # Try a simple query
        result = rag.execute_query("RETURN 1 as test")
        rag.close()
        print("✅ Successfully connected to Neo4j!\n")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check your Neo4j instance is running")
        print("   2. Verify your NEO4J_URI starts with 'neo4j+s://'")
        print("   3. Confirm your username and password are correct")
        print("   4. Make sure your IP is whitelisted in Neo4j Aura")
        return False


def load_dataset():
    """Load the dataset into Neo4j."""
    print("📥 Step 3: Loading dataset into Neo4j...")

    try:
        rag = Neo4jGraphRAG()

        # Check if data already exists
        count = rag.execute_query("MATCH (n) RETURN count(n) as count")

        if count[0]['count'] > 0:
            print(f"ℹ️  Found {count[0]['count']} existing nodes in database")
            response = input("   Do you want to reload the data? (y/N): ").strip().lower()

            if response == 'y':
                print("   Clearing existing data...")
                rag.execute_query("MATCH (n) DETACH DELETE n")
                print("   ✅ Data cleared!")
            else:
                print("   ℹ️  Skipping data load - using existing data\n")
                rag.close()
                return True

        # Load the data
        csv_url = 'https://raw.githubusercontent.com/dcarpintero/generative-ai-101/main/dataset/synthetic_articles.csv'
        print(f"   Loading from: {csv_url}")

        rag.load_data(csv_url)

        # Verify data was loaded
        count = rag.execute_query("MATCH (n) RETURN count(n) as count")
        article_count = rag.execute_query("MATCH (a:Article) RETURN count(a) as count")
        researcher_count = rag.execute_query("MATCH (r:Researcher) RETURN count(r) as count")

        print(f"✅ Dataset loaded successfully!")
        print(f"   - Total nodes: {count[0]['count']}")
        print(f"   - Articles: {article_count[0]['count']}")
        print(f"   - Researchers: {researcher_count[0]['count']}\n")

        rag.close()
        return True

    except Exception as e:
        print(f"❌ Failed to load dataset: {str(e)}")
        return False


def create_embeddings():
    """Create embeddings for articles."""
    print("🔢 Step 4: Creating embeddings for articles...")
    print("   (This may take 2-3 minutes...)\n")

    try:
        rag = Neo4jGraphRAG()

        # Check if embeddings already exist
        emb_count = rag.execute_query(
            "MATCH (a:Article) WHERE a.embedding IS NOT NULL RETURN count(a) as count"
        )

        if emb_count[0]['count'] > 0:
            print(f"ℹ️  Found {emb_count[0]['count']} articles with existing embeddings")
            response = input("   Do you want to recreate embeddings? (y/N): ").strip().lower()

            if response != 'y':
                print("   ℹ️  Skipping embedding creation - using existing embeddings\n")
                rag.close()
                return True

        # Create embeddings
        rag.create_embeddings_for_articles()

        print("✅ Embeddings created successfully!\n")

        rag.close()
        return True

    except Exception as e:
        print(f"❌ Failed to create embeddings: {str(e)}")
        print("\n💡 This might be an OpenAI API issue:")
        print("   1. Check your OPENAI_API_KEY is valid")
        print("   2. Verify you have credits in your OpenAI account")
        print("   3. Check your API key hasn't been revoked")
        return False


def test_queries():
    """Test that queries work."""
    print("🧪 Step 5: Testing queries...")

    try:
        rag = Neo4jGraphRAG()

        # Test RAG query
        print("   Testing RAG query...")
        rag_result = rag.query("Who are the collaborators of Emily Chen?", use_vector_search=False)

        if rag_result['answer'] and "couldn't find" not in rag_result['answer'].lower():
            print("   ✅ RAG query working!")
        else:
            print("   ⚠️  RAG query returned no results (this might be normal)")

        # Test Knowledge Graph query
        print("   Testing Knowledge Graph query...")
        kg_result = rag.kg_query_with_explanation("How many researchers are there?")

        if kg_result['success']:
            print("   ✅ Knowledge Graph query working!")
        else:
            print(f"   ❌ Knowledge Graph query failed: {kg_result.get('error')}")
            rag.close()
            return False

        print("\n✅ All queries working!\n")

        rag.close()
        return True

    except Exception as e:
        print(f"❌ Query test failed: {str(e)}")
        return False


def main():
    """Main setup process."""
    print_banner()

    steps = [
        ("Environment Check", check_environment),
        ("Connection Test", test_connection),
        ("Dataset Loading", load_dataset),
        ("Embedding Creation", create_embeddings),
        ("Query Testing", test_queries)
    ]

    for step_name, step_func in steps:
        if not step_func():
            print("\n" + "=" * 80)
            print(f"❌ Setup failed at: {step_name}")
            print("=" * 80)
            print("\nPlease fix the issues above and run setup again:")
            print("   python setup.py")
            return False

    # Success!
    print("\n" + "🎉" * 40)
    print("\n✅ Setup completed successfully!")
    print("\n🚀 You can now run the Streamlit app:")
    print("\n   streamlit run app.py")
    print("\n   OR")
    print("\n   ./run_app.sh")
    print("\n" + "🎉" * 40)
    print("\n🎓 Ready to learn more? Check out our course:")
    print("   https://maven.com/boring-bot/advanced-llm?promoCode=200OFF")
    print("   Use code 200OFF for $200 off!")
    print("\n" + "=" * 80 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
