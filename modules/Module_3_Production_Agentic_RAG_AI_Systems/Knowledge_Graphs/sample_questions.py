"""
Sample Questions for RAG vs Knowledge Graph Evaluation
=======================================================

This file contains curated question sets for evaluating RAG and Knowledge Graph
approaches across different question types.

Each category tests different capabilities:
- Relationship queries: Graph traversal and entity connections
- Counting/aggregation: Structured data operations
- Semantic queries: Natural language understanding
- Complex multi-hop: Multi-step reasoning
- And more...

Learn more about building advanced multi-agent systems:
https://maven.com/boring-bot/advanced-llm?promoCode=200OFF
"""

from knowledge_graph_rag_comparison import batch_judge_questions


# ============================================
# EVALUATION QUESTION SETS
# ============================================

# SET 1: RELATIONSHIP QUERIES (KG Expected to Excel)
relationship_questions = [
    "Who are the collaborators of Emily Chen?",
    "Which researchers have co-authored papers with David Johnson?",
    "Find all researchers who have worked with Sarah Lee",
    "Who has Michael Brown collaborated with?",
    "Which authors have published together on AI Ethics?",
]

# SET 2: COUNTING & AGGREGATION (KG Expected to Dominate)
counting_questions = [
    "How many articles has each researcher published?",
    "Which researcher has published the most papers?",
    "How many papers are there on each topic?",
    "Count the number of articles in AI Ethics",
    "Which topic has the most publications?",
    "How many researchers work on Foundations of Language Models?",
    "What is the total number of publications in 2023?",
]

# SET 3: FILTERING & SPECIFIC QUERIES (KG Expected to Win)
filtering_questions = [
    "Show me all articles published by Emily Chen",
    "What papers did Lisa Wang publish in 2024?",
    "Find articles about Model Optimization",
    "Which papers were published after January 2024?",
    "List all researchers working on Safety subtopic",
    "Show me articles on AI Ethics published in 2023",
]

# SET 4: TOPIC-BASED QUERIES (Mixed Results Expected)
topic_questions = [
    "What topics does Emily Chen research?",
    "Which researchers work on AI Ethics?",
    "What are the main research areas in the dataset?",
    "Who works on Model Architectures?",
    "Find all researchers interested in Social Impact",
    "What subtopics are covered under Foundations of Language Models?",
]

# SET 5: SEMANTIC/CONTENT QUERIES (RAG Expected to Excel)
semantic_questions = [
    "What are the main challenges in AI safety according to the research?",
    "Explain the innovations in transformer architectures",
    "What are the ethical concerns about AI development?",
    "Summarize the research on language model optimization",
    "What approaches are proposed for privacy in AI?",
    "How is AI being used to address climate change?",
    "What are the key insights about scaling laws in language models?",
]

# SET 6: COMPLEX MULTI-HOP QUERIES (KG Expected to Excel)
complex_questions = [
    "Which researchers work on the same topics as Emily Chen?",
    "Find researchers who collaborate with colleagues of David Johnson",
    "What topics connect Michael Brown and Sarah Lee?",
    "Which researchers published in both 2023 and 2024?",
    "Find articles that bridge multiple subtopics",
    "Who are the most connected researchers in the collaboration network?",
]

# SET 7: TEMPORAL QUERIES (KG Expected to Win)
temporal_questions = [
    "What research was published in the last quarter of 2023?",
    "Which topics were most popular in 2024?",
    "Show the research timeline for Emily Chen",
    "What was the first paper published on AI Ethics?",
    "Compare publication activity between 2023 and 2024",
]

# SET 8: COMPARISON QUERIES (Mixed Results Expected)
comparison_questions = [
    "Compare the research focus of Emily Chen vs Michael Brown",
    "Which topic has more researchers: AI Ethics or Language Models?",
    "Who is more prolific: David Johnson or Sarah Lee?",
    "Compare collaboration patterns between different research areas",
]

# ============================================
# CURATED EVALUATION SETS
# ============================================

# Quick Evaluation Set (10 questions - fast benchmark)
quick_eval_questions = [
    "Who are the collaborators of Emily Chen?",
    "How many articles has each researcher published?",
    "Show me all articles published by David Johnson",
    "Which researchers work on AI Ethics?",
    "What are the main challenges in AI safety?",
    "Which researchers work on the same topics as Emily Chen?",
    "What research was published in 2024?",
    "Compare the research focus of Emily Chen vs Michael Brown",
    "Which topic has the most publications?",
    "Explain the innovations in transformer architectures",
]

# Medium Evaluation Set (20 questions - balanced)
medium_eval_questions = (
    relationship_questions +
    counting_questions[:3] +
    topic_questions[:3] +
    semantic_questions[:3] +
    complex_questions[:3] +
    temporal_questions[:3]
)

# Strength/Weakness Diagnostic Set
strength_weakness_questions = [
    # KG Strengths
    "Who collaborated with whom on Model Optimization papers?",
    "How many co-authors does each researcher have?",
    "Find all papers published between June and December 2023",
    "Which researchers published exactly 2 papers?",

    # RAG Strengths
    "What are the key innovations proposed for transformer architectures?",
    "Summarize the ethical concerns discussed in AI research",
    "Explain the privacy-preserving techniques mentioned in the papers",
    "What solutions are proposed for AI bias mitigation?",

    # Edge Cases (where both might struggle)
    "What is the citation impact of each paper?",
    "Compare the technical depth of papers on Safety",
    "Predict future research directions based on current trends",
    "Which paper had the most innovative methodology?",
]

# ============================================
# QUESTION CATEGORY SUMMARY
# ============================================

question_categories = {
    "Relationship Queries (KG Expected to Win)": relationship_questions,
    "Counting & Aggregation (KG Expected to Win)": counting_questions,
    "Filtering Queries (KG Expected to Win)": filtering_questions,
    "Topic Queries (Mixed Results)": topic_questions,
    "Semantic/Content Queries (RAG Expected to Win)": semantic_questions,
    "Complex Multi-hop (KG Expected to Win)": complex_questions,
    "Temporal Queries (KG Expected to Win)": temporal_questions,
    "Comparison Queries (Mixed)": comparison_questions,
}


def print_question_summary():
    """Print a summary of all available question sets."""
    print("=" * 80)
    print("AVAILABLE QUESTION SETS")
    print("=" * 80)

    for category, questions in question_categories.items():
        print(f"\n{category}")
        print(f"  Total: {len(questions)} questions")
        print(f"  Examples:")
        for q in questions[:2]:
            print(f"    • {q}")

    print("\n" + "=" * 80)
    print("CURATED EVALUATION SETS")
    print("=" * 80)
    print(f"\nQuick Evaluation: {len(quick_eval_questions)} questions")
    print(f"Medium Evaluation: {len(medium_eval_questions)} questions")
    print(f"Strength/Weakness: {len(strength_weakness_questions)} questions")
    print("\n" + "=" * 80)


# ============================================
# MAIN EXECUTION EXAMPLES
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("Sample Questions for RAG vs Knowledge Graph Evaluation")
    print("=" * 80)
    print("\nLearn more about building advanced multi-agent systems:")
    print("🎓 https://maven.com/boring-bot/advanced-llm?promoCode=200OFF")
    print("=" * 80)

    # Show available question sets
    print_question_summary()

    print("\n\nSelect an evaluation to run:")
    print("1. Quick Evaluation (10 questions)")
    print("2. Medium Evaluation (20 questions)")
    print("3. Relationship Queries Only")
    print("4. Semantic Queries Only")
    print("5. Strength/Weakness Analysis")

    # Uncomment to run specific evaluations:

    # Option 1: Quick evaluation
    print("\n\nRunning Quick Evaluation...")
    batch_judge_questions(quick_eval_questions)

    # Option 2: Medium evaluation
    # print("\n\nRunning Medium Evaluation...")
    # batch_judge_questions(medium_eval_questions)

    # Option 3: Specific category
    # print("\n\nEvaluating Relationship Queries...")
    # batch_judge_questions(relationship_questions)

    # Option 4: Semantic queries
    # print("\n\nEvaluating Semantic Queries...")
    # batch_judge_questions(semantic_questions)

    # Option 5: Strength/Weakness analysis
    # print("\n\nRunning Strength/Weakness Analysis...")
    # batch_judge_questions(strength_weakness_questions)
