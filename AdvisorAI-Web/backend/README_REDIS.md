# Redis Setup for Chat Caching

## Overview
The chat system now uses Redis for caching chat sessions to improve performance and ensure chat history persistence.

## Installation

### Option 1: Install Redis Locally
```bash
# macOS (using Homebrew)
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server

# Start Redis
redis-server
```

### Option 2: Use Docker
```bash
# Pull and run Redis container
docker run -d --name redis-chat -p 6379:6379 redis:alpine
```

### Option 3: Use Redis Cloud (Free Tier)
1. Sign up at https://redis.com/
2. Create a free database
3. Get connection details and update environment variables

## Environment Variables
Add these to your `.env` file:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional: Redis Cloud connection
# REDIS_HOST=your-redis-cloud-host
# REDIS_PORT=your-redis-cloud-port
# REDIS_PASSWORD=your-redis-cloud-password
```

## Features

### Caching Benefits
- **1-hour cache** for chat sessions
- **Automatic invalidation** when sessions are modified
- **Fallback to database** if Redis is unavailable
- **Improved performance** for frequent chat history access

### Cache Keys
- `chat_sessions:{user_id}` - Cached chat sessions for each user

### Cache Invalidation
Cache is automatically invalidated when:
- New chat session is created
- Session title is updated
- Messages are added to a session
- Session is deleted

## Testing Redis Connection
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Check if keys exist
redis-cli keys "chat_sessions:*"
```

## Troubleshooting

### Redis Connection Failed
If Redis is not available, the system will:
1. Log a warning message
2. Continue working without caching
3. Fetch data directly from Firestore

### Performance Monitoring
Monitor cache hit rates and performance:
```bash
# Check Redis info
redis-cli info memory
redis-cli info stats
```

## Production Considerations
- Use Redis Cloud or managed Redis service for production
- Set up Redis persistence for data durability
- Configure Redis security (authentication, network access)
- Monitor Redis memory usage and performance 