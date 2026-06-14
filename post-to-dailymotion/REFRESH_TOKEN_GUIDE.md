# Dailymotion Refresh Token Guide

This guide explains how to generate a `refresh_token` for Dailymotion using the `password` grant type. This token is required for the `DAILYMOTION_REFRESH_TOKEN` environment variable used by the posting script.

## Prerequisites

1.  **Dailymotion API Key and Secret:** Create an API key in the [Dailymotion Developer Portal](https://www.dailymotion.com/settings/developer).
2.  **Dailymotion Account:** You need the username (email) and password for the account you want to post to.

## Steps to Generate Refresh Token

### 1. Use the Password Grant Type

You can generate an access token and a refresh token by sending a POST request to the Dailymotion OAuth endpoint using your account credentials.

Replace the placeholders in the following `curl` command:

```bash
curl -X POST https://api.dailymotion.com/oauth/token \
  -d "grant_type=password" \
  -d "client_id=YOUR_API_KEY" \
  -d "client_secret=YOUR_API_SECRET" \
  -d "username=YOUR_EMAIL" \
  -d "password=YOUR_PASSWORD" \
  -d "scope=manage_videos"
```

### 2. Extract the Refresh Token

The response will be a JSON object:

```json
{
    "access_token": "ACCESS_TOKEN",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "manage_videos",
    "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

Copy the value of `"refresh_token"`. This is what you should use for the `DAILYMOTION_REFRESH_TOKEN` environment variable.

## Security Note

**Important:** Never share your `client_secret` or `refresh_token`. If you are using GitHub Actions, store these as **Secrets**.

## Reference

For more details, see the official Dailymotion documentation:
- [Generate access token with password method](https://developers.dailymotion.com/reference/generate-access-token-with-password-method)
- [Generate refresh token](https://developers.dailymotion.com/reference/api-generate-refresh-token)
