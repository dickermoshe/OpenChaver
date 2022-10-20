# set the name of the installer
!define VERSION "0.4.1"
Name "OpenChaver ${VERSION}"
Outfile "Installer.exe"
 
# Set the destination install
InstallDir "$PROGRAMFILES\OpenChaver"

# Default Section
Section "Installer"
 
    # call UserInfo plugin to get user info.  The plugin puts the result in the stack
    UserInfo::GetAccountType
   
    # pop the result from the stack into $0
    Pop $0
 
    # compare the result with the string "Admin" to see if the user is admin.
    # If match, jump 3 lines down.
    StrCmp $0 "Admin" +3
 
    # if there is not a match, print message and return
    MessageBox MB_OK "Please re-run the Installer as Administrator: $0"
    Return

    # Set the Output Directory
    SetOutPath $INSTDIR

    # Copy all the contents of ./openchaver.dist to the install directory
    File /r "build\openchaver.dist\"
    File /r "bin\"

    # Run NSSM to install the OpenChaver service
    ExecWait '"$INSTDIR\nssm.exe" install OpenChaver "$INSTDIR\openchaver.exe" "services"'

    # Run NSSM to start the OpenChaver service
    ExecWait '"$INSTDIR\nssm.exe" start OpenChaver'

    # Run NSSM to set the OpenChaver service to start on boot
    ExecWait '"$INSTDIR\nssm.exe" set OpenChaver Start SERVICE_AUTO_START'

    # Run NSSM to set the OpenChaver service to run as the Local System account
    ExecWait '"$INSTDIR\nssm.exe" set OpenChaver ObjectName LocalSystem'

    # Create a Registry Key to run the monitor on boot
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run"  "OpenChaver Monitor" "$INSTDIR\openchaver.exe monitor"

    # Run the OpenChaver Monitor
    Exec '"$INSTDIR\openchaver.exe" monitor'

# default section end
SectionEnd
