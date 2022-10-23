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

    # Set SERVICENAME to the name of the service
    !define SERVICENAME "OpenChaver"

    # Set the Output Directory
    SetOutPath $INSTDIR

    # Kill any processes that are running
    KillProcDLL::KillProc "openchaver.exe"

    # Run NSSM to stop the OpenChaver service if it already exists
    nsExec::ExecToLog '"$INSTDIR\nssm.exe" stop ${SERVICENAME}'

    # Wait for the process to die
    Sleep 1000

    # Copy all the contents of ./openchaver.dist to the install directory
    File /r "build\openchaver.dist\"
    File /r "bin\"

    # Run the OpenChaver Setup
    ExecWait '"$INSTDIR\openchaver.exe" setup'
    # Run twice to make sure the service is installed
    Sleep 500
    ExecWait '"$INSTDIR\openchaver.exe" setup'

# default section end
SectionEnd

