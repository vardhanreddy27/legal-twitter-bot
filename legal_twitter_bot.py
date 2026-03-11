#!/usr/bin/env python3
"""
Legal News Twitter Bot - Automated posts about AP, Delhi HC, Kadapa court cases
Uses Groq for content generation and Twitter API for posting
"""

import os
import requests
from datetime import datetime
from groq import Groq
import tweepy
from typing import Optional

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Twitter client
twitter_client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    wait_on_rate_limit=True
)


def search_legal_news() -> str:
    """
    Search for legal news related to AP, Delhi High Court, Kadapa District
    Uses NewsAPI or direct web search
    """
    print("🔍 Searching for legal news...")
    
    # Keywords for search
    keywords = [
        "Delhi High Court",
        "AP court",
        "Kadapa District court",
        "Andhra Pradesh law",
        "advocate news"
    ]
    
    # Option 1: Using NewsAPI (requires free API key from newsapi.org)
    news_api_key = os.getenv("NEWS_API_KEY")
    news_items = []
    
    if news_api_key:
        for keyword in keywords:
            try:
                url = f"https://newsapi.org/v2/everything"
                params = {
                    "q": keyword,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 5,
                    "apiKey": news_api_key
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    articles = response.json().get("articles", [])
                    if articles:
                        # Get the latest article
                        latest = articles[0]
                        news_items.append({
                            "title": latest.get("title", ""),
                            "description": latest.get("description", ""),
                            "url": latest.get("url", ""),
                            "source": latest.get("source", {}).get("name", "")
                        })
            except Exception as e:
                print(f"Error fetching news for '{keyword}': {e}")
    
    # If no news found, use mock data (for testing)
    if not news_items:
        print("⚠️  No news found. Using sample legal topic for demonstration...")
        news_items = [
            {
                "title": "Delhi High Court Issues Important Ruling on Advocate Rights",
                "description": "Delhi High Court has passed a landmark judgment regarding advocate practice guidelines",
                "source": "Legal News India",
                "url": "https://legalnewsindia.com"
            }
        ]
    
    # Combine news into a single string
    news_text = "\n".join([
        f"Title: {item['title']}\nSource: {item['source']}\nDescription: {item['description']}"
        for item in news_items[:3]  # Use top 3 articles
    ])
    
    return news_text


def generate_tweet(news_content: str) -> str:
    """
    Use Groq to generate an engaging tweet about legal news
    Keeps it within Twitter's character limit (280 chars)
    """
    print("✍️  Generating tweet with Groq...")
    
    prompt = f"""You are an advocate and legal news expert. Based on the following legal news, generate ONE engaging Twitter post about it.

Requirements:
- Maximum 270 characters (must fit in a tweet with room for hashtags)
- Professional but accessible tone
- Include relevant hashtags (#Delhi #LawIndia #AdvocateLife #IndianLaw #AP #KadapaDistrict as relevant)
- No promotional content
- Focus on the legal/advocacy angle
- Make it interesting and shareable

Legal News:
{news_content}

Generate ONLY the tweet text, nothing else."""

    try:
        # Use the correct Groq API method
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Free Groq model
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        tweet = response.choices[0].message.content.strip()
        
        # Ensure it's within character limit
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        
        return tweet
    
    except Exception as e:
        print(f"❌ Error generating tweet: {e}")
        return None


def post_to_twitter(tweet_text: str) -> bool:
    """
    Post the generated tweet to Twitter
    """
    if not tweet_text:
        print("❌ No tweet text provided")
        return False
    
    try:
        print(f"📤 Posting to Twitter: {tweet_text[:50]}...")
        
        response = twitter_client.create_tweet(text=tweet_text)
        
        if response.data and response.data.get("id"):
            print(f"✅ Tweet posted successfully! Tweet ID: {response.data['id']}")
            return True
        else:
            print("❌ Failed to post tweet")
            return False
    
    except Exception as e:
        print(f"❌ Error posting to Twitter: {e}")
        return False


def main():
    """
    Main function to orchestrate the entire process
    """
    print("\n" + "="*60)
    print("🏛️  LEGAL NEWS TWITTER BOT")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check for required API keys
    required_keys = ["GROQ_API_KEY", "TWITTER_BEARER_TOKEN", "TWITTER_CONSUMER_KEY",
                     "TWITTER_CONSUMER_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
    
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        print("Please set these environment variables before running.\n")
        return False
    
    # Step 1: Search for legal news
    news_content = search_legal_news()
    
    if not news_content:
        print("❌ Could not find any legal news")
        return False
    
    # Step 2: Generate tweet using Groq
    tweet = generate_tweet(news_content)
    
    if not tweet:
        print("❌ Could not generate tweet")
        return False
    
    print(f"\n📝 Generated Tweet:\n{tweet}\n")
    print(f"Character count: {len(tweet)}/280\n")
    
    # Step 3: Post to Twitter
    success = post_to_twitter(tweet)
    
    print("\n" + "="*60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    return success


if __name__ == "__main__":
    main()
