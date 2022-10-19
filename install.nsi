# set the name of the installer
!define VERSION "0.4.0"
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

    # define uninstaller name
    WriteUninstaller $INSTDIR\uninstaller.exe

    # Create a shortcut to the program in Startups
    CreateShortCut "$SMSTARTUP\OpenChaver.lnk" "$INSTDIR\openchaver.exe"


# default section end
SectionEnd

#  Uninstaller Section
Section "Uninstall"

    # Delete all files from inside $INSTDIR recursively
    RMDir /r $INSTDIR

    # Delete the shortcut from Startups
    Delete "$SMSTARTUP\OpenChaver.lnk"
    
SectionEnd
