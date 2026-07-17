#### Hey Danny it's me

1. Install git if you don't already have it

2. If you don't already have Python, during the Python installation, select: Add Python to PATH

3. Make sure all are downloaded running this in PowerShell
```
git --version
python --version
pip --version
```

4. Run these seperately with the correct informationvto set up data to remember your information
```
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

5. Run the snippet below to create a SSH key and save it to the default location (should be here: C:\Users\YourUsername\.ssh\id_ed25519). This will let you upload local files on git to github once you connect them with the keys
```
ssh-keygen -t ed25519 -C "your-email@example.com"
```

6. Run both of these in Powershell
```
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
```

7. Replace user profile name with yours and run
```
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

8. Then run and copy everything it output
```
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

9. Open github repository and go to settings and add paste what you just copied as a key and save it (don't delete mine if you see it)

10. Run this and confirm connections is up
```
ssh -T git@github.com
```

11. In the same terminal or a new one, run this (it just changes the folder your telling the commands to run on)
```
cd $env:USERPROFILE\Documents
```

12. Run this to pull everything that's on github onto your laptop
```
git clone git@github.com:USERNAME/REPOSITORY-NAME.git
```

13. Run this to go into project repository (don't close this terminal)
```
cd REPOSITORY-NAME
```

14. Open VSCode and open the project folder you downloaded

15. Run the first line. If you're in powershell run the second line, or if you're on command prompt run the third (terminal directory should now begin with (.venv))
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.venv\Scripts\activate.bat
```

16. Then run this
```
python -m pip install --upgrade pip
```

17. Run this and wait for everything to download (imports nba_api and everything it needs to run)
```
pip install -r requirements.txt
```

18. You should see a bunch of packages if you run this
```
pip list
```