# Kraken API Keys Configuration Guide

## Overview

This document explains how to securely configure and use Kraken API keys in the Muckard project. The system supports two types of API keys:

1. **Read-only Keys** - Safe for development/testing (cannot execute trades)
2. **Trading Keys** - For production only (can execute real trades)

## Key Types

### Read-only Keys
- **Purpose**: Development, testing, and data fetching
- **Capabilities**: Can read account data, balances, market data
- **Limitations**: Cannot execute trades, withdrawals, or deposits
- **Safety**: Safe to use in development environments

### Trading Keys
- **Purpose**: Production trading operations
- **Capabilities**: Can execute trades, read data, manage positions
- **Limitations**: None - full trading access
- **Safety**: ⚠️ **DANGEROUS** - Can execute real trades with real money

## Configuration

### Backend Services (muckard-fastapi)

The backend services use a mode-based approach to select which keys to use.

#### Environment Variables

Add to `muckard-fastapi/.env`:

```env
# Development/Testing (Read-only keys - SAFE for testing)
KRAKEN_API_KEY_READONLY=your_readonly_api_key_here
KRAKEN_API_SECRET_READONLY=your_readonly_api_secret_here

# Production (Trading keys - ONLY for production)
KRAKEN_API_KEY_TRADING=your_trading_api_key_here
KRAKEN_API_SECRET_TRADING=your_trading_api_secret_here

# Default key mode (readonly for dev, trading for prod)
KRAKEN_KEY_MODE=readonly
```

#### Key Mode Selection

The system uses the `KRAKEN_KEY_MODE` environment variable to determine which keys to use:

- `KRAKEN_KEY_MODE=readonly` - Uses read-only keys (default, safe for development)
- `KRAKEN_KEY_MODE=trading` - Uses trading keys (production only)

#### Accessing Keys in Code

```python
from app.config import settings

# Get the appropriate key based on mode
api_key = settings.kraken_api_key
api_secret = settings.kraken_api_secret
```

### Bot Service (muckard-bot)

The bot service uses direct environment variables.

#### Environment Variables

Add to `muckard-bot/.env`:

```env
# Development/Testing (Read-only keys - SAFE for testing)
API_KEY=your_readonly_api_key_here
API_SECRET=your_readonly_api_secret_here

# Production (Trading keys - ONLY for production)
# Uncomment and use ONLY in production:
# API_KEY=your_trading_api_key_here
# API_SECRET=your_trading_api_secret_here
```

**Note**: The bot service uses `API_KEY` and `API_SECRET` (not `KRAKEN_API_KEY`), as per the existing code in `src/util/config.py`.

## Security Best Practices

### 1. Never Commit Keys to Git
- ✅ `.env` files are in `.gitignore` - never commit them
- ✅ Use `.env.example` files as templates
- ✅ Use environment variables or Vault for production

### 2. Use Read-only Keys for Development
- ✅ Always use read-only keys in development
- ✅ Read-only keys cannot execute trades - safe for testing
- ✅ Trading keys should only be used in production

### 3. Production Key Management
- ✅ Use HashiCorp Vault for production key storage
- ✅ Rotate keys regularly
- ✅ Use separate keys for different environments
- ✅ Monitor key usage and permissions

### 4. Safety Checks
The system includes automatic safety checks:
- ⚠️ Warning if trading keys are used in DEBUG mode
- ⚠️ Logs warnings when trading keys are detected in development

## Switching Between Modes

### Development to Production

1. **Backend Services**:
   ```env
   # Change in muckard-fastapi/.env
   KRAKEN_KEY_MODE=trading
   ```

2. **Bot Service**:
   ```env
   # Update in muckard-bot/.env
   # Comment out read-only keys
   # API_KEY=your_readonly_api_key_here
   # API_SECRET=your_readonly_api_secret_here
   
   # Uncomment trading keys
   API_KEY=your_trading_api_key_here
   API_SECRET=your_trading_api_secret_here
   ```

### Production to Development

1. **Backend Services**:
   ```env
   # Change in muckard-fastapi/.env
   KRAKEN_KEY_MODE=readonly
   ```

2. **Bot Service**:
   ```env
   # Update in muckard-bot/.env
   # Comment out trading keys
   # API_KEY=your_trading_api_key_here
   # API_SECRET=your_trading_api_secret_here
   
   # Uncomment read-only keys
   API_KEY=your_readonly_api_key_here
   API_SECRET=your_readonly_api_secret_here
   ```

## Troubleshooting

### Issue: Trading keys used in development

**Symptom**: Warning messages in logs about trading keys in DEBUG mode

**Solution**: 
1. Check `KRAKEN_KEY_MODE` in `muckard-fastapi/.env` - should be `readonly`
2. Check bot service `.env` - should use read-only keys
3. Restart services after changing environment variables

### Issue: Keys not loading

**Symptom**: API calls fail with authentication errors

**Solution**:
1. Verify `.env` file exists in the correct location
2. Check environment variable names match exactly
3. Ensure no extra spaces or quotes around values
4. Restart services after updating `.env`

### Issue: Wrong keys being used

**Symptom**: Unexpected behavior (e.g., trades executing in development)

**Solution**:
1. Verify `KRAKEN_KEY_MODE` setting
2. Check which keys are actually loaded (check logs)
3. Ensure `.env` files are in the correct directories
4. Clear any cached configuration

## Client-Provided Keys

The client has provided both read-only and trading keys. These should be:

1. **Stored securely** in `.env` files (not committed to git)
2. **Used appropriately** - read-only for dev, trading for prod
3. **Protected** - never share or expose in logs/errors
4. **Rotated** - if compromised, generate new keys immediately

## Additional Resources

- [Kraken API Documentation](https://docs.kraken.com/rest/)
- [Kraken API Key Permissions](https://support.kraken.com/hc/en-us/articles/360000919966-How-to-generate-an-API-key-pair)
- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)

## Support

If you encounter issues with API key configuration:
1. Check this documentation
2. Review environment variable settings
3. Check service logs for warnings/errors
4. Contact the development team

