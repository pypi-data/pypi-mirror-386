import argparse
import logging
import sys
from .core import sign_apk, AndroSignError
from . import __version__


def main():
    print("""       :+@@*                                              *@@+:       
        -@@@@-                                          -@@@@-        
        ..#@@-                                          -@@#..        
         .#@@@*.      ....:+@@@@@@@@@@@@%-...          +@@@#.         
          .=@@*.     -@@@@@@@@@@@@@@@@@@@@@@@@#-.    ..*@@=.          
           .-%@%:+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=::%@#..           
            .#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#...          
           =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=.             
        ..#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%=:  ....        
       *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:   *@@@*       
    .-@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:.   -@@@@@@@-     
   .*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#-.      .-@@@@@@@@*    
  :@@@@@@@@@@+:..............................        ..*@@@@@@@@@@@:  
 +@@@@@@@@-.      .                               ..+@@@@@@@@@@@@@@@+.
@@@@@@@@#       .:=@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@=      =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@#..   .-%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@#.  .#@@-  .+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*:. -@@@@@@@@@@@@@
@@@@=.  .:#*     .=@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%: .    *@@@@@@@@@@@
@@@@=   -@@*      :%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:      .-@@@@@@@@@@
@@@@=   -@@*     .=@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%:      *@@@@@@@@@@@
@@@@=  :+@@@@- .:*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*:. -@@@@@@@@@@@@@
@@@@=  *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@=  *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@=  *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@=  *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@=  *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
""")

    parser = argparse.ArgumentParser(description="AndroSing - Fast APK signing (v1/v2).")
    parser.add_argument("apk", nargs="?", help="Path to APK file")
    parser.add_argument("--v1", action="store_true", help="Use v1 signature (JAR)")
    parser.add_argument("--v2", action="store_true", help="Use v2 signature (APK scheme v2)")
    parser.add_argument("--keystore", help="Path to keystore file")
    parser.add_argument("--key-alias", help="Alias in keystore")
    parser.add_argument("--ks-pass", help="Keystore password")
    parser.add_argument("--key-pass", help="Key password")
    parser.add_argument("--out", help="Output APK path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--version", "-v", action="store_true", help="Show version and exit")

    args = parser.parse_args()
    
    if args.version:
        print(f"version: {__version__}")
        sys.exit(0)

    if not args.apk:
        parser.print_help()
        sys.exit(1)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
    )

    try:
        sign_apk(
            apk=args.apk,
            v1=args.v1,
            v2=args.v2,
            keystore=args.keystore,
            key_alias=args.key_alias,
            ks_pass=args.ks_pass,
            key_pass=args.key_pass,
            out=args.out,
        )
    except AndroSignError as e:
        logging.error(e)
        sys.exit(1)