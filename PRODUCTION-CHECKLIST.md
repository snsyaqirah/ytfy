# YTFY Production Deployment Checklist

## Pre-Deployment Requirements

### ✅ Completed
- [x] Privacy Policy page
- [x] Bidirectional conversion working
- [x] Error handling and retry logic
- [x] Secure authentication flow
- [x] Session management (separate Spotify/YouTube)
- [x] Responsive UI with Tailwind CSS

### ⏳ To Do Before Production

#### 1. **Google OAuth Verification (YouTube API)**
- [ ] Change OAuth consent screen from "Testing" to "Production"
- [ ] Submit OAuth verification request
- [ ] Prepare verification materials:
  - [ ] **Video Demo**: 2-3 minute screen recording showing:
    - YouTube → Spotify conversion
    - Spotify → YouTube conversion
    - Auth flow (login/logout)
    - Privacy policy
  - [ ] **App Description**: Write detailed explanation of ytfy's purpose
  - [ ] **Justification**: Explain why you need YouTube playlist management scope
  - [ ] **Homepage URL**: Your deployed domain (e.g., ytfy.onrender.com)

#### 2. **Spotify Extended Quota Request**
- [ ] Go to Spotify Developer Dashboard
- [ ] Submit "Extended Quota Mode" request
- [ ] Provide:
  - [ ] App name: YTFY
  - [ ] App description: Bidirectional playlist converter
  - [ ] Website URL: Your deployed domain
  - [ ] Privacy policy URL: `https://your-domain.com/privacy`
  - [ ] Expected users: Estimate (100? 1000?)

#### 3. **Production Environment Setup**
- [ ] Deploy to Render (or preferred host)
- [ ] Set up custom domain (optional but professional)
  - Suggestion: `ytfy.app` or `ytfy.io`
- [ ] Update environment variables on hosting:
  - [ ] `FLASK_SECRET_KEY` - Generate new one for production
  - [ ] `SPOTIFY_CLIENT_ID` - Production credentials
  - [ ] `SPOTIFY_CLIENT_SECRET` - Production credentials
  - [ ] `YOUTUBE_API_KEY` - Same key (no changes needed)
  - [ ] `YOUTUBE_CLIENT_ID` - Production OAuth credentials
  - [ ] `YOUTUBE_CLIENT_SECRET` - Production OAuth credentials
  - [ ] `REDIRECT_URI` - Update to production domain
  - [ ] Remove `OAUTHLIB_INSECURE_TRANSPORT=1` (only for local dev)

#### 4. **Update OAuth Redirect URIs**
- [ ] **Spotify Dashboard**: Add production callback URL
  - Example: `https://ytfy.onrender.com/callback`
- [ ] **Google Cloud Console**: Add production callback URL
  - Example: `https://ytfy.onrender.com/youtube_callback`

#### 5. **Update API Restrictions**
- [ ] **YouTube API Key**: Update HTTP referrer restrictions
  - Add your production domain (e.g., `ytfy.onrender.com/*`)
  - Keep "None" for server-side requests OR add server IP

#### 6. **Create Terms of Service (Optional but Recommended)**
- [ ] Write ToS page (`templates/terms.html`)
- [ ] Add link in footer alongside Privacy Policy
- [ ] Include:
  - User responsibilities
  - Service limitations (API quotas)
  - Liability disclaimers

#### 7. **Add Rate Limiting (Recommended)**
- [ ] Install `flask-limiter`: `pip install flask-limiter`
- [ ] Add rate limits to prevent abuse:
  - Max 10 conversions per hour per IP
  - Max 50 requests per day per IP

#### 8. **Monitoring & Analytics (Optional)**
- [ ] Set up error logging (Sentry, LogRocket, etc.)
- [ ] Add basic analytics (Google Analytics, Plausible)
- [ ] Monitor API quota usage (create dashboard)

#### 9. **Testing**
- [ ] Test all conversion flows in production
- [ ] Test with fresh accounts (not test emails)
- [ ] Test error scenarios
- [ ] Mobile responsiveness check
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)

#### 10. **Legal Compliance**
- [ ] Add copyright notice
- [ ] Ensure compliance with YouTube TOS
- [ ] Ensure compliance with Spotify TOS
- [ ] Add DMCA takedown contact (if applicable)

---

## Production Deployment Steps

### 1. Deploy to Render
```bash
# Your app is already Dockerized and ready!
# Just push to GitHub and connect Render to your repo
```

### 2. Update OAuth Callbacks
```
Spotify Redirect URI: https://your-domain.com/callback
YouTube Redirect URI: https://your-domain.com/youtube_callback
```

### 3. Test Authentication
- Test Spotify login
- Test YouTube login
- Test both conversions
- Test logout

### 4. Submit for Verification
- **Google**: Can take 1-6 weeks
- **Spotify**: Usually 3-7 days

---

## During Verification Period

While waiting for Google verification:
- ✅ Spotify Extended Quota should work immediately after approval
- ⏳ YouTube will still be in "Testing" mode
- 💡 **Workaround**: Keep adding users manually until verified (up to 100 test users)

---

## Post-Verification

Once both are approved:
- ✅ Remove all test users (no longer needed)
- ✅ Announce launch! 🎉
- ✅ Share on social media, Product Hunt, Reddit, etc.

---

## Important Notes

### API Quotas
- **YouTube**: 10,000 units/day = ~66 songs
  - Consider requesting quota increase if needed
  - Form: [Google Cloud Quotas](https://console.cloud.google.com/iam-admin/quotas)

### Cost Considerations
- **YouTube API**: Free (with quota limits)
- **Spotify API**: Free (unlimited)
- **Hosting**: Render free tier or $7/month
- **Domain**: ~$10-15/year (optional)

### Backup Plan
If Google verification takes too long:
- Launch with Spotify → YouTube disabled temporarily
- Only enable YouTube → Spotify (no auth needed for reading public playlists)
- Add waitlist for full bidirectional conversion

---

## Quick Links

- [Google OAuth Verification](https://support.google.com/cloud/answer/9110914)
- [Spotify Extended Quota](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)
- [YouTube API Policies](https://developers.google.com/youtube/terms/developer-policies)
- [Render Deployment](https://render.com/docs)

---

## Need Help?

Check these resources:
- Google verification guide: https://support.google.com/cloud/answer/9110914
- Spotify quota guide: https://developer.spotify.com/documentation/web-api/concepts/quota-modes
- YouTube policies: https://developers.google.com/youtube/terms/developer-policies
