# Building Desktop Application with PyInstaller

This guide explains how to package the Content Understanding Agent as a standalone Windows desktop application.

## Prerequisites

- Conda environment with all dependencies installed
- PyInstaller: `pip install pyinstaller`
- All required files in the `content-understanding-agent` directory

## Build Steps

### 1. Install PyInstaller

```bash
conda activate content-understanding
pip install pyinstaller
```

### 2. Ensure .env File Exists

Make sure your `.env` file is configured with all necessary values:

```env
PROJECT_ENDPOINT=https://...
MODEL_DEPLOYMENT_NAME=gpt-4.1
FUNCTION_APP_URL=https://...
STORAGE_ACCOUNT_NAME=...
CLASSIFIER_ID=prebuilt-layout
```

### 3. Build the Application

```bash
# Navigate to the agent directory
cd "c:\Users\akunanbaeva\OneDrive - Microsoft\Content Understanding Agent\content-understanding-agent"

# Build using the spec file
pyinstaller content_understanding_agent.spec
```

This will create:
- `build/` - Temporary build files
- `dist/ContentUnderstandingAgent/` - **Your packaged application**

### 4. Test the Application

```bash
cd dist\ContentUnderstandingAgent
.\ContentUnderstandingAgent.exe
```

The app will:
1. Start on an available port (usually 8501)
2. Print the URL in the console
3. Open automatically in your default browser

## Distribution

To share the application:

1. **Compress the entire folder:**
   ```bash
   Compress-Archive -Path "dist\ContentUnderstandingAgent" -DestinationPath "ContentUnderstandingAgent.zip"
   ```

2. **Share the ZIP file** with users

3. **Users need to:**
   - Extract the ZIP file
   - Run `ContentUnderstandingAgent.exe`
   - Run `az login` (Azure CLI must be installed)
   - Configure their `.env` file if needed

## Important Notes

### Azure Authentication

Users **must have Azure CLI installed** and run `az login` before using the app:

```bash
az login
```

The app uses `DefaultAzureCredential` which relies on Azure CLI authentication.

### Configuration

The `.env` file is bundled with the executable. To reconfigure:

1. Navigate to `dist\ContentUnderstandingAgent\_internal\`
2. Edit the `.env` file
3. Restart the application

### File Size

The packaged application is approximately 500MB-800MB due to:
- Python runtime
- Streamlit and all dependencies
- Azure SDK libraries

### Limitations

- **Not truly standalone**: Requires Azure CLI for authentication
- **Internet required**: Calls Azure services
- **Windows only**: This build is for Windows; macOS/Linux need separate builds

## Alternative: Create Installer

For a more professional distribution, create an installer using Inno Setup:

1. Download [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Create an installer script that:
   - Installs the app to Program Files
   - Creates desktop shortcut
   - Optionally installs Azure CLI
   - Guides user through initial setup

## Troubleshooting

**App doesn't start:**
- Check console output for errors
- Ensure Azure CLI is installed
- Run from command line to see error messages

**ModuleNotFoundError:**
- Add missing modules to `hiddenimports` in `.spec` file
- Rebuild with `pyinstaller content_understanding_agent.spec --clean`

**Authentication fails:**
- User needs to run `az login` in a terminal
- Check that `.env` file has correct values
- Verify Storage Blob Data Contributor role is assigned

**Port already in use:**
- The app automatically finds a free port
- If issues persist, check for other Streamlit instances

## Advanced: Electron Wrapper (Alternative)

For a more native desktop experience with embedded browser:

1. Install Node.js and npm
2. Use `electron-packager` or `electron-builder`
3. Create an Electron app that launches Streamlit internally
4. Package as a native Windows application

This approach provides:
- Native window controls
- No browser required
- Better user experience
- Larger file size (~1GB)

Contact me if you'd like help setting up the Electron version.
