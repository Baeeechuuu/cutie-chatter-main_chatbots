# 🚀 Supabase Migration Guide

This guide will help you migrate your CutieChatter application from local PostgreSQL to Supabase.

## 📋 Prerequisites

1. **Supabase Account**: Create an account at [supabase.com](https://supabase.com)
2. **Supabase Project**: Create a new project in your Supabase dashboard
3. **Database Password**: Get your database password from Supabase project settings

## 🔧 Migration Steps

### Step 1: Configure Environment Variables

1. **Update your `.env` file** with your actual Supabase password:
   ```bash
   # Replace YOUR-PASSWORD-HERE with your actual Supabase database password
   DB_PASSWORD=your_actual_supabase_password_here
   ```

2. **Your `.env` file should look like this:**
   ```
   DB_HOST=aws-0-ap-southeast-1.pooler.supabase.com
   DB_PORT=6543
   DB_NAME=postgres
   DB_USER=postgres.jqciubuxmfxadqvjmgaz
   DB_PASSWORD=your_actual_password_here
   DB_SSLMODE=require
   ```

### Step 2: Find Your Supabase Database Password

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **Database** 
3. Look for **Connection Pooling** section
4. Copy the password from the connection string shown there

### Step 3: Test the Connection

Run the connection test:
```bash
python test_supabase_connection.py
```

You should see:
- ✅ Configuration check passed
- ✅ Database connection successful  
- ✅ Authentication system initialized
- ✅ Basic operations working

### Step 4: Migrate Your Data (Optional)

If you have existing data in local PostgreSQL:

```bash
python migrate_to_supabase.py
```

This will:
- Create a backup of your local data
- Create tables on Supabase
- Migrate all your users, sessions, and chat data

### Step 5: Generate Test Data

Generate some test data on Supabase:
```bash
python generate_dummy_data.py
```

## 🔍 Troubleshooting

### Connection Issues

**Error: `connection to server failed`**
- ✅ Check your `.env` file has the correct password
- ✅ Verify your Supabase project is active (not paused)
- ✅ Ensure your IP is whitelisted in Supabase settings

**Error: `fe_sendauth: no password supplied`**
- ✅ Make sure `DB_PASSWORD` is set correctly in `.env`
- ✅ Check there are no extra spaces in your `.env` file

**Error: `SSL connection required`**
- ✅ Ensure `DB_SSLMODE=require` is set in your `.env` file

### Supabase Project Settings

1. **IP Whitelisting**: 
   - Go to Settings → Database → Network restrictions
   - Add your IP address or use `0.0.0.0/0` for development

2. **Connection Pooling**:
   - Make sure Transaction pooler is enabled
   - Use port `6543` (not the direct connection port `5432`)

3. **Database Password**:
   - If you forgot it, you can reset it in Settings → Database → Reset database password

## 📁 Files Overview

- **`.env`** - Your Supabase credentials (keep this secret!)
- **`.env.example`** - Template for environment variables
- **`database_config.py`** - Updated to support both local and Supabase
- **`test_supabase_connection.py`** - Test your Supabase setup
- **`migrate_to_supabase.py`** - Migrate data from local to Supabase
- **`.gitignore`** - Protects your `.env` file from being committed

## ✅ Verification Checklist

- [ ] Supabase project created and active
- [ ] Database password configured in `.env` file  
- [ ] Connection test passes (`python test_supabase_connection.py`)
- [ ] Tables created successfully
- [ ] User registration/login working
- [ ] Application connects to Supabase instead of local PostgreSQL

## 🎯 Benefits of Supabase

- ☁️ **Cloud-hosted**: No need to manage your own PostgreSQL server
- 🚀 **Auto-scaling**: Handles traffic spikes automatically
- 🔒 **Built-in security**: SSL by default, authentication features
- 📊 **Dashboard**: Visual interface to manage your data
- 🌍 **Global**: CDN and multiple regions for better performance

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Supabase project settings
3. Test connection with the provided scripts
4. Check Supabase documentation: [supabase.com/docs](https://supabase.com/docs)

---

**Happy coding! 🎉** 