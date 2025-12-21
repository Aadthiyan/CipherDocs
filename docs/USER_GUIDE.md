# User Guide - CipherDocs

## Table of Contents

1. [Getting Started](#getting-started)
2. [Account Management](#account-management)
3. [Uploading Documents](#uploading-documents)
4. [Searching Documents](#searching-documents)
5. [Managing Documents](#managing-documents)
6. [Admin Features](#admin-features)
7. [Analytics & Reporting](#analytics--reporting)
8. [FAQ](#faq)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Sign Up

1. **Open CipherDocs**
   - Go to `https://cipherdocs.com`
   - Click **"Sign Up"** button

2. **Enter Information**
   - Email address (must be unique)
   - Full name
   - Password (minimum 12 characters, with uppercase, numbers, and special characters)

3. **Create Account**
   - Click **"Create Account"**
   - Check your email for verification link
   - Click verification link

4. **Start Using**
   - You're now signed in!
   - Proceed to upload your first document

### Log In

1. **Visit Login Page**
   - Go to `https://cipherdocs.com/login`

2. **Enter Credentials**
   - Email address
   - Password

3. **Access Account**
   - You'll be redirected to your dashboard
   - If you see "Invalid credentials", double-check your email and password

### Password Reset

1. **On Login Page**
   - Click **"Forgot Password?"**

2. **Enter Email**
   - Provide your registered email address
   - Click **"Send Reset Link"**

3. **Check Email**
   - Look for "Password Reset" email
   - Click the reset link (valid for 24 hours)

4. **Create New Password**
   - Enter new password (must meet requirements)
   - Click **"Reset Password"**

---

## Account Management

### Edit Profile

1. **Navigate to Profile**
   - Click your avatar (top right)
   - Select **"Profile Settings"**

2. **Update Information**
   - Full name
   - Email address
   - Profile picture (optional)
   - Bio/About (optional)

3. **Save Changes**
   - Click **"Save Profile"**
   - You'll see a success message

### Change Password

1. **Go to Profile Settings**
   - Click avatar → **"Profile Settings"**

2. **Click "Security"** tab

3. **Enter Passwords**
   - Current password (for verification)
   - New password (12+ chars, uppercase, numbers, special chars)
   - Confirm new password

4. **Save**
   - Click **"Change Password"**
   - You'll be logged out
   - Log in with new password

### Enable Two-Factor Authentication (2FA)

1. **In Security Settings**
   - Click **"Enable 2FA"**

2. **Choose Method**
   - Authenticator App (Google Authenticator, Microsoft Authenticator)
   - SMS (text message)

3. **Scan QR Code** (if using app)
   - Open authenticator app
   - Scan the QR code
   - Enter 6-digit code from app

4. **Verify**
   - Enter the 6-digit code
   - Click **"Verify"**

5. **Save Backup Codes**
   - ⚠️ **Important**: Download and safely store backup codes
   - Use these if you lose access to your authenticator

### Delete Account

⚠️ **Warning**: This action is **permanent** and cannot be undone.

1. **Navigate to Account Settings**
   - Click avatar → **"Settings"** → **"Account"**

2. **Scroll to Bottom**
   - Find **"Delete Account"** section

3. **Confirm Deletion**
   - Type your password
   - Check: **"I understand this is permanent"**
   - Click **"Delete My Account"**

4. **Final Confirmation**
   - You'll receive a confirmation email
   - Click the link to complete deletion
   - All data deleted within 24 hours

---

## Uploading Documents

### Upload a Document

1. **Click "Upload Document"**
   - Or drag and drop a file anywhere

2. **Select File**
   - Supported formats: PDF, DOC, DOCX, TXT, RTF
   - Maximum file size: 100 MB

3. **Add Details** (Optional)
   - Document title (auto-filled from filename)
   - Description
   - Tags (comma-separated)
   - Category (Finance, Legal, HR, Other)

4. **Upload**
   - Click **"Upload"**
   - Monitor progress bar
   - You can close the dialog; upload continues in background

### Processing Status

```
Upload           → Extracting Text
Extracting Text  → Generating Embeddings (AI)
Embeddings       → Encrypting Data
Encrypting       → Ready ✅
```

**Time to Ready**: 5-30 seconds (depending on file size)

### Bulk Upload

1. **Click "Bulk Upload"** button

2. **Select Multiple Files**
   - Choose up to 10 files at once
   - All formats and sizes shown

3. **Review**
   - Check file list
   - Click **"Upload All"**

4. **Monitor Progress**
   - See progress for each file
   - Close dialog to continue working

### Upload Settings

1. **Click Settings** (⚙️ icon)

2. **Configure**
   - Default category for uploads
   - Auto-tagging enabled/disabled
   - Encrypt documents (yes/no)
   - Notify when ready

3. **Save**
   - Click **"Save Settings"**

---

## Searching Documents

### Basic Search

1. **Click Search** (magnifying glass)

2. **Enter Query**
   - Use plain English
   - Examples:
     - "machine learning"
     - "quarterly financial report"
     - "contract terms"

3. **View Results**
   - Results shown with relevance score
   - Click any result to preview

### Advanced Search

1. **Click "Advanced Search"** link

2. **Use Filters**
   - **Date Range**: When uploaded
   - **Category**: Finance, Legal, HR, Other
   - **Document Type**: PDF, Word, Text
   - **Tags**: Select specific tags
   - **Creator**: Who uploaded it

3. **Combine Filters**
   - Stack multiple filters
   - Results narrow as you add filters

4. **Save Search**
   - Click **"Save Search"**
   - Give it a name
   - Access from **"Saved Searches"** later

### Search Tips

| Query | Result |
|-------|--------|
| `"exact phrase"` | Exact phrase matching |
| `AI -finance` | Documents with AI, excluding finance |
| `2024 OR 2025` | Documents from either year |
| `budget*` | Matches: budget, budgeting, budgets |
| `project AND "Q4"` | Both terms present |

### Search Results

Each result shows:
- **Title** (clickable to preview)
- **Excerpt** (relevant text snippet)
- **Score** (relevance 0-100)
- **Tags** (document labels)
- **Date** (uploaded when)
- **Size** (file size)

---

## Managing Documents

### View Document

1. **From Search Results**
   - Click document title

2. **Preview Opens**
   - Read extracted text
   - View metadata (size, type, uploaded)
   - See similar documents

3. **Actions Available**
   - Download original
   - Download as text
   - Share with team
   - Delete document
   - Add to collection

### Edit Document Metadata

1. **Open Document**

2. **Click "Edit Metadata"** (pencil icon)

3. **Update**
   - Title
   - Description
   - Tags
   - Category
   - Visibility (private/team/public)

4. **Save**
   - Click **"Save Changes"**

### Download Document

**Two Download Options**:

1. **Original File**
   - Downloads as uploaded
   - Format: PDF, Word, Text, etc.

2. **As Text**
   - Downloads extracted text
   - Useful for copying quotes

**How to Download**:
- Open document
- Click **"Download"** menu
- Choose format
- File saved to Downloads

### Share Document

#### Share with Team Member

1. **Click "Share"** button

2. **Enter Email Address**
   - Type team member's email
   - Their name appears if registered

3. **Set Permission**
   - **View**: Read-only
   - **Comment**: View + add notes
   - **Edit**: View + edit metadata

4. **Send**
   - Click **"Share"**
   - They'll receive notification

#### Share with Link

1. **Click "Share"** → **"Get Link"**

2. **Copy Link**
   - Click **"Copy to Clipboard"**
   - Share with anyone (via email, chat, etc.)

3. **Link Expiry**
   - Set expiration date (1 day - 90 days)
   - Or "Never" expires

4. **Revoke Access**
   - Click **"Revoke Link"**
   - No one can access anymore

### Delete Document

1. **Open Document**

2. **Click "Delete"** button

3. **Confirm**
   - You'll see warning: "This action cannot be undone"
   - Click **"Delete Permanently"**

4. **Deleted**
   - Document removed immediately
   - You can't recover it

---

## Collections

### Create Collection

1. **Click "Collections"** (sidebar)

2. **Click "New Collection"**

3. **Enter Details**
   - Name (e.g., "Q4 Reports")
   - Description (optional)
   - Color (for visual organization)

4. **Create**
   - Click **"Create"**

### Add Documents to Collection

1. **Open Document**

2. **Click "Add to Collection"**

3. **Select Collection**
   - Click checkbox next to collection
   - Or create new collection right here

4. **Save**
   - Document added immediately

### View Collection

1. **Click Collections** (sidebar)

2. **Click Collection Name**

3. **See All Documents**
   - In that collection
   - Can search within collection
   - Can sort by date, title, etc.

### Share Collection

1. **In Collection**

2. **Click "Share Collection"**

3. **Add Team Members**
   - Enter emails
   - Set permission (View/Edit/Admin)

4. **Save**
   - All documents in collection now shared

---

## Admin Features

### User Management (Admin Only)

1. **Click Settings** (⚙️) → **"Users"**

2. **View All Users**
   - Email
   - Full name
   - Role
   - Last active
   - Documents uploaded

3. **Manage Users**

**Change Role**:
- Click user row
- Select new role (User/Viewer/Admin)
- Click **"Save"**

**Disable User**:
- Click user row
- Click **"Disable Account"**
- User can't log in anymore

**Delete User**:
- Click user row
- Click **"Delete User"**
- Confirm deletion
- All their documents deleted

### Organization Settings (Admin Only)

1. **Click Settings** → **"Organization"**

2. **Configure**
   - Organization name
   - Logo (for reports/branding)
   - Email domain (for auto-invites)
   - Settings (encryption, retention, etc.)

3. **Save**
   - Click **"Save Settings"**

### Billing (Admin Only)

1. **Click Settings** → **"Billing"**

2. **View Plan**
   - Current subscription
   - Billing cycle
   - Next renewal date

3. **Manage Payment**
   - Update credit card
   - Download invoices
   - View usage

4. **Upgrade/Downgrade**
   - Click **"Change Plan"**
   - Select new plan
   - Confirm changes

---

## Analytics & Reporting

### View Dashboard

1. **Click "Analytics"** (sidebar)

2. **See Overview**
   - Total documents
   - Total searches
   - Most active users
   - Most accessed documents
   - Search trends

### Document Analytics

1. **Open Document**

2. **Click "Analytics"** tab

3. **See Metrics**
   - **Views**: How many times viewed
   - **Searches**: How many searches led to this
   - **Viewers**: Who viewed it
   - **Last viewed**: When last accessed
   - **Downloads**: How many downloads

### User Activity Report

1. **In Analytics**

2. **Click "User Activity"**

3. **See**
   - Each user's activities
   - Documents uploaded
   - Searches performed
   - Documents accessed
   - Time period (last 7, 30, 90 days)

4. **Export**
   - Click **"Download Report"**
   - Get CSV file

### Search Analytics

1. **In Analytics**

2. **Click "Search Trends"**

3. **Analyze**
   - Most common searches
   - Search success rate
   - Average result time
   - Popular topics

4. **Export**
   - Download as report
   - Use for insights

---

## FAQ

### Q: How long does it take to process a document?

**A**: Usually 5-30 seconds depending on:
- File size (larger = slower)
- File type (PDFs faster than scanned images)
- Server load (peak times = slightly slower)

### Q: Can I edit my documents?

**A**: You can edit the metadata (title, tags, description) but not the content itself. For updated content, re-upload the document.

### Q: How secure is my data?

**A**: Very secure! 
- All data encrypted with military-grade AES-256
- Only you (and people you share with) can access
- Regular security audits and updates

### Q: Can I delete my account?

**A**: Yes. Go to Settings → Account → "Delete Account". ⚠️ This is permanent.

### Q: What file formats are supported?

**A**: PDF, Word (DOCX), Text (TXT), and RTF. Maximum 100 MB per file.

### Q: Can I search across all my documents?

**A**: Yes! The main search bar searches all your documents and any shared with you.

### Q: How do I share documents securely?

**A**: Two ways:
1. **Team**: Share with specific users (most secure)
2. **Link**: Generate expiring link (convenient for one-time access)

### Q: Is there a mobile app?

**A**: Coming soon! For now, use the web version on mobile browsers.

### Q: What happens to my data if I delete my account?

**A**: All your documents deleted permanently within 24 hours. Shared documents (created by others) remain accessible to them.

---

## Troubleshooting

### Login Issues

**Problem**: "Invalid Email or Password"
- Solution:
  - Check email spelling
  - Verify CAPS LOCK is off
  - Use "Forgot Password" to reset
  - Check if you registered with different email

**Problem**: "Account Not Found"
- Solution:
  - Check email spelling
  - You may not be registered yet - click "Sign Up"
  - Try email used before if you have multiple

**Problem**: "Too Many Login Attempts"
- Solution:
  - Wait 15 minutes
  - Try "Forgot Password" instead
  - Check if account was hacked (change password)

### Upload Issues

**Problem**: "File Too Large"
- Solution:
  - Files must be under 100 MB
  - Compress file or split into smaller parts
  - Check file wasn't corrupted during download

**Problem**: "Unsupported File Format"
- Solution:
  - CipherDocs supports: PDF, DOCX, TXT, RTF
  - Convert your file to one of these formats
  - If PDF with images, text extraction may take longer

**Problem**: "Upload Stuck/Not Completing"
- Solution:
  - Check internet connection
  - Try smaller file first
  - Refresh page and retry
  - Clear browser cache (Settings → Privacy)

### Search Issues

**Problem**: "No Results Found"
- Solution:
  - Try simpler query
  - Check spelling
  - Try different keywords
  - Document may still be processing (wait few seconds)

**Problem**: "Slow Search Results"
- Solution:
  - If searching large corpus (100k+ documents), slower is normal
  - Try narrowing with filters (date, category, tags)
  - Complex queries take longer than simple ones

**Problem**: "Search Results Not Relevant"
- Solution:
  - The system uses AI; it finds conceptually similar documents
  - Try more specific terms
  - Use exact phrase search with quotes: "exact phrase"

### Download Issues

**Problem**: "Download Not Starting"
- Solution:
  - Check download folder permissions
  - Try different browser
  - Disable browser extensions (ad blockers can block downloads)
  - Check browser download settings

**Problem**: "Downloaded File Corrupted"
- Solution:
  - Try downloading again
  - Try different format (original vs text)
  - Contact support if persists

### Performance Issues

**Problem**: "Website Slow / Freezing"
- Solution:
  - Check internet connection (try speedtest.net)
  - Close other browser tabs
  - Clear cache: Settings → Privacy → Clear browsing data
  - Try different browser (Chrome, Firefox, Safari)
  - Restart browser

**Problem**: "Out of Storage"
- Solution:
  - Delete old unused documents
  - Archive documents to external storage
  - Upgrade plan for more storage
  - Contact support for bulk deletion

### Account Issues

**Problem**: "Can't Change Password"
- Solution:
  - Current password must be correct
  - New password must meet requirements (12 chars, uppercase, numbers, special)
  - Refresh page and try again

**Problem**: "Can't Access Shared Documents"
- Solution:
  - Make sure you're logged in
  - The person sharing may have revoked access
  - Ask them to reshare
  - Check your "Shared with Me" section

### Still Having Issues?

**Contact Support**:
- **Email**: support@cipherdocs.com
- **Chat**: Click help icon (?) in bottom right
- **Status**: Check status.cipherdocs.com

When contacting support, provide:
- What you were trying to do
- Error message (if any)
- Browser and OS used
- Screenshot of issue

---

## Tips & Best Practices

### Organization

- ✅ Use descriptive titles (not "Document1.pdf")
- ✅ Tag documents consistently
- ✅ Use collections to organize by project
- ✅ Keep descriptions brief

### Searching

- ✅ Use specific terms for better results
- ✅ Combine related terms
- ✅ Use filters to narrow results
- ✅ Save frequent searches

### Security

- ✅ Use strong unique passwords
- ✅ Enable 2FA for security
- ✅ Don't share access links unnecessarily
- ✅ Set expiration dates on shared links
- ❌ Don't share passwords with others
- ❌ Don't store passwords in plain text

### Sharing

- ✅ Share with specific users when possible (more secure)
- ✅ Use link sharing for one-time access
- ✅ Set expiration dates for links
- ✅ Revoke access when no longer needed

---

**Last Updated**: December 16, 2025  
**Version**: 1.0  
**Status**: ✅ Complete
