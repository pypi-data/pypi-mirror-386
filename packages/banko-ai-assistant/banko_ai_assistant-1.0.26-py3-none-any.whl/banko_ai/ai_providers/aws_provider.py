"""
AWS Bedrock AI provider implementation.

This module provides AWS Bedrock integration for vector search and RAG responses.
"""

import os
import json
from typing import List, Dict, Any, Optional
import boto3
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

from .base import AIProvider, SearchResult, RAGResponse, AIConnectionError, AIAuthenticationError


class AWSProvider(AIProvider):
    """AWS Bedrock AI provider implementation."""
    
    def __init__(self, config: Dict[str, Any], cache_manager=None):
        """Initialize AWS provider."""
        # Support both config and environment variables with defaults
        self.access_key_id = config.get("access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = config.get("secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = config.get("region") or os.getenv("AWS_REGION", "us-east-1")
        self.model_id = config.get("model") or os.getenv("AWS_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        self.bedrock_client = None
        self.embedding_model = None
        self.db_engine = None
        self.cache_manager = cache_manager
        
        # Make credentials optional for demo mode
        if not self.access_key_id:
            print("⚠️ AWS_ACCESS_KEY_ID not found - running in demo mode")
        if not self.secret_access_key:
            print("⚠️ AWS_SECRET_ACCESS_KEY not found - running in demo mode")
        
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate AWS configuration."""
        try:
            # Let boto3 automatically discover credentials
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
            print(f"✅ AWS Bedrock client created (region: {self.region}, model: {self.model_id})")
            
            # Verify credentials by getting caller identity
            print("🔍 Verifying AWS credentials...")
            sts = boto3.client('sts', region_name=self.region)
            identity = sts.get_caller_identity()
            print(f"✅ AWS Identity verified: {identity['Arn']}")
            print(f"   Account: {identity['Account']}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n⚠️ AWS Bedrock initialization failed!")
            print(f"   Error: {error_msg}")
            
            # Provide specific help based on error type
            if 'ExpiredToken' in error_msg or 'expired' in error_msg.lower():
                print("\n❌ Your AWS credentials have EXPIRED")
                print("\n💡 To fix:")
                print("   1. Get fresh credentials from AWS Console")
                print("   2. Or run: aws sso login (if using SSO)")
            elif 'NoCredentials' in error_msg or 'Unable to locate credentials' in error_msg:
                print("\n❌ No AWS credentials found")
                print("   Set credentials via:")
                print("   - export AWS_ACCESS_KEY_ID=...")
                print("   - export AWS_SECRET_ACCESS_KEY=...")
                print("   - Or configure ~/.aws/credentials")
            
            self.bedrock_client = None
            print()
    
    def get_default_model(self) -> str:
        """Get the default AWS model."""
        return "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def get_available_models(self) -> List[str]:
        """Get available AWS models."""
        return [
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "us.anthropic.claude-3-opus-20240229-v1:0",
            "us.anthropic.claude-3-sonnet-20240229-v1:0",
            "us.anthropic.claude-3-haiku-20240307-v1:0"
        ]
    
    def _get_embedding_model(self) -> SentenceTransformer:
        """Get or create the embedding model."""
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
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
            
            # FIXED: Use named parameters with a dictionary instead of %s with a list
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
                "limit": limit
            }
            
            # Conditionally add user_id filter if provided
            if user_id:
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
                WHERE user_id = :user_id
                ORDER BY embedding <=> :search_embedding
                LIMIT :limit
                """
                params["user_id"] = user_id
            
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
        """Generate comprehensive financial insights from expense data."""
        if not search_results:
            return {}
        
        total_amount = 0
        categories = {}
        merchants = {}
        payment_methods = {}
        
        for result in search_results:
            # Handle both SearchResult objects and dictionaries
            if hasattr(result, 'amount'):
                amount = float(result.amount)
                merchant = result.merchant
                category = result.metadata.get('shopping_type', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
                payment = result.metadata.get('payment_method', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
            else:
                amount = float(result.get('expense_amount', 0))
                merchant = result.get('merchant', 'Unknown')
                category = result.get('shopping_type', 'Unknown')
                payment = result.get('payment_method', 'Unknown')
            
            total_amount += amount
            categories[category] = categories.get(category, 0) + amount
            merchants[merchant] = merchants.get(merchant, 0) + amount
            payment_methods[payment] = payment_methods.get(payment, 0) + amount
        
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
        """Generate personalized budget recommendations based on spending patterns."""
        if not insights:
            return ""
        
        recommendations = []
        
        if insights.get('top_category'):
            category, amount = insights['top_category']
            recommendations.append(f"Your highest spending category is **{category}** at **${amount:.2f}**. Consider setting a monthly budget limit for this category.")
        
        avg_amount = insights.get('avg_transaction', 0)
        if avg_amount > 100:
            recommendations.append(f"Your average transaction is **${avg_amount:.2f}**. Consider reviewing larger purchases to identify potential savings.")
        
        if insights.get('top_merchant'):
            merchant, amount = insights['top_merchant']
            recommendations.append(f"You frequently shop at **{merchant}** (${amount:.2f} total). Look for loyalty programs or discounts at this merchant.")
        
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
        """Generate RAG response using AWS Bedrock."""
        try:
            print(f"\n🤖 AWS BEDROCK RAG (with caching):")
            print(f"1. Query: '{query[:60]}...'")
            
            # Check for cached response first
            if self.cache_manager:
                # Convert context to dict format for cache lookup (handle both objects and dicts)
                search_results_dict = []
                for result in context:
                    if hasattr(result, 'expense_id'):
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
                        search_results_dict.append(result)
                
                cached_response = self.cache_manager.get_cached_response(
                    query, search_results_dict, "aws"
                )
                if cached_response:
                    print(f"2. ✅ Response cache HIT! Returning cached response")
                    return RAGResponse(
                        response=cached_response,
                        sources=context,
                        metadata={
                            'provider': 'aws',
                            'model': self.get_default_model(),
                            'user_id': user_id,
                            'language': language,
                            'cached': True
                        }
                    )
                print(f"2. ❌ Response cache MISS, generating fresh response")
            else:
                print(f"2. No cache manager available, generating fresh response")
            
            # Generate financial insights
            insights = self._get_financial_insights(context)
            budget_recommendations = self._generate_budget_recommendations(insights, query)
            
            # Prepare the search results context with enhanced analysis
            search_results_text = ""
            if context:
                context_parts = []
                for result in context:
                    if hasattr(result, 'amount'):
                        description = result.description
                        merchant = result.merchant
                        amount = result.amount
                        shopping_type = result.metadata.get('shopping_type', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
                        payment_method = result.metadata.get('payment_method', 'Unknown') if hasattr(result, 'metadata') and result.metadata else 'Unknown'
                    else:
                        description = result.get('description', '')
                        merchant = result.get('merchant', 'Unknown')
                        amount = result.get('expense_amount', 0)
                        shopping_type = result.get('shopping_type', 'Unknown')
                        payment_method = result.get('payment_method', 'Unknown')
                    
                    context_parts.append(
                        f"• **{shopping_type}** at {merchant}: ${amount} ({payment_method}) - {description}"
                    )
                
                search_results_text = "\n".join(context_parts)
                
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
            
            # Create enhanced prompt
            enhanced_prompt = f"""You are Banko, a financial assistant. Answer based on this expense data:

Q: {query}

Data:
{search_results_text}

{budget_recommendations if budget_recommendations else ''}

Provide helpful insights with numbers, markdown formatting, and actionable advice."""
            
            # Define input parameters for Claude
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "top_k": 250,
                "stop_sequences": [],
                "temperature": 1,
                "top_p": 0.999,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": enhanced_prompt
                            }
                        ]
                    }
                ]
            }
            
            # Convert to JSON format
            body = json.dumps(payload)
            
            # Use current model
            model_id = self.current_model
            
            # Invoke model
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            # Cache the response for future similar queries
            if self.cache_manager and ai_response:
                search_results_dict = []
                for result in context:
                    if hasattr(result, 'expense_id'):
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
                        search_results_dict.append(result)
                
                # Estimate token usage
                prompt_tokens = len(enhanced_prompt.split()) * 1.3
                response_tokens = len(ai_response.split()) * 1.3
                
                self.cache_manager.cache_response(
                    query, ai_response, search_results_dict, "aws",
                    int(prompt_tokens), int(response_tokens)
                )
                print(f"3. ✅ Cached response (est. {int(prompt_tokens + response_tokens)} tokens)")
            
            return RAGResponse(
                response=ai_response,
                sources=context,
                metadata={
                    "provider": "aws",
                    "model": model_id,
                    "region": self.region,
                    "language": language,
                    "user_id": user_id,
                    "cached": False
                }
            )
            
        except Exception as e:
            raise AIConnectionError(f"RAG response generation failed: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding_model = self._get_embedding_model()
            embedding = embedding_model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            raise AIConnectionError(f"Embedding generation failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test AWS Bedrock connection."""
        try:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Hello"}]
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.current_model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text'] is not None
            
        except Exception:
            return False