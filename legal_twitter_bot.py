#!/usr/bin/env python3
"""
Legal News Twitter Bot - Automated posts about AP, Delhi HC, Kadapa court cases
Uses Groq for content generation and Twitter API v1.1 with OAuth 1.0a
"""

import os
import requests
from datetime import datetime
from groq import Groq
from requests_oauthlib import OAuth1Session

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Twitter API v1.1 endpoint for posting tweets
TWITTER_API_URL = "https://api.twitter.com/1.1/statuses/update.json"

# Get Twitter credentials from environment
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")


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
        # Use the correct Groq API method with latest working model
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Latest working Groq model (free tier)
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
    Post the generated tweet to Twitter using OAuth 1.0a User Context
    """
    if not tweet_text:
        print("❌ No tweet text provided")
        return False
    
    try:
        print(f"📤 Posting to Twitter: {tweet_text[:50]}...")
        
        # Create OAuth 1.0a session
        twitter = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=ACCESS_TOKEN,
            resource_owner_secret=ACCESS_TOKEN_SECRET
        )
        
        # Post the tweet
        payload = {"status": tweet_text}
        response = twitter.post(TWITTER_API_URL, json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            tweet_id = response_data.get("id")
            print(f"✅ Tweet posted successfully! Tweet ID: {tweet_id}")
            return True
        else:
            print(f"❌ Failed to post tweet. Status code: {response.status_code}")
            print(f"Response: {response.text}")
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
    required_keys = ["GROQ_API_KEY", "TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET",
                     "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]
    
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
