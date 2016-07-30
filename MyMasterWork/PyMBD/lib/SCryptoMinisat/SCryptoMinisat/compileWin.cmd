@ECHO OFF
SETLOCAL

SET _OUTPUT=SCryptoMinisat.exe
SET _SLVRSOLVER=..\cryptominisat-2.5.1\solver
SET _SLVRMTL=..\cryptominisat-2.5.1\mtl
SET _SLVRMTRAND=..\cryptominisat-2.5.1\MTRand

cl /favor:INTEL64 /O2 /Fe%_OUTPUT% /F2097152 /TP /EHsc -I%_SLVRSOLVER% -I%_SLVRMTL% -I%_SLVRMTRAND% Main.C %_SLVRSOLVER%\*.cpp

ENDLOCAL

del *.obj
