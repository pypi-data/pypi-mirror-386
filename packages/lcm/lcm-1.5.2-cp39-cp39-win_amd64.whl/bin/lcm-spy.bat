setlocal enableDelayedExpansion

:: Determine our canonical location
set mydir=%~dp0

:: Find dependency JARs
if exist %mydir%\lcm.jar (
    set jars=%mydir%\lcm.jar
    set jars=!jars!;%mydir%\jchart2d-code\jchart2d-3.2.2.jar
    set ext=%mydir%\jchart2d-code\ext
) else (
    if exist %mydir%\..\share\java\lcm.jar (
      set jars=%mydir%\..\share\java\lcm.jar
      set jars=!jars!;%mydir%\..\share\java\jchart2d-3.2.2.jar
      set ext=%mydir%\..\share\java
    ) else (
      echo "Unable to find 'lcm.jar'; please check your installation"
      exit 1
    )
)

set jars=%jars%:$ext/xmlgraphics-commons-1.3.1.jar
set jars=%jars%:$ext/jide-oss-2.9.7.jar

:: Add user's CLASSPATH, if set
IF NOT "%CLASSPATH%"=="" set jars=%jars%;%CLASSPATH%

:: Launch the applet
java -server -Djava.net.preferIPv4Stack=true -Xmx128m -Xms64m -ea -cp "%jars%" lcm.spy.Spy %*
