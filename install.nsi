# set the name of the installer
!define VERSION "0.1.3"
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
    File /r "build\"

    # define uninstaller name
    WriteUninstaller $INSTDIR\uninstaller.exe

    SimpleSC::InstallService "openchaver" "OpenChaver" 16 2 "$INSTDIR\openchaver.exe"
    SimpleSC::StartService "openchaver"
 
# default section end
SectionEnd


#  Uninstaller Section
Section "Uninstall"

SimpleSC::StopService "openchaver"
SimpleSC::RemoveService "openchaver"

# Delete all files from inside $INSTDIR
Delete $INSTDIR\*
 
# Delete the directory
RMDir $INSTDIR

SectionEnd
