"""
Google Gemini AI provider implementation.

This module provides Google Vertex AI/Gemini integration for vector search and RAG responses.
"""

import os
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

try:
    from google.cloud import aiplatform
    from google.oauth2 import service_account
    import vertexai
    from vertexai.generative_models import GenerativeModel
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import AIProvider, SearchResult, RAGResponse, AIConnectionError, AIAuthenticationError


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""

    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize Gemini provider."""
        if not GEMINI_AVAILABLE:
            raise AIConnectionError("Google Cloud AI Platform not available. Install with: pip install google-cloud-aiplatform vertexai")

        self.cache_manager = cache_manager

        self.project_id = config.get("project_id") or os.getenv("GOOGLE_PROJECT_ID")
        self.location = config.get("location") or os.getenv("GOOGLE_LOCATION", "us-central1")
        self.model_name = config.get("model") or os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-001")
        self.embedding_model = None
        self.db_engine = None
        self.vertex_client = None
        self.genai_client = None
        self.credentials = None
        self.use_vertex_ai = True  # Try Vertex AI first, fallback to Generative AI
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate Gemini configuration."""
        if not self.project_id:
            raise AIAuthenticationError("Google project ID is required")

        # Set up authentication from service account key file
        try:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path and os.path.exists(credentials_path):
                self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
                print(f"✅ Loaded Google credentials from: {credentials_path}")

                # Try Vertex AI first
                try:
                    vertexai.init(
                        project=self.project_id,
                        location=self.location,
                        credentials=self.credentials
                    )

                    # Create the generative model using the correct model name
                    model_name = self.model_name
                    if model_name == "gemini-1.5-pro":
                        model_name = "gemini-1.5-pro-001"
                    elif model_name == "gemini-1.5-flash":
                        model_name = "gemini-1.5-flash-001"
                    elif model_name == "gemini-1.0-pro":
                        model_name = "gemini-1.0-pro-001"

                    self.vertex_client = GenerativeModel(model_name)
                    self.use_vertex_ai = True
                    print(f"✅ Initialized Vertex AI with project: {self.project_id}, location: {self.location}, model: {self.model_name}")

                except Exception as vertex_error:
                    print(f"⚠️  Vertex AI initialization failed: {vertex_error}")
                    print("🔄 Falling back to Generative AI API...")

                    # Fallback to Generative AI API
                    try:
                        # Check if there's a GOOGLE_API_KEY environment variable
                        api_key = os.getenv("GOOGLE_API_KEY")
                        if api_key:
                            genai.configure(api_key=api_key)
                            self.genai_client = genai.GenerativeModel(self.model_name)
                            self.use_vertex_ai = False
                            print(f"✅ Initialized Generative AI API with model: {self.model_name}")
                        else:
                            print("❌ No GOOGLE_API_KEY found for Generative AI API fallback")
                            raise AIConnectionError("Both Vertex AI and Generative AI API initialization failed - no API key")

                    except Exception as genai_error:
                        print(f"❌ Generative AI API initialization failed: {genai_error}")
                        raise AIConnectionError(f"Failed to initialize both Vertex AI and Generative AI: {vertex_error}")

            else:
                print("❌ No GOOGLE_APPLICATION_CREDENTIALS found")
                raise AIAuthenticationError("Google credentials are required")

        except Exception as e:
            if isinstance(e, (AIConnectionError, AIAuthenticationError)):
                raise
            raise AIConnectionError(f"Failed to initialize Gemini provider: {str(e)}")

    def get_default_model(self) -> str:
        """Get the default Gemini model."""
        return "gemini-1.5-pro"

    def get_available_models(self) -> List[str]:
        """Get available Gemini models."""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro"
        ]

    def _get_embedding_model(self) -> SentenceTransformer:
        """Get or create the embedding model."""
        if self.embedding_model is None:
            try:
                # Use configurable embedding model from environment or default
                embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                self.embedding_model = SentenceTransformer(embedding_model_name)
            except Exception as e:
                raise AIConnectionError(f"Failed to load embedding model: {str(e)}")
        return self.embedding_model

    def _get_db_engine(self):
        """Get database engine."""
        if self.db_engine is None:
            database_url = os.getenv("DATABASE_URL", "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable")
            try:
                self.db_engine = create_engine(database_url)
            except Exception as e:
                raise AIConnectionError(f"Failed to connect to database: {str(e)}")
        return self.db_engine

    def search_expenses(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """Search for expenses using vector similarity."""
        try:
            # Generate query embedding
            embedding_model = self._get_embedding_model()
            query_embedding = embedding_model.encode([query])[0]

            # Convert to PostgreSQL vector format (JSON string)
            search_embedding = json.dumps(query_embedding.tolist())

            # Build SQL query using named parameters (e.g., :search_embedding)
            sql = """
            SELECT
                expense_id,
                user_id,
                description,
                merchant,
                expense_amount,
                expense_date,
                embedding <=> :search_embedding as similarity_score
            FROM expenses
            ORDER BY embedding <=> :search_embedding
            LIMIT :limit
            """

            # Build the parameters dictionary
            params = {
                "search_embedding": search_embedding,
                "threshold": threshold,
                "limit": limit
            }

            # Execute query using the dictionary of parameters
            engine = self._get_db_engine()
            with engine.connect() as conn:
                result = conn.execute(text(sql), params)
                rows = result.fetchall()

            # Convert to SearchResult objects
            results = []
            for row in rows:
                results.append(SearchResult(
                    expense_id=str(row[0]),
                    user_id=str(row[1]),
                    description=row[2] or "",
                    merchant=row[3] or "",
                    amount=float(row[4]),
                    date=str(row[5]),
                    similarity_score=float(row[6]),
                    metadata={}
                ))

            return results

        except Exception as e:
            raise AIConnectionError(f"Search failed: {str(e)}")

    def _get_financial_insights(self, search_results) -> dict:
        """Generate comprehensive financial insights from expense data (handles both SearchResult objects and dicts)."""
        if not search_results:
            return {}

        total_amount = 0
        categories = {}
        merchants = {}
        payment_methods = {}

        for result in search_results:
            # Handle both SearchResult objects and dictionaries
            if hasattr(result, 'amount'):
                # It's a SearchResult object
                amount = float(result.amount)
                merchant = result.merchant
                category = result.metadata.get('shopping_type', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
                payment = result.metadata.get('payment_method', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
            else:
                # It's a dictionary
                amount = float(result.get('expense_amount', 0))
                merchant = result.get('merchant', 'Unknown')
                category = result.get('shopping_type', 'Unknown')
                payment = result.get('payment_method', 'Unknown')

            total_amount += amount

            # Category analysis
            categories[category] = categories.get(category, 0) + amount

            # Merchant analysis
            merchants[merchant] = merchants.get(merchant, 0) + amount

            # Payment method analysis
            payment_methods[payment] = payment_methods.get(payment, 0) + amount

        # Find top categories and merchants
        top_category = max(categories.items(), key=lambda x: x[1]) if categories else None
        top_merchant = max(merchants.items(), key=lambda x: x[1]) if merchants else None

        return {
            'total_amount': total_amount,
            'num_transactions': len(search_results),
            'avg_transaction': total_amount / len(search_results) if search_results else 0,
            'categories': categories,
            'top_category': top_category,
            'top_merchant': top_merchant,
            'payment_methods': payment_methods
        }

    def _generate_budget_recommendations(self, insights: dict, prompt: str) -> str:
        """Generate personalized budget recommendations based on spending patterns (following WatsonX pattern)."""
        if not insights:
            return ""

        recommendations = []

        # High spending category recommendations
        if insights.get('top_category'):
            category, amount = insights['top_category']
            recommendations.append(f"Your highest spending category is **{category}** at **${amount:.2f}**. Consider setting a monthly budget limit for this category.")

        # Average transaction analysis
        avg_amount = insights.get('avg_transaction', 0)
        if avg_amount > 100:
            recommendations.append(f"Your average transaction is **${avg_amount:.2f}**. Consider reviewing larger purchases to identify potential savings.")

        # Merchant frequency analysis
        if insights.get('top_merchant'):
            merchant, amount = insights['top_merchant']
            recommendations.append(f"You frequently shop at **{merchant}** (${amount:.2f} total). Look for loyalty programs or discounts at this merchant.")

        # General budgeting tips
        if insights.get('total_amount', 0) > 500:
            recommendations.append("💡 **Budget Tip**: Consider the 50/30/20 rule: 50% for needs, 30% for wants, 20% for savings and debt repayment.")

        return "\n".join(recommendations) if recommendations else ""

    def generate_rag_response(
        self,
        query: str,
        context: List[SearchResult],
        user_id: Optional[str] = None,
        language: str = "en"
    ) -> RAGResponse:
        """Generate RAG response using Google Gemini (following WatsonX pattern)."""
        try:
            print(f"\n🤖 GOOGLE GEMINI RAG (with caching):")
            print(f"1. Query: '{query[:60]}...'")

            # DEBUG: Check what we received
            print(f"DEBUG: Context type: {type(context)}")
            print(f"DEBUG: Context length: {len(context)}")
            if context:
                print(f"DEBUG: First item type: {type(context[0])}")
                print(f"DEBUG: First item: {context[0]}")
                if hasattr(context[0], '__dict__'):
                    print(f"DEBUG: First item attributes: {context[0].__dict__}")

            # Check for cached response first
            if self.cache_manager:
                # Convert SearchResult objects to dict format for cache lookup
                search_results_dict = []
                for i, result in enumerate(context):
                    print(f"DEBUG: Processing context item {i}: type={type(result)}")
                    try:
                        # Handle both SearchResult objects and dictionaries
                        if hasattr(result, 'expense_id'):
                            # It's a SearchResult object
                            search_results_dict.append({
                                'expense_id': result.expense_id,
                                'user_id': result.user_id,
                                'description': result.description,
                                'merchant': result.merchant,
                                'expense_amount': result.amount,
                                'expense_date': result.date,
                                'similarity_score': result.similarity_score,
                                'shopping_type': result.metadata.get('shopping_type'),
                                'payment_method': result.metadata.get('payment_method'),
                                'recurring': result.metadata.get('recurring'),
                                'tags': result.metadata.get('tags')
                            })
                        else:
                            # It's already a dictionary - use it as is
                            search_results_dict.append(result)
                    except Exception as e:
                        print(f"DEBUG: Error processing context item {i}: {e}")
                        print(f"DEBUG: Item content: {result}")
                        raise

                cached_response = self.cache_manager.get_cached_response(
                    query, search_results_dict, "gemini"
                )
                if cached_response:
                    print(f"2. ✅ Response cache HIT! Returning cached response")
                    return RAGResponse(
                        response=cached_response,
                        sources=context,
                        metadata={
                            'provider': 'gemini',
                            'model': self.get_default_model(),
                            'user_id': user_id,
                            'language': language,
                            'cached': True
                        }
                    )
                print(f"2. ❌ Response cache MISS, generating fresh response")
            else:
                print(f"2. No cache manager available, generating fresh response")

            # Generate financial insights from search results (following WatsonX pattern)
            print(f"DEBUG: About to call _get_financial_insights with {len(context)} items")
            try:
                insights = self._get_financial_insights(context)
                print(f"DEBUG: Financial insights generated successfully: {insights}")
            except Exception as e:
                print(f"DEBUG: Error in _get_financial_insights: {e}")
                insights = {}

            try:
                budget_recommendations = self._generate_budget_recommendations(insights, query)
                print(f"DEBUG: Budget recommendations generated successfully")
            except Exception as e:
                print(f"DEBUG: Error in _generate_budget_recommendations: {e}")
                budget_recommendations = ""

            # Prepare the search results context with enhanced analysis (handles both objects and dicts)
            search_results_text = ""
            if context:
                context_parts = []
                for result in context:
                    # Handle both SearchResult objects and dictionaries
                    if hasattr(result, 'amount'):
                        # It's a SearchResult object
                        description = result.description
                        merchant = result.merchant
                        amount = result.amount
                        shopping_type = result.metadata.get('shopping_type', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
                        payment_method = result.metadata.get('payment_method', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
                    else:
                        # It's a dictionary
                        description = result.get('description', '')
                        merchant = result.get('merchant', 'Unknown')
                        amount = result.get('expense_amount', 0)
                        shopping_type = result.get('shopping_type', 'Unknown')
                        payment_method = result.get('payment_method', 'Unknown')

                    context_parts.append(
                        f"• **{shopping_type}** at {merchant}: ${amount} ({payment_method}) - {description}"
                    )

                search_results_text = "\n".join(context_parts)

                # Add financial summary
                if insights:
                    search_results_text += f"\n\n**📊 Financial Summary:**\n"
                    search_results_text += f"• Total Amount: **${insights['total_amount']:.2f}**\n"
                    search_results_text += f"• Number of Transactions: **{insights['num_transactions']}**\n"
                    search_results_text += f"• Average Transaction: **${insights['avg_transaction']:.2f}**\n"
                    if insights.get('top_category'):
                        cat, amt = insights['top_category']
                        search_results_text += f"• Top Category: **{cat}** (${amt:.2f})\n"
            else:
                search_results_text = "No specific expense records found for this query."

            # Create optimized prompt (following WatsonX pattern)
            enhanced_prompt = f"""You are Banko, a financial assistant. Answer based on this expense data:

Q: {query}

Data:
{search_results_text}

{budget_recommendations if budget_recommendations else ''}

Provide helpful insights with numbers, markdown formatting, and actionable advice."""

            # Generate response using either Vertex AI or Generative AI client
            ai_response = ""
            try:
                if self.use_vertex_ai and self.vertex_client:
                    from vertexai.generative_models import GenerationConfig

                    generation_config = GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=1000,
                        top_p=0.9,
                        top_k=40
                    )

                    # Make the request with Vertex AI
                    response = self.vertex_client.generate_content(
                        enhanced_prompt,
                        generation_config=generation_config
                    )

                    # Extract response text
                    if response and response.text:
                        ai_response = response.text
                    else:
                        ai_response = "I apologize, but I couldn't generate a response at this time."

                elif self.genai_client:
                    # Use Generative AI API
                    response = self.genai_client.generate_content(
                        enhanced_prompt,
                        generation_config={
                            'temperature': 0.7,
                            'max_output_tokens': 1000,
                            'top_p': 0.9,
                            'top_k': 40
                        }
                    )

                    # Extract response text
                    if response and response.text:
                        ai_response = response.text
                    else:
                        ai_response = "I apologize, but I couldn't generate a response at this time."
                else:
                    ai_response = "No Gemini client available."

            except Exception as e:
                # Fallback to structured response if API call fails (following WatsonX pattern)
                print(f"⚠️ Gemini API call failed: {e}")
                default_recommendations = "• Monitor your spending patterns regularly\n• Consider setting up budget alerts\n• Review high-value transactions for optimization opportunities"
                ai_response = f"""## Financial Analysis for: "{query}"

### 📋 Transaction Details
{search_results_text}

### 📊 Financial Summary
${insights.get('total_amount', 0):.2f} total across {insights.get('num_transactions', 0)} transactions

### 🤖 AI-Powered Insights
Based on your expense data, I found {len(context)} relevant records. Here's a comprehensive analysis:

**Spending Analysis:**
- Total Amount: ${insights.get('total_amount', 0):.2f}
- Transaction Count: {insights.get('num_transactions', 0)}
- Average Transaction: ${insights.get('avg_transaction', 0):.2f}
- Top Category: {insights.get('top_category', ('Unknown', 0))[0] if insights.get('top_category') else 'Unknown'} (${insights.get('top_category', ('Unknown', 0))[1] if insights.get('top_category') else 0:.2f})

**Smart Recommendations:**
{budget_recommendations if budget_recommendations else default_recommendations}

**Next Steps:**
• Track your spending trends over time
• Set realistic budget goals for each category
• Review and optimize your payment methods

**Note**: API call failed, showing structured analysis above."""

            # Cache the response for future similar queries
            if self.cache_manager and ai_response:
                # Convert context items to dict format for caching (handle both objects and dicts)
                search_results_dict = []
                for result in context:
                    if hasattr(result, 'expense_id'):
                        # It's a SearchResult object
                        search_results_dict.append({
                            'expense_id': result.expense_id,
                            'user_id': result.user_id,
                            'description': result.description,
                            'merchant': result.merchant,
                            'expense_amount': result.amount,
                            'expense_date': result.date,
                            'similarity_score': result.similarity_score,
                            'shopping_type': result.metadata.get('shopping_type') if result.metadata else None,
                            'payment_method': result.metadata.get('payment_method') if result.metadata else None,
                            'recurring': result.metadata.get('recurring') if result.metadata else None,
                            'tags': result.metadata.get('tags') if result.metadata else None
                        })
                    else:
                        # It's already a dictionary - use it as is or ensure it has the right keys
                        search_results_dict.append({
                            'expense_id': result.get('expense_id', ''),
                            'user_id': result.get('user_id', ''),
                            'description': result.get('description', ''),
                            'merchant': result.get('merchant', ''),
                            'expense_amount': result.get('expense_amount', 0),
                            'expense_date': result.get('expense_date', ''),
                            'similarity_score': result.get('similarity_score', 0),
                            'shopping_type': result.get('shopping_type'),
                            'payment_method': result.get('payment_method'),
                            'recurring': result.get('recurring'),
                            'tags': result.get('tags')
                        })

                # Estimate token usage (rough approximation for Gemini)
                prompt_tokens = len(enhanced_prompt.split()) * 1.3  # ~1.3 tokens per word
                response_tokens = len(ai_response.split()) * 1.3

                self.cache_manager.cache_response(
                    query, ai_response, search_results_dict, "gemini",
                    int(prompt_tokens), int(response_tokens)
                )
                print(f"3. ✅ Cached response (est. {int(prompt_tokens + response_tokens)} tokens)")

            return RAGResponse(
                response=ai_response,
                sources=context,
                metadata={
                    'provider': 'gemini',
                    "model": self.model_name,
                    "project_id": self.project_id,
                    "location": self.location,
                    "language": language,
                    'user_id': user_id,
                    'cached': False
                }
            )

        except Exception as e:
            # Return a structured error response like WatsonX does
            return RAGResponse(
                response=f"Sorry, I'm experiencing technical difficulties with Google Gemini. Error: {str(e)}",
                sources=context,
                metadata={
                    'provider': 'gemini',
                    'model': self.model_name,
                    'user_id': user_id,
                    'language': language,
                    'error': str(e)
                }
            )

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding_model = self._get_embedding_model()
            embedding = embedding_model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            raise AIConnectionError(f"Embedding generation failed: {str(e)}")

    def test_connection(self) -> bool:
        """Test Gemini connection."""
        try:
            # Test with a simple completion using the appropriate client
            if self.use_vertex_ai and self.vertex_client:
                from vertexai.generative_models import GenerationConfig

                generation_config = GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=5
                )

                response = self.vertex_client.generate_content(
                    "Hello",
                    generation_config=generation_config
                )

                return response and response.text is not None

            elif self.genai_client:
                response = self.genai_client.generate_content(
                    "Hello",
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 5
                    }
                )

                return response and response.text is not None
            else:
                return False

        except Exception as e:
            print(f"❌ Gemini connection test failed: {str(e)}")
            return False
